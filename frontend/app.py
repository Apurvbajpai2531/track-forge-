import os
import json
import logging
from datetime import datetime
from functools import wraps

import requests
from requests.exceptions import RequestException
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, Response, jsonify
)


app = Flask(__name__)
app.secret_key = os.getenv("FRONTEND_SECRET_KEY", "dev-secret-change-me")
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")
REQUEST_TIMEOUT = float(os.getenv("API_TIMEOUT_SECONDS", "5"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trackforge.frontend")


def api_headers():
    token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_call(method, path, **kwargs):
    url = f"{API_BASE}{path}"
    try:
        return requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    except RequestException as exc:
        logger.error("Backend call failed: %s %s -> %s", method, url, exc)

        class _Unavailable:
            status_code = 503
            content = b""
            def json(self): return {"detail": "Backend service unavailable."}

        return _Unavailable()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("token"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def handle_auth_failure(resp):
    if getattr(resp, "status_code", None) == 401:
        session.clear()
        flash("Session expired. Please log in again.", "error")
        return True
    return False


@app.context_processor
def inject_globals():
    return {"now": datetime.utcnow().isoformat()}


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong"), 500


# ===== Auth =====

@app.route("/")
def index():
    return redirect(url_for("projects_list") if session.get("token") else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        payload = {
            "username": request.form["username"],
            "email": request.form["email"],
            "full_name": request.form.get("full_name", ""),
            "password": request.form["password"],
        }
        resp = api_call("POST", "/auth/register", json=payload)
        if resp.status_code == 201:
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        flash(resp.json().get("detail", "Registration failed"), "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        payload = {"username": request.form["username"], "password": request.form["password"]}
        resp = api_call("POST", "/auth/login", json=payload)
        if resp.status_code == 200:
            session["token"] = resp.json()["access_token"]
            session["username"] = payload["username"]
            return redirect(url_for("welcome"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/welcome")
@login_required
def welcome():
    # Get user info
    me_resp = api_call("GET", "/auth/me", headers=api_headers())
    user = me_resp.json() if me_resp.status_code == 200 else {"username": session.get("username", ""), "full_name": ""}

    # Get all projects to find most recent one
    projects_resp = api_call("GET", "/projects", headers=api_headers())
    projects = projects_resp.json() if projects_resp.status_code == 200 else []

    # Get dashboard stats from first project if available
    stats = {}
    last_project = None
    if projects:
        last_project = projects[-1]
        stats_resp = api_call("GET", f"/projects/{last_project['id']}/dashboard", headers=api_headers())
        if stats_resp.status_code == 200:
            stats = stats_resp.json()

    return render_template("welcome.html", user=user, stats=stats, project=last_project)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ===== Projects =====

@app.route("/projects")
@login_required
def projects_list():
    resp = api_call("GET", "/projects", headers=api_headers())
    if handle_auth_failure(resp):
        return redirect(url_for("login"))
    projects = resp.json() if resp.status_code == 200 else []
    return render_template("projects.html", projects=projects)


@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    if request.method == "POST":
        payload = {
            "key": request.form["key"].upper(),
            "name": request.form["name"],
            "description": request.form.get("description", ""),
        }
        resp = api_call("POST", "/projects", json=payload, headers=api_headers())
        if resp.status_code == 201:
            return redirect(url_for("projects_list"))
        flash(resp.json().get("detail", "Could not create project"), "error")
    return render_template("project_new.html")


# ===== Board =====

@app.route("/projects/<int:project_id>/board")
@login_required
def board(project_id):
    search = request.args.get("search", "")
    filter_type = request.args.get("filter", "all")

    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    me_resp = api_call("GET", "/auth/me", headers=api_headers())
    me = me_resp.json() if me_resp.status_code == 200 else {}

    params = {}
    if search:
        params["search"] = search
    if filter_type == "mine" and me.get("id"):
        params["assignee_id"] = me["id"]

    issues_resp = api_call(
        "GET",
        f"/projects/{project_id}/issues",
        params=params,
        headers=api_headers()
    )

    project = project_resp.json() if project_resp.status_code == 200 else None
    data = issues_resp.json() if issues_resp.status_code == 200 else []
    issues = data.get("items", data) if isinstance(data, dict) else data

    if filter_type == "overdue":
        now = datetime.utcnow().isoformat()
        issues = [
            i for i in issues
            if i.get("due_date")
            and i["due_date"] < now
            and i["status"] != "done"
        ]

    columns = {
        "todo": [],
        "in_progress": [],
        "in_review": [],
        "done": []
    }

    for issue in issues:
        columns.setdefault(issue["status"], []).append(issue)

    total = sum(len(issue_list) for issue_list in columns.values())

    return render_template(
        "board.html",
        project=project,
        columns=columns,
        total=total,
        search=search,
        filter_type=filter_type
    )


# ===== Issues =====

@app.route("/projects/<int:project_id>/issues/new", methods=["GET", "POST"])
@login_required
def issue_new(project_id):
    if request.method == "POST":
        payload = {
            "title": request.form["title"],
            "description": request.form.get("description", ""),
            "priority": request.form.get("priority", "medium"),
            "type": request.form.get("type", "task"),
            "due_date": request.form.get("due_date") or None,
            "story_points": int(request.form["story_points"]) if request.form.get("story_points") else None,
        }
        resp = api_call("POST", f"/projects/{project_id}/issues", json=payload, headers=api_headers())
        if resp.status_code == 201:
            return redirect(url_for("board", project_id=project_id))
        flash("Could not create issue", "error")
    templates_resp = api_call("GET", f"/projects/{project_id}/templates", headers=api_headers())
    templates = templates_resp.json() if templates_resp.status_code == 200 else []
    return render_template("issue_new.html", project_id=project_id, templates=templates)


@app.route("/projects/<int:project_id>/issues/<int:issue_id>", methods=["GET", "POST"])
@login_required
def issue_detail(project_id, issue_id):
    if request.method == "POST":
        payload = {"status": request.form["status"]}
        api_call("PATCH", f"/projects/{project_id}/issues/{issue_id}", json=payload, headers=api_headers())
        return redirect(url_for("issue_detail", project_id=project_id, issue_id=issue_id))

    issue_resp = api_call("GET", f"/projects/{project_id}/issues/{issue_id}", headers=api_headers())
    comments_resp = api_call("GET", f"/issues/{issue_id}/comments", headers=api_headers())
    activity_resp = api_call("GET", f"/projects/{project_id}/issues/{issue_id}/activity", headers=api_headers())
    timelogs_resp = api_call("GET", f"/issues/{issue_id}/timelogs", headers=api_headers())
    total_time_resp = api_call("GET", f"/issues/{issue_id}/timelogs/total", headers=api_headers())

    issue = issue_resp.json() if issue_resp.status_code == 200 else None
    comments = comments_resp.json() if comments_resp.status_code == 200 else []
    activity = activity_resp.json() if activity_resp.status_code == 200 else []
    timelogs = timelogs_resp.json() if timelogs_resp.status_code == 200 else []
    total_time = total_time_resp.json() if total_time_resp.status_code == 200 else {}

    return render_template(
        "issue_detail.html",
        issue=issue, comments=comments, activity=activity,
        timelogs=timelogs, total_time=total_time, project_id=project_id
    )


@app.route("/projects/<int:project_id>/issues/<int:issue_id>/comment", methods=["POST"])
@login_required
def add_comment(project_id, issue_id):
    body = request.form.get("body", "").strip()
    if body:
        api_call("POST", f"/issues/{issue_id}/comments", json={"body": body}, headers=api_headers())
    return redirect(url_for("issue_detail", project_id=project_id, issue_id=issue_id))


@app.route("/projects/<int:project_id>/issues/<int:issue_id>/log-time", methods=["POST"])
@login_required
def log_time(project_id, issue_id):
    try:
        minutes = int(request.form.get("minutes", 0))
    except ValueError:
        minutes = 0
    note = request.form.get("note", "").strip()
    if minutes > 0:
        api_call("POST", f"/issues/{issue_id}/timelogs", json={"minutes": minutes, "note": note}, headers=api_headers())
        flash(f"Logged {minutes} minutes successfully.", "success")
    return redirect(url_for("issue_detail", project_id=project_id, issue_id=issue_id))


# ===== AJAX =====

@app.route("/projects/<int:project_id>/issues/<int:issue_id>/json")
@login_required
def issue_json(project_id, issue_id):
    issue_resp = api_call("GET", f"/projects/{project_id}/issues/{issue_id}", headers=api_headers())
    comments_resp = api_call("GET", f"/issues/{issue_id}/comments", headers=api_headers())
    issue = issue_resp.json() if issue_resp.status_code == 200 else None
    comments = comments_resp.json() if comments_resp.status_code == 200 else []
    return jsonify({"issue": issue, "comments": comments})


@app.route("/projects/<int:project_id>/issues/<int:issue_id>/comment-ajax", methods=["POST"])
@login_required
def add_comment_ajax(project_id, issue_id):
    body_text = (request.json or {}).get("body", "").strip()
    if not body_text:
        return jsonify({"ok": False, "error": "Body required"}), 400
    resp = api_call("POST", f"/issues/{issue_id}/comments", json={"body": body_text}, headers=api_headers())
    if resp.status_code == 201:
        return jsonify({"ok": True, "comment": resp.json()})
    return jsonify({"ok": False, "error": "Failed"}), 500


@app.route("/api/projects/<int:project_id>/issues/<int:issue_id>/move", methods=["POST"])
@login_required
def move_issue(project_id, issue_id):
    new_status = (request.json or {}).get("status")
    if new_status not in ("todo", "in_progress", "in_review", "done"):
        return jsonify({"ok": False, "error": "Invalid status"}), 400
    resp = api_call("PATCH", f"/projects/{project_id}/issues/{issue_id}",
                    json={"status": new_status}, headers=api_headers())
    if resp.status_code == 200:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Failed to update"}), resp.status_code


@app.route("/api/projects/<int:project_id>/bulk", methods=["POST"])
@login_required
def bulk_action(project_id):
    data = request.json or {}
    resp = api_call("POST", f"/projects/{project_id}/bulk", json=data, headers=api_headers())
    if resp.status_code == 200:
        return jsonify({"ok": True, "detail": resp.json().get("detail", "Done")})
    return jsonify({"ok": False, "error": resp.json().get("detail", "Failed")}), 400


@app.route("/projects/<int:project_id>/issues/export")
@login_required
def export_issues(project_id):
    resp = api_call("GET", f"/projects/{project_id}/issues/export/csv", headers=api_headers())
    if resp.status_code != 200:
        flash("Could not export issues", "error")
        return redirect(url_for("board", project_id=project_id))
    return Response(
        resp.content, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=issues_{project_id}.csv"},
    )


# ===== Dashboard =====

@app.route("/projects/<int:project_id>/dashboard")
@login_required
def project_dashboard(project_id):
    resp = api_call("GET", f"/projects/{project_id}/dashboard", headers=api_headers())
    stats = resp.json() if resp.status_code == 200 else {}
    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    project = project_resp.json() if project_resp.status_code == 200 else None
    return render_template("dashboard.html", stats=stats, project=project, project_id=project_id)


# ===== Sprints =====

@app.route("/projects/<int:project_id>/sprints")
@login_required
def sprint_list(project_id):
    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    sprints_resp = api_call("GET", f"/projects/{project_id}/sprints", headers=api_headers())
    project = project_resp.json() if project_resp.status_code == 200 else None
    sprints = sprints_resp.json() if sprints_resp.status_code == 200 else []

    sprint_issues = {}
    for sprint in sprints:
        issues_resp = api_call("GET", f"/projects/{project_id}/sprints/{sprint['id']}/issues", headers=api_headers())
        sprint_issues[sprint["id"]] = issues_resp.json() if issues_resp.status_code == 200 else []

    return render_template("sprints.html", project=project, sprints=sprints, sprint_issues=sprint_issues)


@app.route("/projects/<int:project_id>/sprints/new", methods=["POST"])
@login_required
def sprint_new(project_id):
    payload = {
        "name": request.form["name"],
        "goal": request.form.get("goal", "") or None,
        "start_date": request.form.get("start_date") or None,
        "end_date": request.form.get("end_date") or None,
    }
    resp = api_call("POST", f"/projects/{project_id}/sprints", json=payload, headers=api_headers())
    if resp.status_code == 201:
        flash("Sprint created!", "success")
    else:
        flash("Could not create sprint", "error")
    return redirect(url_for("sprint_list", project_id=project_id))


@app.route("/projects/<int:project_id>/sprints/<int:sprint_id>/start")
@login_required
def sprint_start(project_id, sprint_id):
    api_call("PATCH", f"/projects/{project_id}/sprints/{sprint_id}/status",
             params={"status": "active"}, headers=api_headers())
    flash("Sprint started!", "success")
    return redirect(url_for("sprint_list", project_id=project_id))


@app.route("/projects/<int:project_id>/sprints/<int:sprint_id>/complete")
@login_required
def sprint_complete(project_id, sprint_id):
    api_call("PATCH", f"/projects/{project_id}/sprints/{sprint_id}/status",
             params={"status": "completed"}, headers=api_headers())
    flash("Sprint completed!", "success")
    return redirect(url_for("sprint_list", project_id=project_id))


# ===== Roadmap =====

@app.route("/projects/<int:project_id>/roadmap")
@login_required
def roadmap(project_id):
    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    issues_resp = api_call("GET", f"/projects/{project_id}/issues", headers=api_headers())
    project = project_resp.json() if project_resp.status_code == 200 else None
    data = issues_resp.json() if issues_resp.status_code == 200 else []
    issues = data.get("items", data) if isinstance(data, dict) else data
    return render_template("roadmap.html", project=project, issues=issues, project_id=project_id)


# ===== Profile =====

@app.route("/profile")
@login_required
def profile_page():
    resp = api_call("GET", "/auth/me", headers=api_headers())
    user = resp.json() if resp.status_code == 200 else {}
    return render_template("profile.html", user=user)


@app.route("/profile/update", methods=["POST"])
@login_required
def profile_update():
    payload = {}
    if request.form.get("full_name"):
        payload["full_name"] = request.form["full_name"]
    if request.form.get("email"):
        payload["email"] = request.form["email"]
    if request.form.get("password"):
        payload["password"] = request.form["password"]
    resp = api_call("PATCH", "/profile", json=payload, headers=api_headers())
    if resp.status_code == 200:
        flash("Profile updated!", "success")
    else:
        flash(resp.json().get("detail", "Update failed"), "error")
    return redirect(url_for("profile_page"))


# ===== Notifications =====

@app.route("/notifications")
@login_required
def notifications_page():
    resp = api_call("GET", "/notifications", headers=api_headers())
    notifications = resp.json() if resp.status_code == 200 else []
    return render_template("notifications.html", notifications=notifications)


@app.route("/api/notifications/unread-count")
@login_required
def notifications_unread_count():
    resp = api_call("GET", "/notifications/unread-count", headers=api_headers())
    return jsonify(resp.json() if resp.status_code == 200 else {"count": 0})


@app.route("/notifications/mark-all", methods=["POST"])
@login_required
def notifications_mark_all():
    api_call("POST", "/notifications/mark-all-read", headers=api_headers())
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications_page"))


# ===== Project Settings / Members / Templates =====

@app.route("/projects/<int:project_id>/settings")
@login_required
def project_settings(project_id):
    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    members_resp = api_call("GET", f"/projects/{project_id}/members", headers=api_headers())
    templates_resp = api_call("GET", f"/projects/{project_id}/templates", headers=api_headers())
    project = project_resp.json() if project_resp.status_code == 200 else None
    members = members_resp.json() if members_resp.status_code == 200 else []
    templates = templates_resp.json() if templates_resp.status_code == 200 else []
    return render_template("project_settings.html", project=project, members=members, templates=templates)


@app.route("/projects/<int:project_id>/members/add", methods=["POST"])
@login_required
def project_add_member(project_id):
    payload = {"user_id": int(request.form["user_id"]), "role": request.form.get("role", "member")}
    resp = api_call("POST", f"/projects/{project_id}/members", json=payload, headers=api_headers())
    if resp.status_code == 201:
        flash("Member added!", "success")
    else:
        flash(resp.json().get("detail", "Failed to add member"), "error")
    return redirect(url_for("project_settings", project_id=project_id))


@app.route("/projects/<int:project_id>/templates/new", methods=["POST"])
@login_required
def create_template(project_id):
    payload = {
        "name": request.form["name"],
        "default_title": request.form.get("default_title") or None,
        "type": request.form.get("type", "task"),
        "priority": request.form.get("priority", "medium"),
        "description": request.form.get("description") or None,
    }
    resp = api_call("POST", f"/projects/{project_id}/templates", json=payload, headers=api_headers())
    if resp.status_code == 201:
        flash("Template created!", "success")
    else:
        flash("Failed to create template", "error")
    return redirect(url_for("project_settings", project_id=project_id))


@app.route("/projects/<int:project_id>/templates/<int:template_id>/delete", methods=["POST"])
@login_required
def delete_template(project_id, template_id):
    api_call("DELETE", f"/projects/{project_id}/templates/{template_id}", headers=api_headers())
    flash("Template deleted.", "success")
    return redirect(url_for("project_settings", project_id=project_id))


@app.route("/projects/<int:project_id>/issues/new-with-templates", methods=["GET", "POST"])
@login_required
def issue_new_with_templates(project_id):
    if request.method == "POST":
        payload = {
            "title": request.form["title"],
            "description": request.form.get("description", ""),
            "priority": request.form.get("priority", "medium"),
            "type": request.form.get("type", "task"),
            "due_date": request.form.get("due_date") or None,
        }
        resp = api_call("POST", f"/projects/{project_id}/issues", json=payload, headers=api_headers())
        if resp.status_code == 201:
            return redirect(url_for("board", project_id=project_id))
        flash("Could not create issue", "error")
    templates_resp = api_call("GET", f"/projects/{project_id}/templates", headers=api_headers())
    templates = templates_resp.json() if templates_resp.status_code == 200 else []
    return render_template("issue_new.html", project_id=project_id, templates=templates)


# ===== AI features (via local Ollama) =====

def call_ollama(prompt, max_tokens=400, json_mode=False):
    """Calls local Ollama instead of Anthropic. Raises on failure."""
    import requests as req
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens}
    }
    if json_mode:
        payload["format"] = "json"

    resp = req.post(
        "http://stockloom-ollama:11434/api/generate",
        json=payload,
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Ollama error: {resp.status_code} {resp.text}")
    return resp.json()["response"].strip()


@app.route("/projects/<int:project_id>/ai-create")
@login_required
def ai_create(project_id):
    return render_template("ai_create.html", project_id=project_id)


@app.route("/ai/generate-issue", methods=["POST"])
@login_required
def ai_generate_issue():
    prompt = (request.json or {}).get("prompt", "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "No prompt provided"}), 400

    try:
        full_prompt = f"""You are a project management assistant. Convert this plain English description into a structured issue.

Description: {prompt}

Respond with ONLY valid JSON (no markdown, no explanation, no extra text before or after). Use \\n for line breaks inside string values, never literal newlines:
{"title": "concise issue title under 60 chars",
  "description": "## Problem\\nDetailed description\\n\\n## Steps to Reproduce\\n1. \\n\\n## Expected\\n\\n## Actual\\n",
  "type": "bug or task or story or epic",
  "priority": "low or medium or high or critical"
} """

        content = call_ollama(full_prompt, max_tokens=600, json_mode=True)

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        # strict=False allows literal control chars (raw newlines) inside strings —
        # small models often break this rule even in json_mode
        data = json.loads(content.strip(), strict=False)

        return jsonify({
            "ok": True,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "type": data.get("type", "task"),
            "priority": data.get("priority", "medium"),
        })

    except Exception as e:
        logger.error("AI generate error: %s", e)
        return jsonify({"ok": False, "error": "AI generation failed"}), 500


@app.route("/projects/<int:project_id>/standup")
@login_required
def standup(project_id):
    project_resp = api_call("GET", f"/projects/{project_id}", headers=api_headers())
    project = project_resp.json() if project_resp.status_code == 200 else None
    return render_template("standup.html", project=project, project_id=project_id)


@app.route("/api/projects/<int:project_id>/standup/generate", methods=["POST"])
@login_required
def generate_standup(project_id):
    issues_resp = api_call("GET", f"/projects/{project_id}/issues", headers=api_headers())
    data = issues_resp.json() if issues_resp.status_code == 200 else []
    issues = data.get("items", data) if isinstance(data, dict) else data

    in_progress = [i for i in issues if i["status"] == "in_progress"]
    done_recently = [i for i in issues if i["status"] == "done"][:5]
    overdue = [i for i in issues if i.get("due_date") and i["due_date"] <
               datetime.utcnow().isoformat() and i["status"] != "done"]

    context = f"""
    In Progress: {[i['title'] for i in in_progress[:5]]}
    Recently Done: {[i['title'] for i in done_recently]}
    Overdue/Blocked: {[i['title'] for i in overdue[:3]]}
    """

    try:
        full_prompt = f"""Generate a concise daily standup update based on this project data.

{context}

Format it as:
✅ Yesterday: (what was completed)
🔄 Today: (what's being worked on)
🚧 Blockers: (any blockers or risks)

Keep it brief, professional, under 100 words total."""

        text = call_ollama(full_prompt, max_tokens=400)
        return jsonify({"ok": True, "standup": text})
    except Exception as e:
        logger.error("Standup generate error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


CHAT_DAILY_LIMIT = int(os.getenv("CHAT_DAILY_LIMIT", "20"))


def get_chat_usage():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage = session.get("chat_usage", {})
    if usage.get("date") != today:
        usage = {"date": today, "count": 0}
    return usage


@app.route("/ai/chat/usage")
@login_required
def ai_chat_usage():
    usage = get_chat_usage()
    remaining = max(0, CHAT_DAILY_LIMIT - usage["count"])
    return jsonify({"remaining": remaining, "limit": CHAT_DAILY_LIMIT})


@app.route("/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    usage = get_chat_usage()
    if usage["count"] >= CHAT_DAILY_LIMIT:
        return jsonify({
            "ok": False,
            "error": "Daily message limit reached. Try again tomorrow.",
            "remaining": 0,
            "limit": CHAT_DAILY_LIMIT
        }), 429

    data = request.json or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])  # list of {"role": "user"/"assistant", "content": "..."}

    if not message:
        return jsonify({"ok": False, "error": "No message provided"}), 400

    try:
        system_prefix = (
            "You are a helpful assistant embedded inside TrackForge, a project "
            "management tool. Answer clearly and concisely. If asked about "
            "TrackForge itself, mention it has projects, a kanban board, sprints, "
            "labels, comments, and a dashboard.\n\n"
        )

        convo = ""
        for turn in history[-10:]:
            role = "User" if turn.get("role") == "user" else "Assistant"
            convo += f"{role}: {turn.get('content', '')}\n"
        convo += f"User: {message}\nAssistant:"

        full_prompt = system_prefix + convo
        reply = call_ollama(full_prompt, max_tokens=500)

        usage["count"] += 1
        session["chat_usage"] = usage
        remaining = max(0, CHAT_DAILY_LIMIT - usage["count"])

        return jsonify({"ok": True, "reply": reply, "remaining": remaining, "limit": CHAT_DAILY_LIMIT})

    except Exception as e:
        logger.error("AI chat error: %s", e)
        return jsonify({"ok": False, "error": "AI assistant unavailable"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
