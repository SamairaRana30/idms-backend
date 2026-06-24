import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from config import Config


def get_db():
    """Return a psycopg2 connection (or local SQLite fallback if unreachable)."""
    url = Config.get_database_url()
    if url:
        try:
            conn = psycopg2.connect(url, connect_timeout=3)
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {Config.get_schema()}")
            conn.commit()
            return conn
        except Exception:
            pass
    # Supabase unreachable — use local SQLite demo database
    from utils.local_db import get_local_db
    return get_local_db()


def close_db(conn, cur=None):
    """Safely close cursor and connection."""
    try:
        if cur:
            cur.close()
        if conn:
            conn.close()
    except Exception:
        pass


_supabase: Client = None

def get_supabase() -> Client:
    """Return a singleton Supabase client for storage and other Supabase operations."""
    global _supabase
    if _supabase is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    return _supabase
