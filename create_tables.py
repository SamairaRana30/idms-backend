"""
Creates all IDMS tables in the current schema (dev or prod).
Usage:
  python create_tables.py              # dev
  ENV=production python create_tables.py  # prod (PowerShell: $env:ENV="production"; python ...)
"""
from dotenv import load_dotenv
load_dotenv()

from utils.supabase_client import get_db, close_db
from config import Config

TABLES = [
    ("users", """
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            full_name     VARCHAR(200),
            email         VARCHAR(200) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role          VARCHAR(20)  NOT NULL DEFAULT 'member',
            is_active     BOOLEAN      NOT NULL DEFAULT true,
            photo_url     TEXT,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ
        )
    """),
    ("ballots", """
        CREATE TABLE IF NOT EXISTS ballots (
            id          SERIAL PRIMARY KEY,
            title       VARCHAR(300) NOT NULL,
            description TEXT,
            status      VARCHAR(20)  NOT NULL DEFAULT 'draft',
            start_date  DATE,
            end_date    DATE,
            created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """),
    ("ballot_options", """
        CREATE TABLE IF NOT EXISTS ballot_options (
            id         SERIAL PRIMARY KEY,
            ballot_id  INTEGER NOT NULL REFERENCES ballots(id) ON DELETE CASCADE,
            text       VARCHAR(300) NOT NULL,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """),
    ("votes", """
        CREATE TABLE IF NOT EXISTS votes (
            id        SERIAL PRIMARY KEY,
            ballot_id INTEGER NOT NULL REFERENCES ballots(id) ON DELETE CASCADE,
            option_id INTEGER NOT NULL REFERENCES ballot_options(id) ON DELETE CASCADE,
            user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (ballot_id, user_id)
        )
    """),
    ("meetings", """
        CREATE TABLE IF NOT EXISTS meetings (
            id           SERIAL PRIMARY KEY,
            title        VARCHAR(300) NOT NULL,
            scheduled_at TIMESTAMPTZ,
            location     TEXT,
            agenda       TEXT,
            minutes      TEXT,
            status       VARCHAR(20)  NOT NULL DEFAULT 'scheduled',
            created_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """),
    ("finance_records", """
        CREATE TABLE IF NOT EXISTS finance_records (
            id               SERIAL PRIMARY KEY,
            type             VARCHAR(10) NOT NULL CHECK (type IN ('income','expense')),
            amount           NUMERIC(12,2) NOT NULL,
            description      TEXT,
            category         VARCHAR(100),
            transaction_date DATE,
            recorded_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("notifications", """
        CREATE TABLE IF NOT EXISTS notifications (
            id          SERIAL PRIMARY KEY,
            type        VARCHAR(30) NOT NULL DEFAULT 'announcement',
            title       VARCHAR(300) NOT NULL,
            body        TEXT NOT NULL,
            sent_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
            target_role VARCHAR(20) NOT NULL DEFAULT 'all',
            sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("chat_channels", """
        CREATE TABLE IF NOT EXISTS chat_channels (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(80) NOT NULL UNIQUE,
            description TEXT,
            created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """),
    ("chat_messages", """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id          SERIAL PRIMARY KEY,
            channel_id  INTEGER NOT NULL REFERENCES chat_channels(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content     TEXT    NOT NULL,
            reply_to_id INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """),
    ("documents", """
        CREATE TABLE IF NOT EXISTS documents (
            id                SERIAL PRIMARY KEY,
            title             VARCHAR(300) NOT NULL,
            file_path         TEXT NOT NULL,
            file_type         VARCHAR(20),
            category          VARCHAR(100),
            is_public         BOOLEAN NOT NULL DEFAULT false,
            uploaded_by       INTEGER REFERENCES users(id) ON DELETE SET NULL,
            download_count    INTEGER NOT NULL DEFAULT 0,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("audit_log", """
        CREATE TABLE IF NOT EXISTS audit_log (
            id          SERIAL PRIMARY KEY,
            action      VARCHAR(100),
            entity_type VARCHAR(100),
            entity_id   VARCHAR(100),
            user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
            metadata    JSONB,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("chat_analytics", """
        CREATE TABLE IF NOT EXISTS chat_analytics (
            id                    SERIAL PRIMARY KEY,
            upload_date           DATE,
            total_messages        INTEGER,
            active_users          INTEGER,
            peak_hour             INTEGER,
            sentiment_score       NUMERIC(6,4),
            text_count            INTEGER,
            media_count           INTEGER,
            uploaded_by           INTEGER REFERENCES users(id) ON DELETE SET NULL,
            hourly_data           JSONB,
            top_senders           JSONB,
            daily_data            JSONB,
            spam_count            INTEGER DEFAULT 0,
            spam_messages         JSONB,
            emotional_highlights  JSONB,
            influential_members   JSONB,
            interaction_clusters  JSONB,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
]

def create_tables():
    conn = cur = None
    schema = Config.get_schema()
    print(f"Creating tables in schema: {schema}")
    try:
        conn = get_db()
        cur  = conn.cursor()
        for name, sql in TABLES:
            cur.execute(sql)
            print(f"  OK  {name}")
        conn.commit()
        print(f"\nAll tables ready in {schema}.")
    except Exception as e:
        print(f"ERROR: {e}")
        if conn: conn.rollback()
    finally:
        close_db(conn, cur)

if __name__ == "__main__":
    create_tables()
