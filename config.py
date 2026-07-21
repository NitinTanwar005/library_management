"""
config.py
---------
Centralized configuration for the Library Management System.

Every other module imports its MySQL connection settings, file
paths, and small app-wide constants from here so there is a single
place to change them (e.g. when deploying on a different machine).
"""

import os
import mysql.connector
from mysql.connector import Error

# ------------------------------------------------------------------
# MySQL connection settings
# ------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Nitin",   # <-- change this
    "database": "library_db",
}

# ------------------------------------------------------------------
# Application paths
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
LOG_FILE = os.path.join(BASE_DIR, "app.log")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# App-wide constants
# ------------------------------------------------------------------
APP_NAME = "Library Management System"
APP_VERSION = "1.0.0"

LOAN_PERIOD_DAYS = 14      # default number of days a book may be borrowed
FINE_PER_DAY = 5.0         # fine charged per day overdue (currency units)


def get_connection():
    """
    Create and return a new MySQL connection using DB_CONFIG.
    Raises mysql.connector.Error if the connection cannot be made;
    callers should catch this and show a messagebox error.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise Error(f"Could not connect to database: {e}")


def test_connection():
    """Quick helper to verify DB connectivity from the command line."""
    try:
        conn = get_connection()
        if conn.is_connected():
            print("Database connection successful.")
            conn.close()
            return True
    except Error as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
