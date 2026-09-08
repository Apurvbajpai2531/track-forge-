from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Label, Project, User
from app.schemas.schemas import LabelCreate, LabelOut

router = APIRouter(prefix="/api/projects/{project_id}/labels", tags=["labels"])


@router.post("", response_model=LabelOut, status_code=201)
def create_label(project_id: int, payload: LabelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Project).get(project_id):
        raise HTTPException(404, "Project not found")
    label = Label(project_id=project_id, name=payload.name, color=payload.color)
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


@router.get("", response_model=List[LabelOut])
def list_labels(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Label).filter_by(project_id=project_id).all()


@router.delete("/{label_id}", status_code=204)
def delete_label(project_id: int, label_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    label = db.query(Label).filter_by(id=label_id, project_id=project_id).first()
    if not label:
        raise HTTPException(404, "Label not found")
    db.delete(label)
    db.commit()
    return None
