"""
Seed Data Script
================
Script terpisah untuk insert seed data (jika init_db sudah jalan tapi data belum ada).
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import execute_query, test_connection


def seed_all():
    """Insert semua seed data."""
    print("🌱 Seeding data...")

    # Path ke seed_data.sql
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    seed_file = os.path.join(base_dir, "database", "seed_data.sql")

    if not os.path.exists(seed_file):
        print(f"❌ File tidak ditemukan: {seed_file}")
        return False

    with open(seed_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        # Execute per statement untuk better error handling
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in statements:
            if stmt and not stmt.startswith("--"):
                try:
                    execute_query(stmt + ";")
                except Exception as e:
                    print(f"   ⚠️  Skip: {str(e)[:80]}")

        print("✅ Seed data inserted!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if test_connection():
        seed_all()
    else:
        print("❌ Database tidak terhubung")