import os
import sqlite3


# --------------------------------------------------
# DB_PATH — configurable via environment variable.
#
# Local dev    : defaults to "sales.db" (project root)
# Railway      : set DB_PATH=/data/sales.db in dashboard
#                after mounting a Railway Volume at /data
# --------------------------------------------------

DB_PATH = os.getenv("DB_PATH", "sales.db")


def create_database():

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    # Create table if it doesn't exist yet
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_email TEXT,
        customer_need TEXT,
        budget TEXT,
        urgency TEXT,
        callback_required TEXT,
        lead_status TEXT
    )
    """)

    # Add customer_email column if upgrading from old DB (safe to run multiple times)
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN customer_email TEXT")
        print("Added customer_email column to existing database.")
    except Exception:
        pass  # Column already exists — that's fine

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print(f"Database ready at: {DB_PATH}")