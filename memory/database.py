import sqlite3
from pathlib import Path
from config.settings import MEMORY_DIR

DB_PATH = MEMORY_DIR / "decisionops.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            report TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            finding TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)


def save_decision(decision_id, title, objective, status, created_at, report=""):
    with get_connection() as conn:
        conn.execute("""INSERT OR REPLACE INTO decisions
            (decision_id,title,objective,status,created_at,report)
            VALUES (?,?,?,?,?,?)""", (decision_id, title, objective, status, created_at, report))
        conn.commit()


def save_finding(decision_id, agent_name, finding, created_at):
    with get_connection() as conn:
        conn.execute("INSERT INTO findings(decision_id,agent_name,finding,created_at) VALUES(?,?,?,?)",
                     (decision_id, agent_name, finding, created_at))
        conn.commit()


def list_decisions(limit=30):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()


def get_decision(decision_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM decisions WHERE decision_id=?", (decision_id,)).fetchone()
        findings = conn.execute("SELECT * FROM findings WHERE decision_id=? ORDER BY id", (decision_id,)).fetchall()
    return row, findings
