from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Issue, User
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/api/projects/{project_id}/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def dashboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issues = db.query(Issue).filter(Issue.project_id == project_id).all()

    by_status, by_priority, overdue = {}, {}, 0
    now = datetime.utcnow()
    for issue in issues:
        by_status[issue.status.value] = by_status.get(issue.status.value, 0) + 1
        by_priority[issue.priority.value] = by_priority.get(issue.priority.value, 0) + 1
        if issue.due_date and issue.due_date < now and issue.status.value != "done":
            overdue += 1

    return DashboardStats(
        total_issues=len(issues), by_status=by_status, by_priority=by_priority, overdue=overdue
    )