"""
EventBot Database Configuration
===============================
PostgreSQL connection pool & session management.
Singleton pattern untuk efisiensi koneksi.
"""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Load .env dari folder backend (berlaku di semua working directory)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "eventbot"),
    "sslmode": os.getenv("DB_SSLMODE", "prefer"),
}

# Connection pool (singleton)
_connection_pool = None


def get_connection_pool(min_conn=1, max_conn=10):
    """Get or create PostgreSQL connection pool."""
    global _connection_pool

    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                **DB_CONFIG
            )
            print(f"Database pool created: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
        except Exception as e:
            print(f"Failed to create connection pool: {e}")
            raise

    return _connection_pool


@contextmanager
def get_db_connection():
    """Context manager untuk mendapatkan koneksi dari pool."""
    pool = get_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    finally:
        if conn:
            pool.putconn(conn)


@contextmanager
def get_db_cursor(dictionary=True):
    """Context manager untuk mendapatkan cursor.

    Args:
        dictionary: Jika True, return RealDictCursor (hasil dict),
                    jika False, return cursor biasa (hasil tuple).
    """
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dictionary else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def execute_query(sql, params=None, fetch_one=False, fetch_all=False, dictionary=True):
    """Execute SQL query dengan error handling.

    Args:
        sql: SQL query string
        params: Tuple/list parameter untuk parameterized query
        fetch_one: Return 1 row jika True
        fetch_all: Return semua row jika True
        dictionary: Return dict jika True, tuple jika False

    Returns:
        None, dict, atau list of dict tergantung fetch_* flags
    """
    with get_db_cursor(dictionary=dictionary) as cursor:
        cursor.execute(sql, params)

        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            return cursor.rowcount  # Return jumlah row affected


def test_connection():
    """Test database connection."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            print(f"Database connected: {result['version']}")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def close_all_connections():
    """Close all connections in pool. Call saat app shutdown."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        print("All database connections closed")


# ============================================================
# DATABASE HELPER FUNCTIONS (Raw SQL)
# ============================================================

def get_table_count(table_name):
    """Get row count dari sebuah tabel."""
    result = execute_query(
        f"SELECT COUNT(*) as count FROM {table_name}",
        fetch_one=True
    )
    return result['count'] if result else 0


def table_exists(table_name):
    """Cek apakah tabel ada di database."""
    result = execute_query(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = %s
        ) as exists
        """,
        (table_name,),
        fetch_one=True
    )
    return result['exists'] if result else False


def get_enum_values(enum_name):
    """Get semua nilai dari sebuah ENUM type."""
    result = execute_query(
        """
        SELECT enumlabel as value
        FROM pg_enum
        WHERE enumtypid = %s::regtype
        ORDER BY enumsortorder
        """,
        (enum_name,),
        fetch_all=True
    )
    return [row['value'] for row in result] if result else []


# Auto-test saat import
if __name__ == "__main__":
    test_connection()

    # Test basic query
    tables = ['users', 'events', 'tickets', 'categories']
    print("\n📊 Table counts:")
    for table in tables:
        if table_exists(table):
            count = get_table_count(table)
            print(f"   • {table}: {count} rows")
        else:
            print(f"   • {table}: NOT FOUND")

    close_all_connections()