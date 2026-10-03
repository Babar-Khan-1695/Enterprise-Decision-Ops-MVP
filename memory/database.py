import sqlite3
from config.settings import MEMORY_DIR

DB_PATH = MEMORY_DIR / "decisionops.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column(conn, table, column, definition):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            status TEXT NOT NULL,
            executive_status TEXT DEFAULT 'Pending Executive Review',
            decision_type TEXT DEFAULT '',
            constraints TEXT DEFAULT '',
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
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            url TEXT DEFAULT '',
            accessed_at TEXT DEFAULT '',
            details TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        _add_column(conn, "decisions", "executive_status", "TEXT DEFAULT 'Pending Executive Review'")
        _add_column(conn, "decisions", "decision_type", "TEXT DEFAULT ''")
        _add_column(conn, "decisions", "constraints", "TEXT DEFAULT ''")
        _add_column(conn, "decisions", "error_message", "TEXT DEFAULT ''")
        conn.commit()


def save_decision(
    decision_id, title, objective, status, created_at, report="", error_message="",
    executive_status="Pending Executive Review", decision_type="", constraints=""
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO decisions
            (decision_id,title,objective,status,executive_status,decision_type,constraints,created_at,report,error_message)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(decision_id) DO UPDATE SET
                title=excluded.title,
                objective=excluded.objective,
                status=excluded.status,
                executive_status=excluded.executive_status,
                decision_type=excluded.decision_type,
                constraints=excluded.constraints,
                created_at=excluded.created_at,
                report=excluded.report,
                error_message=excluded.error_message
        """, (
            decision_id, title, objective, status, executive_status, decision_type,
            constraints, created_at, report, error_message or ""
        ))
        conn.commit()


def update_decision_status(decision_id, status=None, report=None, error_message=None, executive_status=None):
    updates, values = [], []
    if status is not None:
        updates.append("status=?"); values.append(status)
    if report is not None:
        updates.append("report=?"); values.append(report)
    if error_message is not None:
        updates.append("error_message=?"); values.append(error_message or "")
    if executive_status is not None:
        updates.append("executive_status=?"); values.append(executive_status)
    if not updates:
        return
    values.append(decision_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE decisions SET {', '.join(updates)} WHERE decision_id=?", values)
        conn.commit()


def save_finding(decision_id, agent_name, finding, created_at):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO findings(decision_id,agent_name,finding,created_at) VALUES(?,?,?,?)",
            (decision_id, agent_name, finding or "", created_at)
        )
        conn.commit()


def clear_findings(decision_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM findings WHERE decision_id=?", (decision_id,))
        conn.commit()


def replace_findings(decision_id, findings, created_at):
    clear_findings(decision_id)
    for agent_name, finding in findings:
        save_finding(decision_id, agent_name, finding, created_at)


def save_source(decision_id, source_name, source_type, url="", accessed_at="", details=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sources(decision_id,source_name,source_type,url,accessed_at,details) VALUES(?,?,?,?,?,?)",
            (decision_id, source_name, source_type, url or "", accessed_at or "", details or "")
        )
        conn.commit()


def replace_sources(decision_id, sources):
    with get_connection() as conn:
        conn.execute("DELETE FROM sources WHERE decision_id=?", (decision_id,))
        for s in sources:
            conn.execute(
                "INSERT INTO sources(decision_id,source_name,source_type,url,accessed_at,details) VALUES(?,?,?,?,?,?)",
                (
                    decision_id,
                    s.get("source_name", "Unknown source"),
                    s.get("source_type", "Unknown"),
                    s.get("url", ""),
                    s.get("accessed_at", ""),
                    s.get("details", ""),
                )
            )
        conn.commit()


def list_sources(decision_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM sources WHERE decision_id=? ORDER BY id", (decision_id,)
        ).fetchall()


def save_conversation(decision_id, speaker, message, created_at):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations(decision_id,speaker,message,created_at) VALUES(?,?,?,?)",
            (decision_id, speaker, message, created_at)
        )
        conn.commit()


def list_conversations(decision_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM conversations WHERE decision_id=? ORDER BY id", (decision_id,)
        ).fetchall()


def list_decisions(limit=30):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()


def get_decision(decision_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE decision_id=?", (decision_id,)
        ).fetchone()
        findings = conn.execute(
            "SELECT * FROM findings WHERE decision_id=? ORDER BY id", (decision_id,)
        ).fetchall()
    return row, findings


init_db()
