import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config


def get_db():
    """Return a connection with the correct schema set."""
    url = Config.get_database_url()
    if not url:
        raise RuntimeError("Database URL not configured for environment: " + Config.ENV)
    conn = psycopg2.connect(url)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {Config.get_schema()}")
    conn.commit()
    return conn


def close_db(conn, cur=None):
    """Safely close cursor and connection."""
    try:
        if cur:
            cur.close()
        if conn:
            conn.close()
    except Exception:
        pass
