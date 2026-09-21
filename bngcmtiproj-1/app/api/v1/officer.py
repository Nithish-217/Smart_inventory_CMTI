from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select, text
from app.api.deps import get_current_session, require_role
from app.db.session import get_db
from fastapi import Depends, HTTPException
from fastapi import APIRouter

router = APIRouter()

from app.models.issue import ToolIssue
from app.schemas.issue import ToolIssueOut
from datetime import datetime, timezone
from sqlalchemy import func
from app.models.user import User
from app.models.enums import UserRole, RequestStatus
from app.models.session import Session as SessionModel
from app.models.tool_requests import ToolAdditionRequest, ToolUsageRequest
from app.models.inventory import ToolInventory
from app.schemas.user import UserCreateIn, UserOut
from app.schemas.inventory import ToolAdditionOut, ApproveToolAdditionOut
from app.schemas.common import MessageOut
from app.schemas.tool_requests import ApproveToolUsageOut
from app.core.config import settings
from app.core.security import hash_password
from app.models.notification import Notification

# New endpoint: Get officer notifications
@router.get("/notifications")
def get_officer_notifications(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    officer_id = user.id
    
    # Get notifications for this officer
    notifications = db.execute(
        select(Notification)
        .where(Notification.user_id == officer_id)
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

# Officer: View all reported tool issues
@router.get("/tool-issues", response_model=list[ToolIssueOut])
def list_tool_issues(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    
    # Get all tool issues
    issues = db.execute(
        select(ToolIssue)
        .order_by(ToolIssue.created_at.desc())
    ).scalars().all()
    
    # Return all required fields for each issue
    result = [
        ToolIssueOut(
            id=issue.id,
            tool_id=issue.tool_id,
            operator_id=issue.operator_id,
            description=issue.description,
            status=issue.status,
            created_at=issue.created_at,
            resolved_at=issue.resolved_at
        ) for issue in issues
    ]
    
    return result

# New endpoint: Officer responds to tool issue
@router.post("/tool-issues/{issue_id}/respond")
def respond_to_tool_issue(
    issue_id: int, 
    response: str, 
    db: OrmSession = Depends(get_db), 
    session_data: tuple = Depends(get_current_session)
):
    sess, officer = session_data
    issue = db.execute(select(ToolIssue).where(ToolIssue.id == issue_id)).scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Update issue status and add officer response
    issue.status = "RESPONDED"
    issue.resolved_at = datetime.now(timezone.utc)
    
    # Notify the operator about the officer's response
    from app.services.notifications import notify_user
    notify_user(
        db,
        user_id=issue.operator_id,
        role="OPERATOR",
        title="Issue Response from Officer",
        description=f"Officer has responded to your tool issue: {response[:50]}...",
        target_url="/operator-dashboard",
    )
    
    db.commit()
    return {"message": "Response sent successfully"}

# New endpoint: Officer approves tool issue
@router.post("/tool-issues/{issue_id}/approve")
def approve_tool_issue(
    issue_id: int,
    data: dict,
    db: OrmSession = Depends(get_db),
    session_data: tuple = Depends(get_current_session)
):
    sess, officer = session_data
    issue = db.execute(select(ToolIssue).where(ToolIssue.id == issue_id)).scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if issue.status != "OPEN":
        raise HTTPException(status_code=400, detail="Issue already processed")
    
    # Update issue status
    issue.status = "APPROVED"
    issue.resolved_at = datetime.now(timezone.utc)
    
    # Notify the specific operator about approval
    from app.services.notifications import notify_user
    notify_user(
        db,
        user_id=issue.operator_id,
        role="OPERATOR",
        title="Tool Issue Approved",
        description=f"Your tool issue has been approved by an officer. Response: {data.get('response', 'Issue approved')}",
        target_url="/operator-dashboard",
    )
    
    db.commit()
    return {"message": "Issue approved successfully"}

# New endpoint: Officer rejects tool issue
@router.post("/tool-issues/{issue_id}/reject")
def reject_tool_issue(
    issue_id: int,
    data: dict,
    db: OrmSession = Depends(get_db),
    session_data: tuple = Depends(get_current_session)
):
    sess, officer = session_data
    issue = db.execute(select(ToolIssue).where(ToolIssue.id == issue_id)).scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    if issue.status != "OPEN":
        raise HTTPException(status_code=400, detail="Issue already processed")
    
    # Update issue status
    issue.status = "REJECTED"
    issue.resolved_at = datetime.now(timezone.utc)
    
    # Notify the specific operator about rejection
    from app.services.notifications import notify_user
    notify_user(
        db,
        user_id=issue.operator_id,
        role="OPERATOR",
        title="Tool Issue Rejected",
        description=f"Your tool issue has been rejected by an officer. Reason: {data.get('response', 'Issue rejected')}",
        target_url="/operator-dashboard",
    )
    
    db.commit()
    return {"message": "Issue rejected successfully"}

@router.get("/tool-requests", dependencies=[Depends(require_role(UserRole.OFFICER))])
def list_all_tool_requests_for_officer(db: OrmSession = Depends(get_db)):
    rows = db.execute(
        select(ToolUsageRequest, ToolInventory.tool_name.label('tool_name'))
        .join(ToolInventory, ToolUsageRequest.tool_id == ToolInventory.id)
        .order_by(ToolUsageRequest.requested_at.desc())  # Show newest first
    ).all()
    return [
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

@router.post("/tool-requests/{request_id}/approve", response_model=ApproveToolUsageOut, dependencies=[Depends(require_role(UserRole.OFFICER))])
def officer_approve_tool_request(request_id: str, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    _sess, officer = data
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    inv = db.get(ToolInventory, req.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")

    db.execute(text("LOCK TABLE tool_inventory IN ROW EXCLUSIVE MODE"))
    db.refresh(inv)
    if inv.quantity < req.requested_qty:
        raise HTTPException(status_code=400, detail="Insufficient stock at approval time")

    inv.quantity -= req.requested_qty
    req.status = RequestStatus.APPROVED
    from datetime import datetime, timezone
    req.reviewed_at = datetime.now(timezone.utc)
    req.reviewer_id = officer.id
    db.commit()
    
    # Notify all supervisors about the approval
    supervisors = db.execute(select(User.id).where(User.role == UserRole.SUPERVISOR)).scalars().all()
    for supervisor_id in supervisors:
        notify_user(
            db,
            user_id=supervisor_id,
            role="SUPERVISOR",
            title="Tool Request Approved by Officer",
            description=f"Officer {officer.full_name} approved tool request {request_id} for {req.requested_qty} of {inv.tool_name}",
            target_url="/supervisor/view-tool-requests",
        )
    
    return ApproveToolUsageOut(
        request_id=req.request_id,
        status=req.status.value,
        tool_id=inv.id,
        tool_name=inv.tool_name,
        requested_qty=req.requested_qty,
        remaining_qty=inv.quantity,
        approved_at=req.reviewed_at,
        approved_by={"id": officer.id, "name": officer.full_name},
    )

@router.post("/tool-requests/{request_id}/reject", dependencies=[Depends(require_role(UserRole.OFFICER))])
def officer_reject_tool_request(request_id: str, reason: str = "Not approved", db: OrmSession = Depends(get_db)):
    req = db.execute(select(ToolUsageRequest).where(ToolUsageRequest.request_id == request_id)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Get tool information for notification
    inv = db.get(ToolInventory, req.tool_id)
    tool_name = inv.tool_name if inv else f"Tool ID {req.tool_id}"
    
    from datetime import datetime, timezone
    req.status = RequestStatus.REJECTED
    req.reviewed_at = datetime.now(timezone.utc)
    req.reviewer_remarks = reason
    db.commit()
    
    # Notify all supervisors about the rejection
    supervisors = db.execute(select(User.id).where(User.role == UserRole.SUPERVISOR)).scalars().all()
    for supervisor_id in supervisors:
        notify_user(
            db,
            user_id=supervisor_id,
            role="SUPERVISOR",
            title="Tool Request Rejected by Officer",
            description=f"Officer rejected tool request {request_id} for {req.requested_qty} of {tool_name}. Reason: {reason}",
            target_url="/supervisor/view-tool-requests",
        )
    
    return {"message": "Rejected"}


@router.post("/users", response_model=UserOut, dependencies=[Depends(require_role(UserRole.OFFICER))])
def create_user(payload: UserCreateIn, db: OrmSession = Depends(get_db)):
    if db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
    full_name=payload.full_name,
    username=payload.username,
    email=payload.email,
    contact_number=payload.contact_number,
    role=payload.role,
    hashed_password=hash_password(settings.DEFAULT_PASSWORD),
    is_first_login=True,
    is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_role(UserRole.OFFICER))])
def list_users(db: OrmSession = Depends(get_db)):
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    return users

@router.delete("/users/{user_id}", response_model=MessageOut, dependencies=[Depends(require_role(UserRole.OFFICER))])
def delete_user(user_id: int, db: OrmSession = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return MessageOut(message="User deleted")

@router.get("/tool-additions", response_model=list[ToolAdditionOut], dependencies=[Depends(require_role(UserRole.OFFICER))])
def list_tool_additions(status_filter: RequestStatus | None = None, db: OrmSession = Depends(get_db)):
    stmt = select(ToolAdditionRequest)
    if status_filter:
        stmt = stmt.where(ToolAdditionRequest.status == status_filter)
    rows = db.execute(stmt.order_by(ToolAdditionRequest.created_at.desc())).scalars().all()
    return [
        ToolAdditionOut(
            id=r.id,
            tool_name=r.tool_name,
            status=r.status.value,
            requested_by=r.requested_by,
            created_at=r.created_at,
        )
        for r in rows
    ]

@router.post("/tool-additions/{id}/approve", response_model=ApproveToolAdditionOut, dependencies=[Depends(require_role(UserRole.OFFICER))])
def approve_tool_addition(id: int, data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    _, _officer = data
    req = db.get(ToolAdditionRequest, id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")

    # Persist decision in DB
    req.status = RequestStatus.APPROVED
    db.commit()

    return ApproveToolAdditionOut(
        id=req.id,
        tool_name=req.tool_name,
        status=req.status.value,
    )

@router.post("/tool-additions/{id}/reject", response_model=MessageOut, dependencies=[Depends(require_role(UserRole.OFFICER))])
def reject_tool_addition(id: int, reason: str = "Not approved", data=Depends(get_current_session), db: OrmSession = Depends(get_db)):
    _sess, _officer = data
    req = db.get(ToolAdditionRequest, id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request already processed")

    # Persist decision in DB
    req.status = RequestStatus.REJECTED
    db.commit()
    return MessageOut(message="Rejected")

@router.get("/session-logs", dependencies=[Depends(require_role(UserRole.OFFICER))])
def session_logs(role: UserRole | None = None, username: str | None = None, status_filter: str | None = None, db: OrmSession = Depends(get_db)):
    stmt = select(SessionModel).join(User, User.id == SessionModel.user_id)
    if role:
        stmt = stmt.where(SessionModel.role == role)
    if username:
        stmt = stmt.where(User.username == username)
        rows = db.execute(stmt.order_by(SessionModel.login_at.desc())).scalars().all()
        result = []
        now = datetime.now(timezone.utc)
        for s in rows:
            u = db.get(User, s.user_id)
            active = s.logout_at is None and s.expires_at > now
            if status_filter == "ACTIVE" and not active:
                continue
            if status_filter == "ENDED" and active:
                continue
            result.append({
            "session_id": s.session_id,
            "username": u.username if u else None,
            "full_name": u.full_name if u else None,
            "role": s.role.value,
            "login_at": s.login_at,
            "expires_at": s.expires_at,
            "logout_at": s.logout_at,
            "ended_reason": s.ended_reason.value if s.ended_reason else None,
            "ip_address": s.ip_address,
            })
    return result

@router.get("/active-sessions", dependencies=[Depends(require_role(UserRole.OFFICER))])
def active_sessions(db: OrmSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    rows = db.execute(select(SessionModel).where(SessionModel.logout_at.is_(None))).scalars().all()
    active = []
    for s in rows:
        if s.expires_at > now:
            active.append({
            "session_id": s.session_id,
            "user_id": s.user_id,
            "role": s.role.value,
            "login_at": s.login_at,
            "expires_at": s.expires_at,
            })
    return active