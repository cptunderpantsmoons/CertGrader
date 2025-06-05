"""
Database utility functions for PokéCertify.
Provides connection helpers and initialization logic.
"""

import os
import sqlite3
import logging

DB_PATH = os.getenv("POKECERTIFY_DB_PATH", "pokecertify.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

logger = logging.getLogger("pokecertify.db")

def get_db_connection():
    """Create a new SQLite database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def initialize_database():
    """Initialize the database using the schema.sql file."""
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn = get_db_connection()
        try:
            with conn:
                conn.executescript(schema_sql)
            logger.info("Database initialized successfully.")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_database()