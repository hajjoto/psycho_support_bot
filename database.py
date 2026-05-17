import asyncpg

from config import DATABASE_URL


pool = None


async def init_db():
    global pool

    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            session_id TEXT UNIQUE NOT NULL,
            risk_level TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            stage TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP      
        );
        """)                   

async def create_session(session_id: str):
    async with pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO sessions (session_id, status)
        VALUES ($1, $2)
        ON CONFLICT (session_id) DO NOTHING;
        """, session_id, "started")


async def save_message(session_id: str, role: str, text: str, stage: str = "unknown"):
    async with pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO messages (session_id, role, text, stage)
        VALUES ($1, $2, $3, $4);
        """, session_id, role, text, stage)


async def update_session_risk(session_id: str, risk_level: str, status: str):
    async with pool.acquire() as conn:
        await conn.execute("""
        UPDATE sessions
        SET risk_level = $1,
            status = $2,
            updated_at = CURRENT_TIMESTAMP
        WHERE session_id = $3;
        """, risk_level, status, session_id)
