from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select, func
from app.api.deps import require_role, get_current_session
from app.db.session import get_db
from app.models.enums import UserRole, RequestStatus
from app.models.inventory import ToolInventory
from app.models.tool_requests import ToolUsageRequest
from app.models.user import User
from app.models.issue import ToolIssue
from app.schemas.issue import ToolIssueCreateIn
from app.schemas.inventory import ToolListItem
from app.schemas.tool_requests import ToolUsageCreateIn, ToolUsageShortOut
from app.services.notifications import notify_user
from app.models.notification import Notification

# Single router for all operator endpoints
router = APIRouter()


# Test endpoint to create a sample tool issue
@router.post("/test-issue")
def create_test_issue(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    
    # Create a test tool issue
    from app.models.issue import ToolIssue
    test_issue = ToolIssue(
        tool_id=1,  # Assuming tool ID 1 exists
        operator_id=user.id,
        description="Test issue for debugging purposes",
        status="OPEN",
    )
    db.add(test_issue)
    db.commit()
    db.refresh(test_issue)
    
    # Notify officers
    officers = db.execute(select(User.id).where(User.role == UserRole.OFFICER)).scalars().all()
    for officer_id in officers:
        notify_user(
            db,
            user_id=officer_id,
            role="OFFICER",
            title="Test Tool Issue",
            description=f"Test issue created by {user.full_name}",
            target_url="/officer/issue-reports",
        )
    
    return {"message": "Test issue created", "issue_id": test_issue.id}

# Report a tool issue (operator -> officer)
@router.post("/tool-issues")
def report_tool_issue(
    payload: ToolIssueCreateIn,
    db: OrmSession = Depends(get_db),
    session_data: tuple = Depends(get_current_session)
):
    sess, user = session_data
    
    # Get tool information for better notification
    tool = db.get(ToolInventory, payload.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    issue = ToolIssue(
        tool_id=payload.tool_id,
        operator_id=user.id,
        description=payload.description,
        status="OPEN",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    # Notify all officers with specific tool information
    officers = db.execute(select(User.id).where(User.role == UserRole.OFFICER)).scalars().all()
    for officer_id in officers:
        notify_user(
            db,
            user_id=officer_id,
            role="OFFICER",
            title="New Tool Issue Reported",
            description=f"Operator {user.full_name} reported an issue for tool: {tool.tool_name} (ID: {tool.id})",
            target_url="/officer/issue-reports",
        )
    
    return {"message": "Issue reported and officers notified.", "issue_id": issue.id}

# Endpoint to display all tool requests made by the operator
@router.get("/tool-requests/all")
def list_operator_tool_requests(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    rows = db.execute(
        select(ToolUsageRequest)
        .where(ToolUsageRequest.operator_id == user.id)
        .order_by(ToolUsageRequest.requested_at.desc())
    ).scalars().all()
    return [
        {
            "request_id": r.request_id,
            "tool_id": r.tool_id,
            "requested_qty": r.requested_qty,
            "status": r.status.value,
            "requested_at": str(r.requested_at),
            "reviewed_at": str(r.reviewed_at) if r.reviewed_at else None,
            "reviewer_id": r.reviewer_id,
            "reviewer_remarks": r.reviewer_remarks
        } for r in rows
    ]

# New endpoint: Get operator tool requests (for the new page)
@router.get("/tool-requests")
def get_operator_tool_requests(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    operator_id = user.id
    
    # Get tool requests with tool information
    requests = db.execute(
        select(ToolUsageRequest, ToolInventory.tool_name)
        .join(ToolInventory, ToolUsageRequest.tool_id == ToolInventory.id)
        .where(ToolUsageRequest.operator_id == operator_id)
        .order_by(ToolUsageRequest.requested_at.desc())
    ).all()
    
    return [
        {
            "request_id": req.request_id,
            "tool_id": req.tool_id,
            "tool_name": tool_name,
            "requested_qty": req.requested_qty,
            "status": req.status.value,
            "requested_at": str(req.requested_at),
            "processed_at": str(req.reviewed_at) if req.reviewed_at else None,
            "remarks": req.reviewer_remarks
        } for req, tool_name in requests
    ]

# New endpoint: Get operator tool issues (for the new page)
@router.get("/tool-issues")
def get_operator_tool_issues(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    operator_id = user.id
    
    # Get tool issues with tool information
    issues = db.execute(
        select(ToolIssue, ToolInventory.tool_name)
        .join(ToolInventory, ToolIssue.tool_id == ToolInventory.id)
        .where(ToolIssue.operator_id == operator_id)
        .order_by(ToolIssue.created_at.desc())
    ).all()
    
    return [
        {
            "issue_id": issue.id,
            "tool_id": issue.tool_id,
            "tool_name": tool_name,
            "description": issue.description,
            "status": issue.status,
            "reported_at": str(issue.created_at),
            "resolved_at": str(issue.resolved_at) if issue.resolved_at else None
        } for issue, tool_name in issues
    ]

# New endpoint: Get operator used tools (approved requests)
@router.get("/used-tools")
def get_operator_used_tools(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    operator_id = user.id
    
    # Get approved tool requests with tool information
    used_tools = db.execute(
        select(ToolUsageRequest, ToolInventory)
        .join(ToolInventory, ToolUsageRequest.tool_id == ToolInventory.id)
        .where(
            ToolUsageRequest.operator_id == operator_id,
            ToolUsageRequest.status == RequestStatus.APPROVED
        )
        .order_by(ToolUsageRequest.reviewed_at.desc())
    ).all()
    
    return [
        {
            "tool_id": req.tool_id,
            "tool_name": tool.tool_name,
            "range_mm": tool.range_mm,
            "identification_code": tool.identification_code,
            "make": tool.make,
            "location": None,  # Not available in current model
            "gauge": None,     # Not available in current model
            "quantity_used": req.requested_qty,
            "used_at": str(req.reviewed_at),
            "remarks": None    # Not available in current model
        } for req, tool in used_tools
    ]

# New endpoint: Get operator statistics
@router.get("/statistics")
def get_operator_statistics(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    operator_id = user.id
    
    # Count total tools used (approved requests)
    total_tools_used = db.execute(
        select(func.sum(ToolUsageRequest.requested_qty))
        .where(
            ToolUsageRequest.operator_id == operator_id,
            ToolUsageRequest.status == RequestStatus.APPROVED
        )
    ).scalar() or 0
    
    # Count total tool requests made
    total_requests = db.execute(
        select(func.count(ToolUsageRequest.id))
        .where(ToolUsageRequest.operator_id == operator_id)
    ).scalar() or 0
    
    # Count total issues reported
    total_issues = db.execute(
        select(func.count(ToolIssue.id))
        .where(ToolIssue.operator_id == operator_id)
    ).scalar() or 0
    
    return {
        "total_tools_used": total_tools_used,
        "total_requests": total_requests,
        "total_issues": total_issues,
        "full_name": user.full_name
    }

# New endpoint: Get operator notifications
@router.get("/notifications")
def get_operator_notifications(db: OrmSession = Depends(get_db), session_data: tuple = Depends(get_current_session)):
    sess, user = session_data
    operator_id = user.id
    
    # Get notifications for this operator
    notifications = db.execute(
        select(Notification)
        .where(Notification.user_id == operator_id)
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


# Rewritten endpoint: POST /tool-requests
@router.post("/tool-requests")
def create_tool_request(
    payload: ToolUsageCreateIn,
    db: OrmSession = Depends(get_db),
    session_data: tuple = Depends(get_current_session)
):
    sess, user = session_data
    operator_id = user.id
    inv = db.get(ToolInventory, payload.tool_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Tool not found")
    if payload.requested_qty <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")
    if payload.requested_qty > inv.quantity:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds available")
    next_id = (db.execute(select(func.max(ToolUsageRequest.id))).scalar() or 0) + 1
    rid = f"TR{next_id:05d}"
    row = ToolUsageRequest(
        request_id=rid,
        operator_id=operator_id,
        user_id=user.id,
        tool_id=inv.id,
        requested_qty=payload.requested_qty,
        status=RequestStatus.PENDING,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    # Notify all supervisors with target_url for dashboard
    supervisors = db.execute(
        select(User.id).where(User.role == UserRole.SUPERVISOR)
    ).scalars().all()
    for supervisor_id in supervisors:
        notify_user(
            db,
            user_id=supervisor_id,
            role="SUPERVISOR",
            title="Tool Request",
            description=f"Operator requested {payload.requested_qty} of {inv.tool_name}",
            target_url="/supervisor/tool-requests"
        )
    return JSONResponse(content={
        "message": "Request was successful and supervisors have been notified.",
        "request_id": row.request_id,
        "tool_id": row.tool_id,
        "operator_id": row.operator_id,
        "requested_qty": row.requested_qty,
        "status": row.status.value,
        "requested_at": str(row.requested_at)
    })

@router.get("/test")
def test():
    return {"status": "operator router loaded"}

# Test endpoint for collect functionality
@router.get("/test-collect")
def test_collect():
    return {"status": "collect endpoint accessible", "available_statuses": [status.value for status in RequestStatus]}


# New /tools endpoint: returns only fields present in ToolInventory
@router.get("/tools", response_model=list[ToolListItem])
def list_available_tools(db: OrmSession = Depends(get_db)):
    tools = db.execute(
        select(ToolInventory)
        .order_by(ToolInventory.tool_name.asc())
    ).scalars().all()
    result = [
        ToolListItem(
            id=t.id,
            tool_name=t.tool_name,
            range_mm=t.range_mm,
            identification_code=t.identification_code,
            make=t.make,
            quantity=t.quantity,
            location=None,  # Not available in current model
            gauge=None,     # Not available in current model
            remarks=None,   # Not available in current model
            added_at=t.added_at
        ) for t in tools
    ]
    return result

# New endpoint: Collect approved tool
@router.post("/collect-tool/{request_id}")
def collect_tool(
    request_id: str,
    db: OrmSession = Depends(get_db),
    session_data: tuple = Depends(get_current_session)
):
    try:
        sess, user = session_data
        operator_id = user.id
        
        # Find the tool request
        request = db.execute(
            select(ToolUsageRequest)
            .where(
                ToolUsageRequest.request_id == request_id,
                ToolUsageRequest.operator_id == operator_id
            )
        ).scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Tool request not found")
        
        if request.status != RequestStatus.APPROVED:
            raise HTTPException(status_code=400, detail=f"Tool request status is {request.status}, not approved")
        
        # Get tool information for response
        tool = db.get(ToolInventory, request.tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Update status to RECEIVED (collected)
        request.status = RequestStatus.RECEIVED
        db.commit()
        
        return {
            "message": f"Tool {tool.tool_name} (ID: {tool.id}) collected successfully!",
            "tool_name": tool.tool_name,
            "tool_id": tool.id,
            "request_id": request_id,
            "status": "COLLECTED"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")