from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import TimeLog, Issue, User
from app.schemas.schemas import TimeLogCreate, TimeLogOut

router = APIRouter(prefix="/api/issues/{issue_id}/timelogs", tags=["timelogs"])


@router.post("", response_model=TimeLogOut, status_code=201)
def log_time(issue_id: int, payload: TimeLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Issue).get(issue_id):
        raise HTTPException(404, "Issue not found")
    log = TimeLog(issue_id=issue_id, user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=List[TimeLogOut])
def list_timelogs(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(TimeLog).filter_by(issue_id=issue_id).order_by(TimeLog.logged_at.desc()).all()


@router.get("/total")
def total_time(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(TimeLog).filter_by(issue_id=issue_id).all()
    total_min = sum(l.minutes for l in logs)
    return {"issue_id": issue_id, "total_minutes": total_min, "total_hours": round(total_min / 60, 1)}