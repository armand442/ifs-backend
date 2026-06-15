import psycopg2
from config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL is not configured")

    return psycopg2.connect(DATABASE_URL)


def init_db():
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                device_id TEXT NOT NULL,
                month TEXT NOT NULL,
                messages_used INTEGER NOT NULL,
                PRIMARY KEY (device_id, month)
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                device_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_logs (
                id SERIAL PRIMARY KEY,

                device_id TEXT NOT NULL,

                model TEXT NOT NULL,

                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,

                input_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,
                output_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,
                total_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,

                success BOOLEAN NOT NULL DEFAULT TRUE,
                error_message TEXT,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """)

        con.commit()