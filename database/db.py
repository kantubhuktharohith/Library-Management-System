"""Database connection and initialization module."""
import sqlite3
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'library.db')
SCHEMA_PATH = os.path.join(DB_DIR, 'schema.sql')


def get_db():
    """Return a new database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database from schema.sql."""
    conn = get_db()
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")


def query_db(query, args=(), one=False, commit=False):
    """Execute a query and return results as list of dicts."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        if commit:
            conn.commit()
            return cur.lastrowid
        rv = cur.fetchall()
        return (dict(rv[0]) if rv else None) if one else [dict(row) for row in rv]
    finally:
        conn.close()


def execute_db(query, args=()):
    """Execute a write query (INSERT/UPDATE/DELETE) and return lastrowid."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    print("Database setup complete.")
