import aiosqlite
from datetime import datetime

DB_PATH = "bot.db"


def now_iso() -> str:
    return datetime.utcnow().isoformat()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                finished_at TEXT,
                risk_level TEXT DEFAULT 'UNKNOWN',
                status TEXT DEFAULT 'active'
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                stage TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                scale_score TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS protocol_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                protocol_id TEXT NOT NULL,
                protocol_mode TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                review_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        await db.commit()


async def create_session(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO sessions (
                session_id,
                created_at,
                risk_level,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (session_id, now_iso(), "UNKNOWN", "active")
        )
        await db.commit()


async def update_session_risk(session_id: str, risk_level: str, status: str):
    finished_at = now_iso() if status in ["finished", "crisis"] else None

    async with aiosqlite.connect(DB_PATH) as db:
        if finished_at:
            await db.execute(
                """
                UPDATE sessions
                SET risk_level = ?, status = ?, finished_at = ?
                WHERE session_id = ?
                """,
                (risk_level, status, finished_at, session_id)
            )
        else:
            await db.execute(
                """
                UPDATE sessions
                SET risk_level = ?, status = ?
                WHERE session_id = ?
                """,
                (risk_level, status, session_id)
            )

        await db.commit()


async def save_message(session_id: str, role: str, text: str, stage: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                text,
                stage,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, text, stage, now_iso())
        )
        await db.commit()


async def save_assessment(session_id: str, scale_score: str, risk_level: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO assessments (
                session_id,
                scale_score,
                risk_level,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (session_id, scale_score, risk_level, now_iso())
        )
        await db.commit()


async def save_protocol_run(
    session_id: str,
    protocol_id: str,
    protocol_mode: str,
    attempt_number: int,
    result: str | None = None
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO protocol_runs (
                session_id,
                protocol_id,
                protocol_mode,
                attempt_number,
                result,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                protocol_id,
                protocol_mode,
                attempt_number,
                result,
                now_iso()
            )
        )
        await db.commit()


async def save_review(session_id: str | None, review_text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO reviews (
                session_id,
                review_text,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (session_id, review_text, now_iso())
        )
        await db.commit()
