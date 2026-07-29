from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Comment, Issue, User
from app.schemas.schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/api/issues/{issue_id}/comments", tags=["comments"])


@router.post("", response_model=CommentOut, status_code=201)
def add_comment(
    issue_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = db.query(Issue).get(issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found")

    comment = Comment(issue_id=issue_id, author_id=current_user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("", response_model=List[CommentOut])
def list_comments(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Comment).filter_by(issue_id=issue_id).order_by(Comment.created_at.asc()).all()
