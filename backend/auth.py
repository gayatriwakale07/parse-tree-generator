"""Register / login / logout endpoints plus activity logging helpers (MySQL)."""
import json
from functools import wraps

from flask import Blueprint, jsonify, request, session
from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, fetch_all, fetch_one

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


# ---------- helpers ----------

def log_activity(action, details=None):
    """Store one action for the currently logged-in user (no-op if nobody is logged in)."""
    user_id = session.get("user_id")
    if not user_id:
        return
    execute(
        "INSERT INTO activity_log (user_id, session_id, action, details) "
        "VALUES (%s, %s, %s, %s)",
        (
            user_id,
            session.get("login_session_id"),
            action,
            json.dumps(details) if details is not None else None,
        ),
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Please log in to continue."), 401
        return view(*args, **kwargs)

    return wrapped


# ---------- routes ----------

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not 3 <= len(username) <= 30:
        return jsonify(error="Username must be 3 to 30 characters."), 400
    if len(password) < 6:
        return jsonify(error="Password must be at least 6 characters."), 400

    try:
        execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, generate_password_hash(password)),
        )
    except IntegrityError:
        return jsonify(error="That username is already taken."), 409

    return jsonify(message="Account created. You can log in now."), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = fetch_one("SELECT * FROM users WHERE username = %s", (username,))
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Wrong username or password."), 401

    session_id = execute(
        "INSERT INTO login_sessions (user_id, ip_address, user_agent) VALUES (%s, %s, %s)",
        (user["id"], request.remote_addr, request.headers.get("User-Agent", "")[:255]),
    )

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["login_session_id"] = session_id
    log_activity("login")

    return jsonify(username=user["username"])


@auth_bp.post("/logout")
@login_required
def logout():
    log_activity("logout")
    execute(
        "UPDATE login_sessions SET logout_at = CURRENT_TIMESTAMP WHERE id = %s",
        (session.get("login_session_id"),),
    )
    session.clear()
    return jsonify(message="Logged out.")


@auth_bp.get("/me")
@login_required
def me():
    return jsonify(username=session["username"])


@auth_bp.get("/activity")
@login_required
def my_activity():
    rows = fetch_all(
        "SELECT action, details, created_at FROM activity_log "
        "WHERE user_id = %s ORDER BY id DESC LIMIT 50",
        (session["user_id"],),
    )
    for r in rows:
        r["created_at"] = r["created_at"].isoformat(sep=" ")
    return jsonify(activity=rows)