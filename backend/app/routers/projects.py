from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Project, ProjectMember, User
from app.schemas.schemas import ProjectCreate, ProjectOut, ProjectMemberAdd, UserOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Project).filter(Project.key == payload.key.upper()).first():
        raise HTTPException(400, "Project key already exists")

    project = Project(key=payload.key.upper(), name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)

    # creator becomes admin member
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="admin"))
    db.commit()
    return project


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Project).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/{project_id}/members", status_code=201)
def add_member(
    project_id: int,
    payload: ProjectMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if db.query(ProjectMember).filter_by(project_id=project_id, user_id=payload.user_id).first():
        raise HTTPException(400, "User already a member")

    db.add(ProjectMember(project_id=project_id, user_id=payload.user_id, role=payload.role))
    db.commit()
    return {"detail": "Member added"}


@router.get("/{project_id}/members", response_model=List[UserOut])
def list_members(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    members = db.query(ProjectMember).filter_by(project_id=project_id).all()
    return [m.user for m in members]
