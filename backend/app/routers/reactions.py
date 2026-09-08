from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.models import User


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", "emoji"),)

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emoji = Column(String(10), nullable=False)


router = APIRouter(prefix="/api/comments/{comment_id}/reactions", tags=["reactions"])

ALLOWED = {"👍", "❤️", "😂", "🎉", "🔥", "👀", "😢", "🚀"}


@router.post("/{emoji}")
def toggle_reaction(
        comment_id: int,
        emoji: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    if emoji not in ALLOWED:
        from fastapi import HTTPException
        raise HTTPException(400, "Emoji not allowed")
    existing = db.query(CommentReaction).filter_by(comment_id=comment_id, user_id=current_user.id, emoji=emoji).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "removed"}
    db.add(CommentReaction(comment_id=comment_id, user_id=current_user.id, emoji=emoji))
    db.commit()
    return {"action": "added"}


@router.get("")
def list_reactions(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(CommentReaction).filter_by(comment_id=comment_id).all()
    counts = {}
    for r in rows:
        counts[r.emoji] = counts.get(r.emoji, 0) + 1
    return counts
