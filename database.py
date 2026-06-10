import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():

    database_url = os.getenv('DEV_DATABASE_URL')

    if not database_url:
        raise Exception(
            "DEV_DATABASE_URL environment variable not set"
        )

    conn = psycopg2.connect(database_url)

    with conn.cursor() as cur:
        cur.execute("SET search_path TO idms_dev")

    return conn