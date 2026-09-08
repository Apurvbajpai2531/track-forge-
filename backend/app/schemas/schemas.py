from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from app.models.models import IssueStatus, IssuePriority, IssueType


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    key: str
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str = "member"


# ---------- Issues ----------

class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: IssueStatus = IssueStatus.todo
    priority: IssuePriority = IssuePriority.medium
    type: IssueType = IssueType.task
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    label_ids: Optional[List[int]] = None
    story_points: Optional[int] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    type: Optional[IssueType] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    story_points: Optional[int] = None


class IssueOut(BaseModel):
    id: int
    key: str
    project_id: int
    title: str
    description: Optional[str] = None
    status: IssueStatus
    priority: IssuePriority
    type: IssueType
    reporter_id: int
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    story_points: Optional[int] = None

    class Config:
        from_attributes = True

# ---------- Comments ----------


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: int
    issue_id: int
    author_id: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class LabelCreate(BaseModel):
    name: str
    color: str = "#5b8def"


class LabelOut(BaseModel):
    id: int
    project_id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class ActivityLogOut(BaseModel):
    id: int
    issue_id: int
    user_id: int
    action: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_issues: int
    by_status: dict
    by_priority: dict
    overdue: int


class PaginatedIssues(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[IssueOut]

    # ---------- Sprints ----------


class SprintCreate(BaseModel):
    name: str
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintOut(BaseModel):
    id: int
    project_id: int
    name: str
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SprintIssueAdd(BaseModel):
    issue_id: int


# ---------- Time Logs ----------
class TimeLogCreate(BaseModel):
    minutes: int
    note: Optional[str] = None


class TimeLogOut(BaseModel):
    id: int
    issue_id: int
    user_id: int
    minutes: int
    note: Optional[str] = None
    logged_at: datetime

    class Config:
        from_attributes = True


# ---------- Issue Relations ----------
class IssueRelationCreate(BaseModel):
    to_issue_id: int
    relation_type: str = "blocks"


class IssueRelationOut(BaseModel):
    id: int
    from_issue_id: int
    to_issue_id: int
    relation_type: str

    class Config:
        from_attributes = True


# ---------- Bulk Action ----------
class BulkAction(BaseModel):
    issue_ids: List[int]
    action: str          # "set_status", "set_priority", "delete"
    value: Optional[str] = None

    # ---------- Checklist ----------


class ChecklistItemCreate(BaseModel):
    text: str
    position: int = 0


class ChecklistItemOut(BaseModel):
    id: int
    issue_id: int
    text: str
    is_done: bool
    position: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Notifications ----------
class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Issue Templates ----------
class IssueTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "task"
    priority: str = "medium"
    default_title: Optional[str] = None


class IssueTemplateOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    type: str
    priority: str
    default_title: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- User Update ----------
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
