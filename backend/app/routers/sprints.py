from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Sprint, SprintIssue, Issue, Project, User
from app.schemas.schemas import SprintCreate, SprintOut, SprintIssueAdd, IssueOut

router = APIRouter(prefix="/api/projects/{project_id}/sprints", tags=["sprints"])


@router.post("", response_model=SprintOut, status_code=201)
def create_sprint(project_id: int, payload: SprintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Project).get(project_id):
        raise HTTPException(404, "Project not found")
    sprint = Sprint(project_id=project_id, **payload.model_dump())
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("", response_model=List[SprintOut])
def list_sprints(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Sprint).filter_by(project_id=project_id).order_by(Sprint.id.desc()).all()


@router.get("/{sprint_id}", response_model=SprintOut)
def get_sprint(project_id: int, sprint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sprint = db.query(Sprint).filter_by(id=sprint_id, project_id=project_id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    return sprint


@router.patch("/{sprint_id}/status")
def update_sprint_status(project_id: int, sprint_id: int, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sprint = db.query(Sprint).filter_by(id=sprint_id, project_id=project_id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    if status not in ("planning", "active", "completed"):
        raise HTTPException(400, "Invalid status")
    sprint.status = status
    db.commit()
    return {"detail": "Updated"}


@router.post("/{sprint_id}/issues", status_code=201)
def add_issue_to_sprint(project_id: int, sprint_id: int, payload: SprintIssueAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sprint = db.query(Sprint).filter_by(id=sprint_id, project_id=project_id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    if db.query(SprintIssue).filter_by(sprint_id=sprint_id, issue_id=payload.issue_id).first():
        raise HTTPException(400, "Issue already in sprint")
    db.add(SprintIssue(sprint_id=sprint_id, issue_id=payload.issue_id))
    db.commit()
    return {"detail": "Added"}


@router.get("/{sprint_id}/issues", response_model=List[IssueOut])
def list_sprint_issues(project_id: int, sprint_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = db.query(SprintIssue).filter_by(sprint_id=sprint_id).all()
    return [e.issue for e in entries]


@router.delete("/{sprint_id}/issues/{issue_id}", status_code=204)
def remove_from_sprint(project_id: int, sprint_id: int, issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(SprintIssue).filter_by(sprint_id=sprint_id, issue_id=issue_id).first()
    if not entry:
        raise HTTPException(404, "Not found")
    db.delete(entry)
    db.commit()
    return None