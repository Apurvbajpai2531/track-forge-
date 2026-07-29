from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import ChecklistItem, Issue, User
from app.schemas.schemas import ChecklistItemCreate, ChecklistItemOut

router = APIRouter(prefix="/api/issues/{issue_id}/checklist", tags=["checklist"])


@router.post("", response_model=ChecklistItemOut, status_code=201)
def add_item(issue_id: int, payload: ChecklistItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Issue).get(issue_id):
        raise HTTPException(404, "Issue not found")
    item = ChecklistItem(issue_id=issue_id, text=payload.text, position=payload.position)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=List[ChecklistItemOut])
def list_items(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ChecklistItem).filter_by(issue_id=issue_id).order_by(ChecklistItem.position, ChecklistItem.id).all()


@router.patch("/{item_id}/toggle", response_model=ChecklistItemOut)
def toggle_item(issue_id: int, item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(ChecklistItem).filter_by(id=item_id, issue_id=issue_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    item.is_done = not item.is_done
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(issue_id: int, item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(ChecklistItem).filter_by(id=item_id, issue_id=issue_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return None