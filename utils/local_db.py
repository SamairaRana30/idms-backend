"""
Local SQLite fallback database — mirrors psycopg2 interface so all blueprints
work unchanged. Used automatically when Supabase is unreachable.
"""
import re
import sqlite3

DB_PATH = 'local_demo.db'

# PostgreSQL → SQLite SQL translations
_TRANSLATIONS = [
    (re.compile(r'%s'),                              '?'),
    (re.compile(r'%%'),                              '%'),
    (re.compile(r'\bILIKE\b',          re.I),       'LIKE'),
    (re.compile(r'\bNOW\(\)',           re.I),       "datetime('now')"),
    (re.compile(r'\bCURRENT_TIMESTAMP\b', re.I),    "datetime('now')"),
    (re.compile(r'\btrue\b',            re.I),       '1'),
    (re.compile(r'\bfalse\b',           re.I),       '0'),
    (re.compile(r'::\w+'),                           ''),   # strip PG casts
    (re.compile(r'SET search_path TO \w+', re.I),   'SELECT 1'),
    # DATE_TRUNC('month', col) → strftime('%Y-%m-01', col)
    (re.compile(r"DATE_TRUNC\('month',\s*([^)]+)\)", re.I),
     r"strftime('%Y-%m-01', \1)"),
    # TO_CHAR(x, 'YYYY-MM') → strftime('%Y-%m', x)
    (re.compile(r"TO_CHAR\(([^,]+),\s*'YYYY-MM'\)", re.I),
     r"strftime('%Y-%m', \1)"),
    # COALESCE(x::timestamp, y) — strip casts handled above
]

def _translate(sql):
    for pat, repl in _TRANSLATIONS:
        sql = pat.sub(repl, sql)
    return sql


class LocalCursor:
    def __init__(self, cur, dict_mode=False):
        self._c        = cur
        self._dict     = dict_mode

    def execute(self, sql, params=None):
        sql = _translate(sql)
        try:
            if params is not None:
                self._c.execute(sql, list(params))
            else:
                self._c.execute(sql)
        except Exception:
            raise

    def executemany(self, sql, seq):
        self._c.executemany(_translate(sql), seq)

    def fetchone(self):
        row = self._c.fetchone()
        if row is None:
            return None
        if self._dict and self._c.description:
            return dict(zip([d[0] for d in self._c.description], row))
        return row

    def fetchall(self):
        rows = self._c.fetchall()
        if not self._dict or not self._c.description:
            return rows
        cols = [d[0] for d in self._c.description]
        return [dict(zip(cols, r)) for r in rows]

    @property
    def rowcount(self):  return self._c.rowcount
    @property
    def lastrowid(self): return self._c.lastrowid

    def close(self):
        try: self._c.close()
        except: pass

    def __enter__(self):  return self
    def __exit__(self, *_): self.close()


class LocalConn:
    def __init__(self):
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def cursor(self, cursor_factory=None):
        return LocalCursor(self._conn.cursor(), dict_mode=(cursor_factory is not None))

    def commit(self):   self._conn.commit()
    def rollback(self): self._conn.rollback()

    def close(self):
        try: self._conn.close()
        except: pass

    def __enter__(self):  return self
    def __exit__(self, *_): self.close()


def get_local_db():
    return LocalConn()
