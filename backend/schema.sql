-- =====================================================================
-- Parse Tree Generator: MySQL schema and useful queries
-- The backend creates all of this AUTOMATICALLY on first start (db.py),
-- so running this file is optional. Run it manually with:
--     mysql -u root -p < schema.sql
-- =====================================================================

CREATE DATABASE IF NOT EXISTS parse_tree_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE parse_tree_db;

-- 1) Accounts (password is stored only as a hash)
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(30)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

USE parse_tree_db;
SELECT id, username, created_at FROM users;

-- 2) One row per login; logout_at stays NULL until the user logs out
CREATE TABLE IF NOT EXISTS login_sessions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    login_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_at  DATETIME NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Every action a logged-in user performs
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) Every generated parse tree (grammar + input + tree + steps)
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
-- Queries to inspect the data
-- =====================================================================

-- All users
SELECT id, username, created_at FROM users;

-- Login / logout history (NULL logout_at = still logged in or closed the tab)
SELECT u.username, s.login_at, s.logout_at, s.ip_address
FROM login_sessions s JOIN users u ON u.id = s.user_id
ORDER BY s.id DESC;

-- Everything one user did
SELECT a.created_at, a.action, a.details
FROM activity_log a JOIN users u ON u.id = a.user_id
WHERE u.username = 'your_username'
ORDER BY a.id DESC;

-- Saved grammars / inputs / trees with the owner's username
SELECT u.username, h.id, h.input_string, h.start_symbol, h.success, h.created_at
FROM parse_history h JOIN users u ON u.id = h.user_id
ORDER BY h.id DESC;

-- Full record of one saved parse (grammar, tree JSON, steps JSON)
SELECT grammar, parse_tree, steps FROM parse_history WHERE id = 1;

-- Activity count per user
SELECT u.username, COUNT(*) AS actions
FROM activity_log a JOIN users u ON u.id = a.user_id
GROUP BY u.username ORDER BY actions DESC;