from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import IssueTemplate, Project, User
from app.schemas.schemas import IssueTemplateCreate, IssueTemplateOut

router = APIRouter(prefix="/api/projects/{project_id}/templates", tags=["templates"])


@router.post("", response_model=IssueTemplateOut, status_code=201)
def create_template(project_id: int, payload: IssueTemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Project).get(project_id):
        raise HTTPException(404, "Project not found")
    tmpl = IssueTemplate(project_id=project_id, **payload.model_dump())
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.get("", response_model=List[IssueTemplateOut])
def list_templates(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(IssueTemplate).filter_by(project_id=project_id).all()


@router.delete("/{template_id}", status_code=204)
def delete_template(project_id: int, template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tmpl = db.query(IssueTemplate).filter_by(id=template_id, project_id=project_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    db.delete(tmpl)
    db.commit()
    return None
