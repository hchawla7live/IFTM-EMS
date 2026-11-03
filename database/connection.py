
from pathlib import Path
import sqlite3


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory and file
DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "ems.db"


def get_connection():
    """
    Create and return a connection to the EMS SQLite database.
    """

    # Ensure database directory exists
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # Establish database connection
    connection = sqlite3.connect(DATABASE_PATH)

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    # Return database connection
    return connection


def check_connection():
    """
    Check whether the database connection is working.
    """

    connection = get_connection()

    try:
        result = connection.execute("SELECT 1").fetchone()
        return result == (1,)

    finally:
        connection.close()
