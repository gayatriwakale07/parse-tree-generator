"""Parse Tree Generator backend: login, activity log, parsing and per-user history (Flask + MySQL)."""
import json
import os
import re
from functools import wraps

from dotenv import load_dotenv

load_dotenv()  # must run before db.py reads its settings

from flask import Flask, jsonify, redirect, request, session
from flask_cors import CORS
from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, fetch_all, fetch_one, init_db
from ll1 import GrammarError, ParseError, parse_input

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
MIN_PASSWORD = 10

# The frontend folder is served by Flask itself, so the whole app lives at ONE address
# (http://localhost:5000). Same origin = no CORS or cookie problems in any browser.
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

CORS(
    app,
    supports_credentials=True,
    origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:5500")],
)

init_db(app)  # creates the database and tables on first run


# =====================================================================
# Helpers
# =====================================================================

def log_activity(action, details=None):
    """Store one action for the logged-in user (does nothing if nobody is logged in)."""
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


def save_parse(grammar, input_string, start_symbol, parse_tree=None, steps=None, success=True):
    """Store one parse attempt for the logged-in user. Returns the new history id."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    history_id = execute(
        "INSERT INTO parse_history "
        "(user_id, session_id, grammar, input_string, start_symbol, parse_tree, steps, success) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            session.get("login_session_id"),
            grammar,
            input_string[:500],
            start_symbol,
            json.dumps(parse_tree) if parse_tree is not None else None,
            json.dumps(steps) if steps is not None else None,
            1 if success else 0,
        ),
    )
    log_activity(
        "generate_parse_tree",
        {"history_id": history_id, "input": input_string, "start": start_symbol, "success": success},
    )
    return history_id


# =====================================================================
# Health
# =====================================================================

@app.get("/")
def home():
    return redirect("/login.html")


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response


@app.get("/api/health")
def health():
    return jsonify(success=True, message="Parse Tree Generator backend is running")


# =====================================================================
# Register / login / logout
# =====================================================================

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()  # the "username" is the email address
    password = data.get("password") or ""

    if not username and not password:
        return jsonify(error="Please fill in all the information."), 400
    if not username:
        return jsonify(error="Please enter your email address."), 400
    if not password:
        return jsonify(error="Please enter your password."), 400
    if len(username) > 254 or not EMAIL_RE.match(username):
        return jsonify(error="Enter a valid email address, for example name@example.com."), 400
    if not MIN_PASSWORD <= len(password) <= 128:
        return jsonify(error=f"Password must be {MIN_PASSWORD} to 128 characters."), 400

    try:
        execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, generate_password_hash(password)),
        )
    except IntegrityError:
        return jsonify(error="That username is already taken."), 409

    return jsonify(message="Account created. You can log in now."), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username and not password:
        return jsonify(error="Please fill in all the information."), 400
    if not username:
        return jsonify(error="Please enter your email address."), 400
    if not password:
        return jsonify(error="Please enter your password."), 400

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


@app.post("/api/logout")
@login_required
def logout():
    log_activity("logout")
    execute(
        "UPDATE login_sessions SET logout_at = CURRENT_TIMESTAMP WHERE id = %s",
        (session.get("login_session_id"),),
    )
    session.clear()
    return jsonify(message="Logged out.")


@app.get("/api/me")
@login_required
def me():
    return jsonify(username=session["username"])


@app.get("/api/activity")
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


# =====================================================================
# Parsing
# =====================================================================

@app.post("/api/parse")
@login_required
def parse_route():
    data = request.get_json(silent=True) or {}
    grammar = (data.get("grammar") or "").strip()
    input_string = (data.get("input") or "").strip()
    start = (data.get("start") or "").strip()

    if not grammar:
        return jsonify(error="Enter a grammar first."), 400
    if len(grammar) > 5000 or len(input_string) > 500 or len(start) > 50:
        return jsonify(error="Grammar or input is too long."), 400

    try:
        result = parse_input(grammar, input_string, start)
    except (GrammarError, ParseError) as err:
        save_parse(grammar, input_string, start, None, None, success=False)
        return jsonify(
            error=str(err),
            suggestions=err.suggestions,
            fixed_grammar=err.fixed_grammar,
            fixed_input=err.fixed_input,
        ), 422

    history_id = save_parse(
        grammar, input_string, result["start"], result["tree"], result["steps"], success=True
    )
    return jsonify(tree=result["tree"], steps=result["steps"], history_id=history_id)


@app.post("/api/event")
@login_required
def event():
    action = (request.get_json(silent=True) or {}).get("action")
    if action not in {"reset"}:
        return jsonify(error="Unknown action."), 400
    log_activity(action)
    return jsonify(ok=True)


# =====================================================================
# Per-user history
# =====================================================================

@app.get("/api/history")
@login_required
def list_history():
    rows = fetch_all(
        "SELECT id, grammar, input_string, start_symbol, success, created_at "
        "FROM parse_history WHERE user_id = %s ORDER BY id DESC LIMIT 50",
        (session["user_id"],),
    )
    for r in rows:
        r["created_at"] = r["created_at"].isoformat(sep=" ")
        r["success"] = bool(r["success"])
    return jsonify(history=rows)


@app.get("/api/history/<int:history_id>")
@login_required
def get_history(history_id):
    # user_id in the WHERE clause: nobody can open another user's record
    row = fetch_one(
        "SELECT * FROM parse_history WHERE id = %s AND user_id = %s",
        (history_id, session["user_id"]),
    )
    if row is None:
        return jsonify(error="That record was not found."), 404
    for key in ("parse_tree", "steps"):
        if row[key] is not None:
            row[key] = json.loads(row[key])
    row["created_at"] = row["created_at"].isoformat(sep=" ")
    row["success"] = bool(row["success"])
    log_activity("open_history", {"history_id": history_id})
    return jsonify(row)


@app.delete("/api/history/<int:history_id>")
@login_required
def delete_history(history_id):
    row = fetch_one(
        "SELECT id FROM parse_history WHERE id = %s AND user_id = %s",
        (history_id, session["user_id"]),
    )
    if row is None:
        return jsonify(error="That record was not found."), 404
    execute("DELETE FROM parse_history WHERE id = %s", (history_id,))
    log_activity("delete_history", {"history_id": history_id})
    return jsonify(message="Deleted.")


if __name__ == "__main__":
    app.run(
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )