import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Issue, Project, User, ActivityLog
from app.schemas.schemas import IssueCreate, IssueUpdate, IssueOut, PaginatedIssues, ActivityLogOut

router = APIRouter(prefix="/api/projects/{project_id}/issues", tags=["issues"])


@router.get("/export/csv")
def export_issues_csv(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issues = db.query(Issue).filter(Issue.project_id == project_id).order_by(Issue.id).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Key", "Title", "Status", "Priority", "Type", "Assignee ID", "Due Date", "Created At"])
    for issue in issues:
        writer.writerow([
            issue.key, issue.title, issue.status.value, issue.priority.value,
            issue.type.value, issue.assignee_id or "", issue.due_date or "", issue.created_at,
        ])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=issues_export_{project_id}.csv"},
    )


@router.post("", response_model=IssueOut, status_code=201)
def create_issue(
    project_id: int,
    payload: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    project.issue_seq += 1
    issue_key = f"{project.key}-{project.issue_seq}"

    issue = Issue(
        key=issue_key,
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        type=payload.type,
        reporter_id=current_user.id,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        story_points=payload.story_points,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.get("", response_model=PaginatedIssues)
def list_issues(
    project_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Issue).filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if priority:
        query = query.filter(Issue.priority == priority)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    if search:
        query = query.filter(Issue.title.ilike(f"%{search}%"))

    total = query.count()
    items = (
        query.order_by(Issue.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedIssues(total=total, page=page, page_size=page_size, items=items)


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = db.query(Issue).filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    project_id: int,
    issue_id: int,
    payload: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(Issue).filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        old_value = getattr(issue, field)
        if old_value != value:
            db.add(ActivityLog(
                issue_id=issue.id,
                user_id=current_user.id,
                action=f"changed {field} from '{old_value}' to '{value}'",
            ))
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_id}", status_code=204)
def delete_issue(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = db.query(Issue).filter_by(id=issue_id, project_id=project_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    db.delete(issue)
    db.commit()
    return None


@router.get("/{issue_id}/activity", response_model=List[ActivityLogOut])
def get_activity(project_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(ActivityLog)
        .filter_by(issue_id=issue_id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )

