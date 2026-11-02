"""
====================================================================
E-Learning Course Analytics System - Configuration Module
File: config.py
Handles MySQL database connection parameters and establishes safe,
reusable connections without leaking sensitive credentials.
====================================================================
"""

import os
import logging
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, errorcode
from mysql.connector.pooling import MySQLConnectionPool, PoolError

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("config")

# MySQL Database Configuration
# Default to 127.0.0.1 instead of localhost on Windows to eliminate IPv6 DNS resolution latency
_raw_host = os.getenv("DB_HOST", "127.0.0.1")
DB_HOST = "127.0.0.1" if _raw_host.lower() == "localhost" else _raw_host
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "elearning_db")

# Flask Web Server Configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("SECRET_KEY", "elearning-analytics-secret-key-2026")

# Analytics Thresholds
INACTIVITY_DAYS_THRESHOLD = int(os.getenv("INACTIVITY_DAYS_THRESHOLD", 14))

# Persistent Server-Side Theme Configuration
THEME_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "theme_config.json")

# MySQL Connection Pool Configuration
DB_POOL_NAME = "elearning_pool"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 5))
_db_pool = None


def init_connection_pool(pool_name=DB_POOL_NAME, pool_size=DB_POOL_SIZE):
    """
    Initializes a thread-safe MySQLConnectionPool.
    Returns the initialized pool object or None on failure.
    """
    global _db_pool
    try:
        _db_pool = MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=True,
            connect_timeout=4
        )
        logger.info("Initialized MySQLConnectionPool '%s' (size=%d)", pool_name, pool_size)
        return _db_pool
    except Exception as err:
        error_msg = str(err)
        if DB_PASSWORD and DB_PASSWORD in error_msg:
            error_msg = error_msg.replace(DB_PASSWORD, "******")
        logger.error("Failed to initialize MySQLConnectionPool: %s", error_msg)
        _db_pool = None
        return None


def get_connection_pool():
    """Returns the active pool, initializing it if necessary."""
    global _db_pool
    if _db_pool is None:
        init_connection_pool()
    return _db_pool


def get_app_theme():
    """Reads the locked theme setting from server configuration."""
    try:
        if os.path.exists(THEME_CONFIG_FILE):
            with open(THEME_CONFIG_FILE, "r", encoding="utf-8") as f:
                import json
                data = json.load(f)
                return data.get("theme", "light")
    except Exception as e:
        logger.warning("Error reading theme config: %s", e)
    return "light"


def set_app_theme(theme):
    """Saves the chosen theme permanently on the server across all devices."""
    theme_val = "dark" if str(theme).lower() == "dark" else "light"
    try:
        with open(THEME_CONFIG_FILE, "w", encoding="utf-8") as f:
            import json
            json.dump({"theme": theme_val}, f)
        return True, theme_val
    except Exception as e:
        logger.error("Error writing theme config: %s", e)
        return False, str(e)


def get_db_connection():
    """
    Retrieves a connection from the MySQL connection pool.
    If the pool is exhausted or unavailable, cleanly falls back to a direct connection.
    Never exposes passwords or sensitive credentials in logs or exceptions.

    Returns:
        mysql.connector.connection.MySQLConnection / PooledMySQLConnection or None.
    """
    pool = get_connection_pool()
    if pool is not None:
        try:
            return pool.get_connection()
        except PoolError as pe:
            logger.warning("MySQL connection pool temporarily exhausted (%s); attempting direct connection fallback.", pe)
        except Exception as e:
            logger.error("Error retrieving connection from pool: %s", e)

    # Fallback to direct connection if pool is unavailable
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=True,
            connect_timeout=4
        )
        return connection
    except Error as err:
        # Cleanly log error without exposing credentials
        error_msg = str(err)
        if DB_PASSWORD and DB_PASSWORD in error_msg:
            error_msg = error_msg.replace(DB_PASSWORD, "******")
        logger.error("Database connection failure [%s]: %s", getattr(err, 'errno', 'UNKNOWN'), error_msg)
        return None


def ensure_auth_table():
    """
    Ensures the `users` table exists and seeds a default administrator account
    if no users exist yet.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        from werkzeug.security import generate_password_hash
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(30) NOT NULL DEFAULT 'Admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_username (username),
                INDEX idx_user_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        cursor.execute("SELECT COUNT(*) FROM users;")
        row = cursor.fetchone()
        if row and row[0] == 0:
            admin_pw = generate_password_hash("admin123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """, ("admin", "admin@elearning.edu", admin_pw, "Academic Administrator", "Admin"))
            logger.info("Default admin user verified: admin / admin123")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning("Could not auto-verify users table: %s", e)
        if conn and conn.is_connected():
            conn.close()


def ensure_schema_columns():
    """
    Idempotently verifies and adds optional schema extension columns if not already present.
    Ensures time_spent_minutes and credits have NULL as default.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor(dictionary=True)
        columns_to_check = [
            ("learners", "name", "ALTER TABLE `learners` ADD COLUMN `name` VARCHAR(100) NULL DEFAULT NULL AFTER `roll_no`;"),
            ("learners", "email", "ALTER TABLE `learners` ADD COLUMN `email` VARCHAR(100) NULL DEFAULT NULL AFTER `name`;"),
            ("learners", "department", "ALTER TABLE `learners` ADD COLUMN `department` VARCHAR(50) NULL DEFAULT NULL AFTER `email`;"),
            ("activities", "score", "ALTER TABLE `activities` ADD COLUMN `score` DECIMAL(5,2) NULL DEFAULT NULL AFTER `completed`;"),
            ("activities", "time_spent_minutes", "ALTER TABLE `activities` ADD COLUMN `time_spent_minutes` INT NULL DEFAULT NULL AFTER `score`;"),
            ("courses", "description", "ALTER TABLE `courses` ADD COLUMN `description` TEXT NULL DEFAULT NULL AFTER `category`;"),
            ("courses", "credits", "ALTER TABLE `courses` ADD COLUMN `credits` INT NULL DEFAULT NULL AFTER `description`;")
        ]
        for table, col, sql in columns_to_check:
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s;
            """, (DB_NAME, table, col))
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute(sql)
                logger.info("Auto-migrated missing column: %s.%s", table, col)
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning("Could not auto-verify schema columns: %s", e)
        if conn and conn.is_connected():
            conn.close()


def test_connection():
    """
    Verifies connectivity to MySQL and verifies that required tables exist.

    Returns:
        tuple: (success: bool, message: str, details: dict)
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Could not connect to MySQL server. Please check .env credentials and ensure MySQL is running.", {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "user": DB_USER,
            "connected": False,
            "tables_found": []
        }

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() AS current_db, VERSION() AS mysql_version")
        db_info = cursor.fetchone() or {}

        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        required_tables = ["courses", "learners", "enrollments", "activities", "users"]
        schema_ready = all(t in tables for t in required_tables)

        return True, "Connected to MySQL successfully.", {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": db_info.get("current_db", DB_NAME),
            "mysql_version": db_info.get("mysql_version", "Unknown"),
            "user": DB_USER,
            "connected": True,
            "tables_found": tables,
            "schema_ready": schema_ready,
            "connection_pool": {
                "active": _db_pool is not None,
                "pool_name": DB_POOL_NAME,
                "pool_size": DB_POOL_SIZE
            }
        }
    except Error as err:
        error_msg = str(err)
        if DB_PASSWORD and DB_PASSWORD in error_msg:
            error_msg = error_msg.replace(DB_PASSWORD, "******")
        if conn and conn.is_connected():
            conn.close()
        return False, f"Database query error: {error_msg}", {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "connected": False,
            "tables_found": []
        }
