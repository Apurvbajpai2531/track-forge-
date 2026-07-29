import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class IssueStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    in_review = "in_review"
    done = "done"


class IssuePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueType(str, enum.Enum):
    bug = "bug"
    task = "task"
    story = "story"
    epic = "epic"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    issues_reported = relationship("Issue", back_populates="reporter", foreign_keys="Issue.reporter_id")
    issues_assigned = relationship("Issue", back_populates="assignee", foreign_keys="Issue.assignee_id")
    comments = relationship("Comment", back_populates="author")
    memberships = relationship("ProjectMember", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    issue_seq = Column(Integer, default=0)

    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(20), unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.todo, nullable=False)
    priority = Column(Enum(IssuePriority), default=IssuePriority.medium, nullable=False)
    type = Column(Enum(IssueType), default=IssueType.task, nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="issues")
    reporter = relationship("User", back_populates="issues_reported", foreign_keys=[reporter_id])
    assignee = relationship("User", back_populates="issues_assigned", foreign_keys=[assignee_id])
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")
    labels = relationship("IssueLabel", back_populates="issue", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="issue", cascade="all, delete-orphan")
    sprint_entries = relationship("SprintIssue", back_populates="issue", cascade="all, delete-orphan")
    time_logs = relationship("TimeLog", back_populates="issue", cascade="all, delete-orphan")
    outgoing_relations = relationship("IssueRelation", foreign_keys="IssueRelation.from_issue_id", back_populates="from_issue", cascade="all, delete-orphan")
    incoming_relations = relationship("IssueRelation", foreign_keys="IssueRelation.to_issue_id", back_populates="to_issue", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", back_populates="issue", cascade="all, delete-orphan")

    story_points = Column(Integer, nullable=True)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7), default="#5b8def")

    project = relationship("Project")


class IssueLabel(Base):
    __tablename__ = "issue_labels"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)

    issue = relationship("Issue", back_populates="labels")
    label = relationship("Label")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="activity_logs")
    user = relationship("User")


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    goal = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="planning")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    issues = relationship("SprintIssue", back_populates="sprint", cascade="all, delete-orphan")


class SprintIssue(Base):
    __tablename__ = "sprint_issues"

    id = Column(Integer, primary_key=True, index=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)

    sprint = relationship("Sprint", back_populates="issues")
    issue = relationship("Issue", back_populates="sprint_entries")


class TimeLog(Base):
    __tablename__ = "time_logs"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    minutes = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="time_logs")
    user = relationship("User")


class IssueRelation(Base):
    __tablename__ = "issue_relations"

    id = Column(Integer, primary_key=True, index=True)
    from_issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    to_issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    relation_type = Column(String(30), default="blocks")

    from_issue = relationship("Issue", foreign_keys=[from_issue_id], back_populates="outgoing_relations")
    to_issue = relationship("Issue", foreign_keys=[to_issue_id], back_populates="incoming_relations")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    text = Column(String(255), nullable=False)
    is_done = Column(Boolean, default=False)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("Issue", back_populates="checklist_items")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class IssueTemplate(Base):
    __tablename__ = "issue_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(20), default="task")
    priority = Column(String(20), default="medium")
    default_title = Column(String(255), nullable=True)

    project = relationship("Project")