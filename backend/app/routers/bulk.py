from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Issue, User
from app.schemas.schemas import BulkAction

router = APIRouter(prefix="/api/projects/{project_id}/bulk", tags=["bulk"])


@router.post("")
def bulk_action(project_id: int, payload: BulkAction, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issues = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.id.in_(payload.issue_ids)
    ).all()

    if not issues:
        raise HTTPException(404, "No matching issues found")

    if payload.action == "set_status":
        valid = ("todo", "in_progress", "in_review", "done")
        if payload.value not in valid:
            raise HTTPException(400, f"Invalid status. Must be one of {valid}")
        for issue in issues:
            issue.status = payload.value

    elif payload.action == "set_priority":
        valid = ("low", "medium", "high", "critical")
        if payload.value not in valid:
            raise HTTPException(400, f"Invalid priority. Must be one of {valid}")
        for issue in issues:
            issue.priority = payload.value

    elif payload.action == "delete":
        for issue in issues:
            db.delete(issue)

    else:
        raise HTTPException(400, "Unknown action. Use set_status, set_priority, or delete")

    db.commit()
    return {"detail": f"Action '{payload.action}' applied to {len(issues)} issues"}