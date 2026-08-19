from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import Base, engine
from app.models import models  # noqa
from app.routers import auth, projects, issues, comments, labels, dashboard, sprints, timelogs, bulk
from app.routers import reactions

from app.routers.reactions import CommentReaction
from app.routers import (
    auth, projects, issues, comments, labels,
    dashboard, sprints, timelogs, bulk,
    checklist, notifications, templates, profile
)

app = FastAPI(title="TrackForge API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(labels.router)
app.include_router(dashboard.router)
app.include_router(sprints.router)
app.include_router(timelogs.router)
app.include_router(bulk.router)
app.include_router(reactions.router)
app.include_router(notifications.router)
app.include_router(checklist.router)
app.include_router(templates.router)
app.include_router(profile.router)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "trackforge-api", "version": "2.0.0"}

