from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select, func, text
from app.api.deps import require_role, get_current_session
from app.db.session import get_db
from app.models.enums import UserRole, RequestStatus
from app.models.tool_requests import ToolUsageRequest, ToolAdditionRequest
from app.models.inventory import ToolInventory
from app.models.notification import Notification
from app.schemas.tool_requests import ApproveToolUsageOut
from app.schemas.inventory import ToolAdditionCreateIn, ToolAdditionOut
from app.services.id_generator import make_request_id

router = APIRouter()

# New endpoint: Get supervisor notifications
@router.get("/notifications")
def get_supervisor_notifications(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    supervisor_id = user.id
    
    # Get notifications for this supervisor
    notifications = db.execute(
        select(Notification)
        .where(Notification.user_id == supervisor_id)
        .order_by(Notification.created_at.desc())
    ).scalars().all()
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "message": n.message,
            "target_url": n.target_url,
            "created_at": str(n.created_at),
            "is_read": getattr(n, 'is_read', False)
        } for n in notifications
    ]

@router.get("/tool-requests", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def list_all_tool_requests(db: OrmSession = Depends(get_db)):
    try:
        # Join with inventory to get tool names - show ALL requests, not just pending
        rows = db.execute(
            select(ToolUsageRequest, ToolInventory.tool_name.label('tool_name'))
            .join(ToolInventory, ToolUsageRequest.tool_id == ToolInventory.id)
            .order_by(ToolUsageRequest.requested_at.desc())  # Show newest first
        ).all()
        
        result = [
            {
                "request_id": r.ToolUsageRequest.request_id,
                "operator_id": r.ToolUsageRequest.operator_id,
                "tool_id": r.ToolUsageRequest.tool_id,
                "tool_name": r.tool_name,
                "requested_qty": r.ToolUsageRequest.requested_qty,
                "requested_at": r.ToolUsageRequest.requested_at,
                "status": r.ToolUsageRequest.status.value,  # Include status
                "reviewed_at": r.ToolUsageRequest.reviewed_at,  # Include review time
                "reviewer_remarks": r.ToolUsageRequest.reviewer_remarks,  # Include remarks
            } for r in rows
        ]
        
        return result
        
    except Exception as e:
        print(f"ERROR in supervisor tool-requests: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/tool-requests/{request_id}/approve", response_model=ApproveToolUsageOut, dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def approve_tool_request(request_id: str, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    sess, user = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    if req.reviewer_id is not None:
        raise HTTPException(status_code=403, detail="Already processed by another supervisor")
    inv = db.get(ToolInventory, req.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Lock table row to avoid race (Postgres)
    db.execute(text("LOCK TABLE tool_inventory IN ROW EXCLUSIVE MODE"))
    db.refresh(inv)

    if inv.quantity < req.requested_qty:
        raise HTTPException(status_code=400, detail="Insufficient stock at approval time")

    inv.quantity -= req.requested_qty
    req.status = RequestStatus.APPROVED
    from datetime import datetime, timezone
    req.reviewed_at = datetime.now(timezone.utc)
    req.reviewer_id = user.id

    db.commit()

    # Notify the operator about approval
    from app.services.notifications import notify_user
    notify_user(
        db,
        user_id=req.operator_id,
        role="OPERATOR",
        title="Tool Request Approved",
        description=f"Your request for {inv.tool_name} has been approved by supervisor",
        target_url="/operator-dashboard",
    )

    return ApproveToolUsageOut(
        request_id=req.request_id,
        status=req.status.value,
        tool_id=inv.id,
        tool_name=inv.tool_name,
        requested_qty=req.requested_qty,
        remaining_qty=inv.quantity,
        approved_at=req.reviewed_at,
        approved_by={"id": user.id, "name": user.full_name},
    )

@router.post("/tool-requests/{request_id}/reject", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def reject_tool_request(request_id: str, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    sess, user = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    if req.reviewer_id is not None:
        raise HTTPException(status_code=403, detail="Already processed by another supervisor")
    
    inv = db.get(ToolInventory, req.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")

    req.status = RequestStatus.REJECTED
    from datetime import datetime, timezone
    req.reviewed_at = datetime.now(timezone.utc)
    req.reviewer_id = user.id

    db.commit()

    # Notify the operator about rejection
    from app.services.notifications import notify_user
    notify_user(
        db,
        user_id=req.operator_id,
        role="OPERATOR",
        title="Tool Request Rejected",
        description=f"Your request for {inv.tool_name} has been rejected by supervisor",
        target_url="/operator-dashboard",
    )

    return {"message": "Request rejected successfully"}

@router.post("/tool-additions", response_model=ToolAdditionOut, dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def create_tool_addition(payload: ToolAdditionCreateIn, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    # Persist a minimal tool addition request matching current DB model
    sess, supervisor = data
    row = ToolAdditionRequest(
        tool_name=payload.tool_name,
        requested_by=supervisor.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ToolAdditionOut(
        id=row.id,
        tool_name=row.tool_name,
        status=row.status.value,
        requested_by=row.requested_by,
        created_at=row.created_at,
    )

@router.get("/tool-addition-requests", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def get_tool_addition_requests(status: str = None, db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    supervisor_id = user.id
    
    try:
        # Base query for supervisor's tool addition requests
        query = select(ToolAdditionRequest).where(ToolAdditionRequest.requested_by == supervisor_id)
        
        # Apply status filter if provided
        if status:
            status_enum = RequestStatus(status.upper())
            query = query.where(ToolAdditionRequest.status == status_enum)
        
        # Execute query
        requests = db.execute(query.order_by(ToolAdditionRequest.created_at.desc())).scalars().all()
        
        result = [
            {
                "id": req.id,
                "tool_name": req.tool_name,
                "status": req.status.value,
                "requested_by": req.requested_by,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "reviewed_at": req.reviewed_at.isoformat() if req.reviewed_at else None,
                "reviewer_id": req.reviewer_id,
                "reviewer_remarks": req.reviewer_remarks
            } for req in requests
        ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/logs/approved-usage", dependencies=[Depends(require_role(UserRole.SUPERVISOR))])
def approved_usage_logs(db: OrmSession = Depends(get_db)):
    rows = db.execute(
    select(ToolUsageRequest)
    .where(ToolUsageRequest.status == RequestStatus.APPROVED)
    .order_by(ToolUsageRequest.reviewed_at.desc())
    ).scalars().all()
    return [
    {
    "request_id": r.request_id,
    "tool": r.tool.name if r.tool else None,
    "quantity": r.requested_qty,
    "operator_id": r.operator_id,
    "operator_username": r.operator.username if r.operator else None,
    "supervisor_id": r.approved_by,
    "supervisor_name": r.approver.full_name if r.approver else None,
    "requested_at": r.requested_at,
    "approved_at": r.reviewed_at,
    } for r in rows
    ]
