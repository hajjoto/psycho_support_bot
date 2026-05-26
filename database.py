import os
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=1,
            max_size=5
        )

    return _pool


async def init_db():
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMPTZ,
                risk_level TEXT NOT NULL DEFAULT 'UNKNOWN',
                status TEXT NOT NULL DEFAULT 'active'
            );
        """)

        await conn.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
        """)

        await conn.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;
        """)

        await conn.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS risk_level TEXT NOT NULL DEFAULT 'UNKNOWN';
        """)

        await conn.execute("""
            ALTER TABLE sessions
            ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                stage TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        await conn.execute("""
            ALTER TABLE messages
            ADD COLUMN IF NOT EXISTS stage TEXT;
        """)

        await conn.execute("""
            ALTER TABLE messages
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                scale_score TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS protocol_runs (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                protocol_id TEXT NOT NULL,
                protocol_mode TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                result TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id BIGSERIAL PRIMARY KEY,
                session_id TEXT REFERENCES sessions(session_id) ON DELETE SET NULL,
                review_text TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)


async def create_session(session_id: str):
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO sessions (
                session_id,
                risk_level,
                status
            )
            VALUES ($1, 'UNKNOWN', 'active')
            ON CONFLICT (session_id) DO NOTHING;
        """, session_id)


async def update_session_risk(session_id: str, risk_level: str, status: str):
    pool = await get_pool()

    async with pool.acquire() as conn:
        if status in ["finished", "crisis"]:
            await conn.execute("""
                UPDATE sessions
                SET risk_level = $1,
                    status = $2,
                    finished_at = NOW()
                WHERE session_id = $3;
            """, risk_level, status, session_id)
        else:
            await conn.execute("""
                UPDATE sessions
                SET risk_level = $1,
                    status = $2
                WHERE session_id = $3;
            """, risk_level, status, session_id)


async def save_message(
    session_id: str,
    role: str,
    text: str,
    stage: str | None = None
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO messages (
                session_id,
                role,
                text,
                stage
            )
            VALUES ($1, $2, $3, $4);
        """, session_id, role, text, stage)


async def save_assessment(
    session_id: str,
    scale_score: str,
    risk_level: str
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO assessments (
                session_id,
                scale_score,
                risk_level
            )
            VALUES ($1, $2, $3);
        """, session_id, scale_score, risk_level)


async def save_protocol_run(
    session_id: str,
    protocol_id: str,
    protocol_mode: str,
    attempt_number: int,
    result: str | None = None
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO protocol_runs (
                session_id,
                protocol_id,
                protocol_mode,
                attempt_number,
                result
            )
            VALUES ($1, $2, $3, $4, $5);
        """, session_id, protocol_id, protocol_mode, attempt_number, result)


async def save_review(
    session_id: str | None,
    review_text: str
):
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO reviews (
                session_id,
                review_text
            )
            VALUES ($1, $2);
        """, session_id, review_text)


async def close_pool():
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
