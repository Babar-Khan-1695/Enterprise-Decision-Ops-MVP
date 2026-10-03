import sqlite3
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
            report TEXT DEFAULT '',
            error_message TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            finding TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(decisions)").fetchall()}
        if "error_message" not in columns:
            conn.execute("ALTER TABLE decisions ADD COLUMN error_message TEXT DEFAULT ''")
        conn.commit()


def save_decision(decision_id, title, objective, status, created_at, report="", error_message=""):
    with get_connection() as conn:
        conn.execute("""INSERT OR REPLACE INTO decisions
            (decision_id,title,objective,status,created_at,report,error_message)
            VALUES (?,?,?,?,?,?,?)""", (decision_id, title, objective, status, created_at, report, error_message))
        conn.commit()


def update_decision_status(decision_id, status, report=None, error_message=None):
    with get_connection() as conn:
        if report is None and error_message is None:
            conn.execute("UPDATE decisions SET status=? WHERE decision_id=?", (status, decision_id))
        elif report is None:
            conn.execute("UPDATE decisions SET status=?, error_message=? WHERE decision_id=?", (status, error_message or "", decision_id))
        elif error_message is None:
            conn.execute("UPDATE decisions SET status=?, report=? WHERE decision_id=?", (status, report, decision_id))
        else:
            conn.execute("UPDATE decisions SET status=?, report=?, error_message=? WHERE decision_id=?", (status, report, error_message or "", decision_id))
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
