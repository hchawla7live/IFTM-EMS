
from pathlib import Path

from database.connection import get_connection


# Locate SQL files
DATABASE_DIR = Path(__file__).resolve().parent

SCHEMA_FILE = DATABASE_DIR / "schema.sql"
SEED_FILE = DATABASE_DIR / "seed.sql"


def initialize_database():
    """
    Create database tables and insert initial master data.
    """

    connection = get_connection()

    try:
        # Read SQL files
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        seed_sql = SEED_FILE.read_text(encoding="utf-8")

        # Execute database schema
        connection.executescript(schema_sql)
        print("Database schema created successfully.")

        # Insert initial master data
        connection.executescript(seed_sql)
        print("Initial master data inserted successfully.")

        # Verify created tables
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        print("\nTables created:")

        for table in tables:
            print(f"- {table[0]}")

        # Count master records
        source_count = connection.execute(
            "SELECT COUNT(*) FROM enquiry_sources"
        ).fetchone()[0]

        programme_count = connection.execute(
            "SELECT COUNT(*) FROM programmes"
        ).fetchone()[0]

        print("\nMaster Data Summary:")
        print(f"Enquiry Sources: {source_count}")
        print(f"Programmes: {programme_count}")

        print("\nIFTM EMS database initialization completed!")

    except Exception:
        print("Database initialization failed.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
