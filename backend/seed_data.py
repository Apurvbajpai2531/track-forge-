"""
Temporary seed script — quickly populates a fresh demo project with
12 issues spread across all board columns, plus labels/comments.

Run from backend/ folder (venv active):
    python seed_data.py
"""

import random
from datetime import datetime, timedelta

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.models import (
    User, Project, ProjectMember, Issue, IssueStatus, IssuePriority,
    IssueType, Label, IssueLabel, Comment
)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

PROJECT_KEY = "QUICK"  # change this if you run it more than once

try:
    if db.query(Project).filter(Project.key == PROJECT_KEY).first():
        print(f"Project '{PROJECT_KEY}' already exists. Change PROJECT_KEY in the script and re-run.")
    else:
        print("Seeding quick demo data...")

        # Reuse existing user if 'alice' already exists, else create one
        alice = db.query(User).filter(User.username == "alice").first()
        if not alice:
            alice = User(
                username="alice", email="alice@example.com", full_name="Alice Johnson",
                hashed_password=hash_password("password123"),
            )
            db.add(alice)
            db.commit()
            db.refresh(alice)

        bob = db.query(User).filter(User.username == "bob").first()
        if not bob:
            bob = User(
                username="bob", email="bob@example.com", full_name="Bob Smith",
                hashed_password=hash_password("password123"),
            )
            db.add(bob)
            db.commit()
            db.refresh(bob)

        project = Project(
            key=PROJECT_KEY,
            name="Quick Demo Board",       # <-- temporary project name, change if you like
            description="Auto-seeded demo project with sample issues.",
            issue_seq=0,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        db.add_all([
            ProjectMember(project_id=project.id, user_id=alice.id, role="admin"),
            ProjectMember(project_id=project.id, user_id=bob.id, role="member"),
        ])
        db.commit()

        label_bug = Label(project_id=project.id, name="bug", color="#e25563")
        label_ui = Label(project_id=project.id, name="ui", color="#5b8def")
        label_urgent = Label(project_id=project.id, name="urgent", color="#f2b94b")
        db.add_all([label_bug, label_ui, label_urgent])
        db.commit()
        db.refresh(label_bug)
        db.refresh(label_ui)
        db.refresh(label_urgent)

        statuses = [IssueStatus.todo, IssueStatus.in_progress, IssueStatus.in_review, IssueStatus.done]
        priorities = [IssuePriority.low, IssuePriority.medium, IssuePriority.high, IssuePriority.critical]
        types = [IssueType.task, IssueType.bug, IssueType.story, IssueType.epic]

        titles = [
            "Set up project repository",
            "Fix login page crash on mobile",
            "Design new dashboard layout",
            "Database connection timeout under load",
            "Write API documentation",
            "Implement dark mode toggle",
            "Add pagination to issues list",
            "Fix broken image upload",
            "Improve search performance",
            "Add email notifications",
            "Refactor authentication module",
            "Set up CI pipeline",
            "Polish mobile board view",
            "Add CSV export for issues",
            "Fix typo on settings page",
        ]

        created = []
        for i, title in enumerate(titles[:12]):  # 12 issues
            project.issue_seq += 1
            status = statuses[i % 4]  # cycles evenly through all 4 columns
            due = (datetime.utcnow() + timedelta(days=random.choice([-2, 1, 3, 7, 14]))
                   if random.random() > 0.4 else None)

            issue = Issue(
                key=f"{project.key}-{project.issue_seq}",
                project_id=project.id,
                title=title,
                description=f"Seed description for '{title}'.",
                status=status,
                priority=random.choice(priorities),
                type=random.choice(types),
                reporter_id=alice.id,
                assignee_id=random.choice([alice.id, bob.id, None]),
                due_date=due,
            )
            db.add(issue)
            created.append(issue)

        db.commit()
        for issue in created:
            db.refresh(issue)

        # sprinkle some labels + comments
        for issue in random.sample(created, k=6):
            db.add(IssueLabel(issue_id=issue.id, label_id=random.choice([label_bug.id, label_ui.id, label_urgent.id])))

        for issue in random.sample(created, k=4):
            db.add(Comment(issue_id=issue.id, author_id=random.choice([alice.id, bob.id]),
                           body="Looks good, just double-checking the edge cases."))

        db.commit()

        print("✅ Done!")
        print(f"Project: {project.name}  (key={project.key}, id={project.id})")
        print(f"Created {len(created)} issues across To Do / In Progress / In Review / Done.")
        print("Login: alice / password123  or  bob / password123")
        print("(Or just log in with your own account — board is visible to everyone.)")

finally:
    db.close()
