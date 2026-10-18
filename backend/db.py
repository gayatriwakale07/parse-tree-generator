"""MySQL setup (PyMySQL): users, login sessions and per-user activity log."""
import os

import pymysql
from flask import g
from pymysql.cursors import DictCursor

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        username      VARCHAR(254) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # one row per login; logout_at stays NULL until the user logs out
    """
    CREATE TABLE IF NOT EXISTS login_sessions (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        user_id    INT NOT NULL,
        login_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        logout_at  DATETIME NULL,
        ip_address VARCHAR(45),
        user_agent VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # every action a logged-in user performs
    """
    CREATE TABLE IF NOT EXISTS activity_log (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        user_id    INT NOT NULL,
        session_id INT NULL,
        action     VARCHAR(60) NOT NULL,
        details    JSON NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_activity_user (user_id, created_at),
        FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES login_sessions(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    # every parse tree a user generates (grammar, input and the resulting tree)
    """
    CREATE TABLE IF NOT EXISTS parse_history (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        user_id      INT NOT NULL,
        session_id   INT NULL,
        grammar      TEXT NOT NULL,
        input_string VARCHAR(500) NOT NULL,
        start_symbol VARCHAR(50)  NOT NULL,
        parse_tree   JSON NULL,
        steps        JSON NULL,
        success      TINYINT(1) NOT NULL DEFAULT 1,
        created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_history_user (user_id, created_at),
        FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES login_sessions(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def _connect(with_db=True):
    cfg = dict(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
    if with_db:
        cfg["database"] = os.getenv("DB_NAME", "parse_tree_db")
    return pymysql.connect(**cfg)


def get_db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---- small helpers so routes stay short ----

def execute(sql, params=()):
    """Run INSERT/UPDATE/DELETE, commit, return the new row id."""
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        db.commit()
        return cur.lastrowid


def fetch_one(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def init_db(app):
    """Create the database and tables if they don't exist yet."""
    app.teardown_appcontext(close_db)

    name = os.getenv("DB_NAME", "parse_tree_db")
    conn = _connect(with_db=False)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()

    conn = _connect()
    try:
        with conn.cursor() as cur:
            for statement in SCHEMA:
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()