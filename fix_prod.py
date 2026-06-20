from dotenv import load_dotenv
load_dotenv()
from utils.supabase_client import get_db, close_db

conn = get_db()
cur  = conn.cursor()

fixes = [
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title VARCHAR(300)",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS body TEXT",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS type VARCHAR(30) DEFAULT 'announcement'",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sent_by INTEGER REFERENCES users(id) ON DELETE SET NULL",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS target_role VARCHAR(20) DEFAULT 'all'",
    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ DEFAULT NOW()",
]

for sql in fixes:
    try:
        cur.execute(sql)
        conn.commit()
        print("OK:", sql[:70])
    except Exception as e:
        conn.rollback()
        print("SKIP:", str(e)[:80])

close_db(conn, cur)
print("Done")
