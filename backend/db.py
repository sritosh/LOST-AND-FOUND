"""
Campus Lost & Found System - Database Connection & Helper Module
Supports SQLite out-of-the-box with auto-initialization and MySQL compatibility.
"""

import os
import sqlite3
import datetime
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')
SAMPLE_DATA_PATH = os.path.join(BASE_DIR, 'database', 'sample_data.sql')
SOURCE_DB_PATH = os.path.join(BASE_DIR, 'database', 'campus_lost_found.db')

# In Vercel serverless environment, use /tmp for write access
if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or (os.name != 'nt' and not os.access(BASE_DIR, os.W_OK)):
    DB_PATH = '/tmp/campus_lost_found.db'
else:
    DB_PATH = SOURCE_DB_PATH


def get_db_connection():
    """Returns a SQLite database connection with row factory configured."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable Foreign Key enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force_reinit=False):
    """Initializes the database schema and sample data if not already created."""
    db_exists = os.path.exists(DB_PATH)
    if not db_exists or force_reinit:
        # If in /tmp and pre-seeded database exists in repo, copy it for instant start
        if DB_PATH != SOURCE_DB_PATH and os.path.exists(SOURCE_DB_PATH) and not force_reinit:
            try:
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                shutil.copyfile(SOURCE_DB_PATH, DB_PATH)
                return True
            except Exception:
                pass

        if os.path.exists(DB_PATH) and force_reinit:
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

        conn = get_db_connection()
        cursor = conn.cursor()

        # Read and run schema
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                cursor.executescript(schema_sql)

        # Read and run sample data
        if os.path.exists(SAMPLE_DATA_PATH):
            with open(SAMPLE_DATA_PATH, 'r', encoding='utf-8') as f:
                sample_sql = f.read()
                cursor.executescript(sample_sql)

        conn.commit()
        conn.close()
        return True
    return False


def query_all(query, params=()):
    """Executes a SELECT query and returns a list of dictionaries."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_one(query, params=()):
    """Executes a SELECT query and returns a single dictionary row or None."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute_write(query, params=()):
    """Executes an INSERT, UPDATE, or DELETE query and returns lastrowid and rowcount."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid, cursor.rowcount
    finally:
        conn.close()


def execute_raw_user_query(sql_statement):
    """
    Executes a user-supplied SQL statement for the Live SQL Query Lab.
    Returns column names, rows, execution time, and affected rows count.
    """
    import time
    start_time = time.time()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_statement)
        
        # Check if query returned rows (e.g. SELECT)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            rows = [list(r) for r in raw_rows]
            row_count = len(rows)
            is_select = True
        else:
            conn.commit()
            columns = []
            rows = []
            row_count = cursor.rowcount
            is_select = False
            
        exec_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "is_select": is_select,
            "execution_time_ms": exec_time_ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()
