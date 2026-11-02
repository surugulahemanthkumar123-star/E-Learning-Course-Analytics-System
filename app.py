"""
====================================================================
E-Learning Course Analytics System - Main Application
File: app.py
Flask Web Application & REST API
Manages routing, CRUD operations, analytics API, and CSV reporting.
====================================================================
"""

import os
import io
import csv
import json
import re
import threading
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, Response,
    send_from_directory, session, redirect, url_for, flash
)
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error, errorcode

import config
import analytics
import reports_pdf

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["JSON_SORT_KEYS"] = False

# Hardened Session Security & Cookie Configuration
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=int(os.getenv("PERMANENT_SESSION_LIFETIME_HOURS", 8)))

# Initialize Flask-WTF CSRF Protection
csrf = CSRFProtect(app)

# Setup logger
logger = logging.getLogger("app")

# Auto-verify users table and schema columns on startup
try:
    config.ensure_auth_table()
    config.ensure_schema_columns()
except Exception as _e:
    logger.warning("Could not auto-verify schema on startup: %s", _e)


# Context processor injects the permanently locked theme, CSRF token & active user into all rendered templates
@app.context_processor
def inject_global_settings():
    user_id = session.get("user_id")
    return {
        "active_theme": config.get_app_theme(),
        "csrf_token": generate_csrf,
        "current_user": {
            "id": user_id,
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "email": session.get("email"),
            "role": session.get("role", "Admin"),
            "is_authenticated": bool(user_id)
        }
    }


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """
    Structured CSRF failure handler.
    Returns JSON 400 for API/AJAX requests, or redirects with warning for HTML forms.
    """
    desc = getattr(e, "description", "CSRF token validation failed")
    logger.warning("CSRF validation failure on %s %s: %s", request.method, request.path, desc)
    if request.path.startswith("/api/") or request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": False,
            "error": f"CSRF validation failed: {desc}."
        }), 400
    flash("Session security validation failed or token expired. Please try submitting again.", "danger")
    return redirect(request.referrer or url_for("page_home"))


@app.before_request
def check_authentication():
    """Ensure user is logged in before accessing protected pages or APIs."""
    # Allow static assets and favicon
    if request.path.startswith("/static/") or request.path == "/favicon.ico":
        return None

    # Public routes allowed without authentication
    public_paths = [
        "/login",
        "/register",
        "/logout",
        "/api/health",
        "/api/settings/theme",
        "/api/csrf-token"
    ]
    if request.path in public_paths:
        return None

    # If user not authenticated
    if "user_id" not in session:
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "message": "Authentication required. Please sign in."
            }), 401
        return redirect(url_for("page_login", next=request.path))
    return None


def login_required(f):
    """
    Decorator ensuring user has an active session before accessing a protected route.
    Redirects HTML page requests to /login and returns 401 for protected API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                if request.path in ["/api/health", "/api/settings/theme", "/api/csrf-token"]:
                    return f(*args, **kwargs)
                return jsonify({
                    "success": False,
                    "message": "Authentication required. Please sign in."
                }), 401
            return redirect(url_for("page_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator enforcing Role-Based Access Control (RBAC) on backend routes and APIs.
    Canonicalizes role names and rejects unauthorized roles with HTTP 403 Forbidden.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "message": "Authentication required. Please sign in."}), 401
                return redirect(url_for("page_login", next=request.path))

            user_role = session.get("role", "")
            canonical_map = {
                "admin": "Admin",
                "administrator": "Admin",
                "academic analyst": "Academic Analyst",
                "analyst": "Academic Analyst",
                "instructor": "Instructor",
                "faculty": "Instructor"
            }
            norm_user = canonical_map.get(user_role.lower(), user_role)
            norm_allowed = [canonical_map.get(r.lower(), r) for r in allowed_roles]

            if norm_user not in norm_allowed:
                logger.warning(
                    "RBAC Denied: User '%s' (role: '%s') attempted restricted action on %s %s",
                    session.get("username"), user_role, request.method, request.path
                )
                if request.path.startswith("/api/"):
                    return jsonify({
                        "success": False,
                        "error": f"Access denied: Insufficient privileges for '{user_role}' role."
                    }), 403
                flash(f"Access denied: Your account role ({user_role}) does not have permission to access that resource.", "warning")
                return redirect(url_for("page_home"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Endpoint providing CSRF tokens to AJAX / API clients
@app.route("/api/csrf-token", methods=["GET"])
def api_get_csrf_token():
    """Returns a valid CSRF token for programmatic clients or test harnesses."""
    return jsonify({"success": True, "csrf_token": generate_csrf()})


# ====================================================================
# Date Validation & User Preferences Utilities (Phase 6)
# ====================================================================

def parse_iso_date(date_str, field_name="date"):
    """
    Validates that date_str is a valid ISO date in YYYY-MM-DD format.
    Returns datetime.date or raises ValueError with a user-friendly message.
    """
    if not date_str:
        return None
    cleaned = str(date_str).strip()
    if not cleaned:
        return None
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid {field_name} format: '{cleaned}'. Expected YYYY-MM-DD.")


def validate_date_range(start_date_str, end_date_str):
    """
    Validates optional start_date and end_date query parameters.
    Returns (start_str, end_str, error_message).
    If valid, start_str and end_str are clean 'YYYY-MM-DD' strings (or None).
    If invalid, error_message contains a description suitable for HTTP 400.
    """
    try:
        start_d = parse_iso_date(start_date_str, "start_date")
    except ValueError as e:
        return None, None, str(e)

    try:
        end_d = parse_iso_date(end_date_str, "end_date")
    except ValueError as e:
        return None, None, str(e)

    if start_d and end_d and start_d > end_d:
        return None, None, f"start_date ({start_d}) cannot be after end_date ({end_d})."

    start_str = start_d.strftime("%Y-%m-%d") if start_d else None
    end_str = end_d.strftime("%Y-%m-%d") if end_d else None
    return start_str, end_str, None


USER_PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), "user_preferences.json")
_prefs_lock = threading.Lock()

def get_user_preferences(user_id):
    """
    Retrieves user-specific preferences (theme, page_size, date_preset).
    Guarantees complete isolation between users without leaking data.
    """
    default_prefs = {"theme": config.get_app_theme(), "page_size": 25, "date_preset": "all_time"}
    if not user_id:
        return default_prefs

    with _prefs_lock:
        if os.path.exists(USER_PREFERENCES_FILE):
            try:
                with open(USER_PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    all_prefs = json.load(f)
                    return all_prefs.get(str(user_id), default_prefs)
            except Exception as e:
                logger.warning("Could not read user_preferences.json: %s", e)
    return default_prefs


def save_user_preferences(user_id, prefs):
    """Saves user-specific preferences atomically and thread-safely."""
    if not user_id:
        return False

    with _prefs_lock:
        all_prefs = {}
        if os.path.exists(USER_PREFERENCES_FILE):
            try:
                with open(USER_PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    all_prefs = json.load(f)
            except Exception:
                all_prefs = {}

        current = all_prefs.get(str(user_id), {"theme": "light", "page_size": 25, "date_preset": "all_time"})
        current.update(prefs)
        all_prefs[str(user_id)] = current

        tmp_file = USER_PREFERENCES_FILE + ".tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(all_prefs, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, USER_PREFERENCES_FILE)
            return True
        except Exception as e:
            logger.error("Could not write user_preferences.json atomically: %s", e)
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass
            return False


@app.route("/api/user/preferences", methods=["GET", "PUT"])
@login_required
def api_user_preferences():
    """
    Get or update user-specific preferences (theme, pagination page_size, date_preset).
    Strictly isolated per logged-in user to prevent cross-account leakage.
    """
    user_id = session.get("user_id")
    if request.method == "GET":
        prefs = get_user_preferences(user_id)
        return jsonify({"success": True, "data": prefs})

    payload = request.get_json(silent=True) or {}
    updated = {}
    if "theme" in payload and payload["theme"] in ("light", "dark"):
        updated["theme"] = payload["theme"]
    if "page_size" in payload:
        try:
            ps = int(payload["page_size"])
            if ps in (10, 25, 50, 100):
                updated["page_size"] = ps
        except ValueError:
            pass
    if "date_preset" in payload and payload["date_preset"] in ("all_time", "today", "last_7", "last_30", "this_quarter", "custom"):
        updated["date_preset"] = payload["date_preset"]

    success = save_user_preferences(user_id, updated)
    return jsonify({"success": success, "data": get_user_preferences(user_id)})


# API endpoint to persist theme server-wide across all devices (exempt from CSRF for universal access)
@app.route("/api/settings/theme", methods=["GET", "POST"])
@csrf.exempt
def api_theme_settings():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        theme = body.get("theme", "light")
        success, saved = config.set_app_theme(theme)
        return jsonify({"success": success, "theme": saved})
    return jsonify({"success": True, "theme": config.get_app_theme()})


# ====================================================================
# Authentication Routes (Login, Registration, Logout)
# ====================================================================

@app.route("/login", methods=["GET", "POST"])
def page_login():
    """Render login screen and process user authentication."""
    if "user_id" in session:
        return redirect(url_for("page_home"))

    next_url = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        username_or_email = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        if not username_or_email or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("login.html", next_url=next_url)

        conn = config.get_db_connection()
        if not conn:
            flash("Database connection failure. Please verify MySQL service is running.", "danger")
            return render_template("login.html", next_url=next_url)

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT user_id, username, email, password_hash, full_name, role
                FROM users
                WHERE username = %s OR email = %s
                LIMIT 1;
            """, (username_or_email, username_or_email))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session.permanent = remember
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                session["email"] = user["email"]
                session["role"] = user.get("role", "Administrator")
                flash(f"Welcome back, {user['full_name']}!", "success")

                # Validate safe redirection target - default to Home page upon login
                if next_url and next_url.startswith("/") and not next_url.startswith("//") and next_url not in ["/login", "/register", "/logout", "/dashboard"]:
                    return redirect(next_url)
                return redirect(url_for("page_home"))
            else:
                flash("Invalid username/email or password. Please try again.", "danger")
                return render_template("login.html", next_url=next_url)

        except Exception as e:
            logger.error("Authentication error: %s", e)
            if conn and conn.is_connected():
                conn.close()
            flash("An error occurred during authentication. Please try again.", "danger")
            return render_template("login.html", next_url=next_url)

    return render_template("login.html", next_url=next_url)


@app.route("/register", methods=["GET", "POST"])
def page_register():
    """Render registration screen and create new administrator/analyst accounts."""
    if "user_id" in session:
        return redirect(url_for("page_home"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        username = (request.form.get("username") or "").strip().lower()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "Admin").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        # Basic validations
        if not full_name or not username or not email or not password:
            flash("All fields marked with an asterisk (*) are required.", "danger")
            return render_template("register.html")

        if len(username) < 3 or len(username) > 30 or not re.match(r"^[a-zA-Z0-9_]+$", username):
            flash("Username must be between 3 and 30 alphanumeric characters or underscores.", "danger")
            return render_template("register.html")

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            flash("Please enter a valid institutional email address.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match. Please verify your passwords.", "danger")
            return render_template("register.html")

        conn = config.get_db_connection()
        if not conn:
            flash("Database connection error. Please verify MySQL service is running.", "danger")
            return render_template("register.html")

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM users WHERE username = %s LIMIT 1;", (username,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                flash("That username is already taken. Please choose another.", "warning")
                return render_template("register.html")

            cursor.execute("SELECT user_id FROM users WHERE email = %s LIMIT 1;", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                flash("An account with that email address already exists. Please sign in.", "warning")
                return render_template("register.html")

            p_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s);
            """, (username, email, p_hash, full_name, role))
            cursor.close()
            conn.close()

            flash("Account registered successfully! You can now sign in with your credentials.", "success")
            return redirect(url_for("page_login"))

        except Exception as e:
            logger.error("Registration error: %s", e)
            if conn and conn.is_connected():
                conn.close()
            flash("An error occurred during registration. Please try again.", "danger")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/logout")
def page_logout():
    """Sign the user out, clear session credentials, and redirect to login."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("page_login"))


# ====================================================================
# HTML Page Routes (Protected by @login_required)
# ====================================================================

@app.route("/")
@app.route("/home")
@login_required
def page_home():
    """Render central platform home page with system overview and module navigation."""
    summary = analytics.get_dashboard_summary()

    # Fetch recent learning activity and popular course highlights for the home page feed
    recent_activities = []
    top_courses = []
    conn = config.get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.activity_id, a.activity_type, a.completed, a.activity_date,
                    l.roll_no, c.course_name
                FROM activities a
                JOIN enrollments e ON a.enrollment_id = e.enrollment_id
                JOIN learners l ON e.learner_id = l.learner_id
                JOIN courses c ON e.course_id = c.course_id
                ORDER BY a.activity_date DESC, a.activity_id DESC
                LIMIT 5;
            """)
            recent_activities = cursor.fetchall()

            cursor.execute("""
                SELECT c.course_id, c.course_name, c.category,COUNT(e.enrollment_id) AS total_enrolled, SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count
                FROM courses c
                LEFT JOIN enrollments e ON c.course_id = e.course_id
                GROUP BY c.course_id, c.course_name, c.category
                ORDER BY total_enrolled DESC
                LIMIT 4;
            """)
            top_courses = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as err:
            logger.error("Error fetching home page highlights: %s", err)
            if conn and conn.is_connected():
                conn.close()

    return render_template(
        "home.html",
        page_title="Home",
        summary=summary,
        recent_activities=recent_activities,
        top_courses=top_courses
    )


@app.route("/dashboard")
@login_required
def page_dashboard():
    """Render main analytics dashboard with live charts, KPI cards, and inactive student detection."""
    return render_template("index.html", page_title="Analytics Dashboard")


@app.route("/courses")
@login_required
def page_courses():
    """Render course management page."""
    return render_template("courses.html", page_title="Manage Courses")


@app.route("/learners")
@login_required
def page_learners():
    """Render learner management page."""
    return render_template("learners.html", page_title="Manage Learners")


@app.route("/enrollments")
@login_required
def page_enrollments():
    """Render enrollment management page."""
    return render_template("enrollments.html", page_title="Manage Enrollments")


@app.route("/activities")
@login_required
def page_activities():
    """Render learning activity tracker page."""
    return render_template("activities.html", page_title="Learning Activity")


@app.route("/reports")
@login_required
def page_reports():
    """Render analytics reports and export page."""
    return render_template("reports.html", page_title="Analytics Reports")


@app.route("/settings")
@login_required
def page_settings():
    """Render settings and database health status page."""
    return render_template("settings.html", page_title="Database & Settings")


@app.route("/profile")
@login_required
def page_profile():
    """Render personal profile and security management view."""
    user_id = session.get("user_id")
    conn = config.get_db_connection()
    user_data = {
        "user_id": user_id,
        "username": session.get("username", ""),
        "full_name": session.get("full_name", ""),
        "email": session.get("email", ""),
        "role": session.get("role", "Admin"),
        "created_at": None
    }
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username, email, full_name, role, created_at FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                user_data = row
        except Exception as e:
            logger.error("Error retrieving user profile for view: %s", e)
            if conn and conn.is_connected():
                conn.close()
    return render_template("profile.html", page_title="My Profile & Security", user=user_data)


# ====================================================================
# Self-Service Profile and Security APIs
# ====================================================================

@app.route("/api/profile", methods=["GET"])
@login_required
def api_get_profile():
    """
    Returns personal profile data for the currently authenticated user.
    Never exposes other users' private account information or password hashes.
    """
    user_id = session.get("user_id")
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, username, email, full_name, role, created_at FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "message": "User not found."}), 404

        if user.get("created_at"):
            user["created_at"] = user["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "data": user})
    except Error as e:
        logger.error("Error fetching personal profile: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve profile."}), 500


@app.route("/api/profile", methods=["PUT"])
@login_required
def api_update_profile():
    """
    Self-service endpoint to update permitted profile information (full_name and email).
    Users cannot elevate or change their own role or privileges through this endpoint.
    """
    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}
    full_name = (payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()

    if not full_name:
        return jsonify({"success": False, "message": "Full Name cannot be empty."}), 400
    if len(full_name) > 100:
        return jsonify({"success": False, "message": "Full Name must not exceed 100 characters."}), 400

    if not email:
        return jsonify({"success": False, "message": "Email cannot be empty."}), 400
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"success": False, "message": "Please enter a valid email address format."}), 400
    if len(email) > 100:
        return jsonify({"success": False, "message": "Email must not exceed 100 characters."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Verify email is not in use by another user
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "That email address is already in use by another account."}), 409

        # Safely update ONLY full_name and email (role is strictly protected)
        cursor.execute("""
            UPDATE users
            SET full_name = %s, email = %s
            WHERE user_id = %s
        """, (full_name, email, user_id))
        cursor.close()
        conn.close()

        # Synchronize active session credentials
        session["full_name"] = full_name
        session["email"] = email

        logger.info("User profile updated for user_id=%s (%s)", user_id, session.get("username"))
        return jsonify({
            "success": True,
            "message": "Profile updated successfully.",
            "data": {"user_id": user_id, "full_name": full_name, "email": email}
        })
    except Error as e:
        logger.error("Error updating profile: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update profile."}), 500


@app.route("/api/profile/password", methods=["PUT"])
@login_required
def api_change_password():
    """
    Secure password modification endpoint.
    Verifies current password, enforces length & alphanumeric complexity,
    prevents password reuse, and updates password hash.
    """
    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password") or ""
    new_password = payload.get("new_password") or ""
    confirm_password = payload.get("confirm_password") or ""

    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "Current password, new password, and confirmation are all required."}), 400

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "New password and confirmation do not match."}), 400

    if len(new_password) < 8:
        return jsonify({"success": False, "message": "New password must be at least 8 characters long."}), 400

    if not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
        return jsonify({"success": False, "message": "New password must contain both letters and numbers."}), 400

    if current_password == new_password:
        return jsonify({"success": False, "message": "New password cannot be the same as your current password."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User account not found."}), 404

        if not check_password_hash(user["password_hash"], current_password):
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Current password is incorrect. Please check and try again."}), 400

        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id))
        cursor.close()
        conn.close()

        logger.info("Password successfully changed for user_id=%s (%s)", user_id, session.get("username"))
        return jsonify({"success": True, "message": "Password updated successfully."})
    except Error as e:
        logger.error("Error changing password: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update password."}), 500


# ====================================================================
# Health and Diagnostics API
# ====================================================================

@app.route("/api/health", methods=["GET"])
def api_health():
    """
    Health check endpoint returning application and database connectivity status.
    Guarantees no sensitive credentials or passwords are leaked.
    """
    is_connected, message, details = config.test_connection()
    status_code = 200 if is_connected else 503

    return jsonify({
        "status": "healthy" if is_connected else "degraded",
        "app": "E-Learning Course Analytics System",
        "timestamp": datetime.now().isoformat(),
        "database": details,
        "message": message
    }), status_code


# ====================================================================
# Dashboard and Analytics APIs
# ====================================================================

@app.route("/api/dashboard/summary", methods=["GET"])
def api_dashboard_summary():
    """Returns top summary metrics for dashboard cards with optional course & date filtering."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_dashboard_summary(course_id=course_id, start_date=start_d, end_date=end_d)
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/course-completion", methods=["GET"])
def api_analytics_course_completion():
    """Returns per-course completion statistics for bar charts with optional course_id filter."""
    course_id = request.args.get("course_id", type=int)
    data = analytics.get_course_completion_analytics(course_id=course_id)
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/weekly-activity", methods=["GET"])
def api_analytics_weekly_activity():
    """Returns weekly aggregated learning activity counts with strict date validation."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_weekly_activity_analytics(start_date=start_d, end_date=end_d)
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/inactive-enrollments", methods=["GET"])
def api_analytics_inactive_enrollments():
    """
    Returns enrollments with no activity or with activity older than threshold days.
    """
    threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
    data = analytics.get_inactive_enrollments(threshold_days=threshold)
    return jsonify({"success": True, "data": data, "threshold_days": threshold})


@app.route("/api/analytics/course-comparison", methods=["GET"])
def api_analytics_course_comparison():
    """Returns comparative performance metrics for courses."""
    data = analytics.get_course_comparison()
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/learner-performance", methods=["GET"])
@login_required
def api_analytics_learner_performance():
    """Returns individual learner performance telemetry."""
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    data = analytics.get_learner_performance_analytics(search=search or None, department=department or None)
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/activity-participation", methods=["GET"])
@login_required
def api_analytics_activity_participation():
    """Returns activity participation breakdown by activity_type with strict date validation."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_activity_participation_analytics(
        course_id=course_id,
        start_date=start_d,
        end_date=end_d
    )
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/score-time-trends", methods=["GET"])
@login_required
def api_analytics_score_time_trends():
    """Returns score and learning time trends telemetry with strict date validation."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_score_and_time_trends(course_id=course_id, start_date=start_d, end_date=end_d)
    trends = data.get("trends", [])
    data["score_trends"] = [{"date": t["date"], "average_score": t["average_score"]} for t in trends if t.get("average_score") is not None]
    data["time_trends"] = [{"date": t["date"], "average_time": t.get("total_time_minutes")} for t in trends if t.get("total_time_minutes") is not None]
    return jsonify({"success": True, "data": data})


# ====================================================================
# Course Management APIs
# ====================================================================

@app.route("/api/courses", methods=["GET"])
def api_get_courses():
    """Lists courses with optional search, category filter, enrollment counts and completion rates."""
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if search:
            where_clauses.append("(c.course_name LIKE %s OR c.category LIKE %s OR c.description LIKE %s)")
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        if category:
            where_clauses.append("c.category = %s")
            params.append(category)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                c.course_id,
                c.course_name,
                c.category,
                c.description,
                c.credits,
                c.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrollment_count,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            {where_sql}
            GROUP BY c.course_id, c.course_name, c.category, c.description, c.credits, c.created_at
            ORDER BY c.course_id DESC;
        """
        cursor.execute(query, tuple(params))
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format rows and compute live completion percentage
        for c in courses:
            total = int(c.get("enrollment_count") or 0)
            comp = int(c.get("completed_count") or 0)
            c["completion_rate"] = round((comp / total) * 100.0, 1) if total > 0 else 0.0
            if c.get("created_at"):
                c["created_at"] = c["created_at"].strftime("%Y-%m-%d")

        return jsonify({"success": True, "data": courses})
    except Error as e:
        logger.error("Error fetching courses: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve courses."}), 500


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def api_get_course_detail(course_id):
    """Retrieve details and statistics for a single course."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                c.course_id,
                c.course_name,
                c.category,
                c.description,
                c.credits,
                c.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrollment_count,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            WHERE c.course_id = %s
            GROUP BY c.course_id, c.course_name, c.category, c.description, c.credits, c.created_at;
        """
        cursor.execute(query, (course_id,))
        course = cursor.fetchone()
        cursor.close()
        conn.close()

        if not course:
            return jsonify({"success": False, "message": "Course not found."}), 404

        total = int(course.get("enrollment_count") or 0)
        comp = int(course.get("completed_count") or 0)
        course["completion_rate"] = round((comp / total) * 100.0, 1) if total > 0 else 0.0
        if course.get("created_at"):
            course["created_at"] = course["created_at"].strftime("%Y-%m-%d")

        return jsonify({"success": True, "data": course})
    except Error as e:
        logger.error("Error fetching course detail: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve course detail."}), 500


@app.route("/api/courses/categories", methods=["GET"])
def api_get_course_categories():
    """Retrieve list of distinct existing course categories for filtering."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT category FROM courses WHERE category IS NOT NULL AND category != '' ORDER BY category ASC;")
        categories = [r["category"] for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": categories})
    except Error as e:
        logger.error("Error fetching categories: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve categories."}), 500


@app.route("/api/courses", methods=["POST"])
@login_required
@role_required("Admin")
def api_create_course():
    """Create a new course with optional description and credits."""
    payload = request.get_json(silent=True) or {}
    course_name = (payload.get("course_name") or "").strip()
    category = (payload.get("category") or "").strip()
    description = (payload.get("description") or "").strip() or None
    raw_credits = payload.get("credits")

    # Input validations
    if not course_name or len(course_name) < 2 or len(course_name) > 100:
        return jsonify({"success": False, "message": "Course name must be between 2 and 100 characters."}), 400

    if not category or len(category) < 2 or len(category) > 50:
        return jsonify({"success": False, "message": "Category must be between 2 and 50 characters."}), 400

    credits = None
    if raw_credits not in (None, ""):
        try:
            credits = int(raw_credits)
            if credits < 0 or credits > 30:
                return jsonify({"success": False, "message": "Credits must be a valid number between 0 and 30."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Credits must be a valid whole number."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            INSERT INTO courses (course_name, category, description, credits)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (course_name, category, description, credits))
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Course created successfully.",
            "data": {
                "course_id": new_id,
                "course_name": course_name,
                "category": category,
                "description": description,
                "credits": credits
            }
        }), 201
    except Error as e:
        logger.error("Error creating course: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to create course."}), 500


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
@login_required
@role_required("Admin")
def api_update_course(course_id):
    """Update an existing course's name, category, description, and credits."""
    payload = request.get_json(silent=True) or {}
    course_name = (payload.get("course_name") or "").strip()
    category = (payload.get("category") or "").strip()
    description = (payload.get("description") or "").strip() or None
    raw_credits = payload.get("credits")

    if not course_name or len(course_name) < 2 or len(course_name) > 100:
        return jsonify({"success": False, "message": "Course name must be between 2 and 100 characters."}), 400

    if not category or len(category) < 2 or len(category) > 50:
        return jsonify({"success": False, "message": "Category must be between 2 and 50 characters."}), 400

    credits = None
    if raw_credits not in (None, ""):
        try:
            credits = int(raw_credits)
            if credits < 0 or credits > 30:
                return jsonify({"success": False, "message": "Credits must be a valid number between 0 and 30."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Credits must be a valid whole number."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT course_id FROM courses WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Course not found."}), 404

        query = """
            UPDATE courses 
            SET course_name = %s, category = %s, description = %s, credits = %s 
            WHERE course_id = %s
        """
        cursor.execute(query, (course_name, category, description, credits, course_id))
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Course updated successfully.",
            "data": {
                "course_id": course_id,
                "course_name": course_name,
                "category": category,
                "description": description,
                "credits": credits
            }
        })
    except Error as e:
        logger.error("Error updating course: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update course."}), 500


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
@login_required
@role_required("Admin")
def api_delete_course(course_id):
    """Delete a course. Prevents deletion if existing enrollments are attached."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT course_name FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        if not course:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Course not found."}), 404

        # Safe deletion check: verify if enrollments exist
        cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE course_id = %s", (course_id,))
        count = cursor.fetchone()["count"]
        if count > 0:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": f"Cannot delete '{course['course_name']}' because {count} active learner enrollment(s) exist. Please remove or reassign enrollments first."
            }), 400

        cursor.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Course deleted successfully."})
    except Error as e:
        logger.error("Error deleting course: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to delete course."}), 500


# ====================================================================
# Learner Management APIs
# ====================================================================

@app.route("/api/learners", methods=["GET"])
def api_get_learners():
    """Lists learners with search by roll number/name/email and filter by department."""
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if search:
            where_clauses.append("(l.roll_no LIKE %s OR l.name LIKE %s OR l.email LIKE %s)")
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        if department:
            where_clauses.append("l.department = %s")
            params.append(department)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                l.learner_id,
                l.roll_no,
                l.name,
                l.email,
                l.department,
                l.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrollment_count,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count
            FROM learners l
            LEFT JOIN enrollments e ON l.learner_id = e.learner_id
            {where_sql}
            GROUP BY l.learner_id, l.roll_no, l.name, l.email, l.department, l.created_at
            ORDER BY l.learner_id DESC;
        """
        cursor.execute(query, tuple(params))
        learners = cursor.fetchall()
        cursor.close()
        conn.close()

        for l in learners:
            total = int(l.get("enrollment_count") or 0)
            comp = int(l.get("completed_count") or 0)
            l["completion_rate"] = round((comp / total) * 100.0, 1) if total > 0 else 0.0
            if l.get("created_at"):
                l["created_at"] = l["created_at"].strftime("%Y-%m-%d")

        return jsonify({"success": True, "data": learners})
    except Error as e:
        logger.error("Error fetching learners: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve learners."}), 500


@app.route("/api/learners/<int:learner_id>", methods=["GET"])
def api_get_learner_detail(learner_id):
    """Retrieve full profile details and overall stats for a single learner."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                l.learner_id,
                l.roll_no,
                l.name,
                l.email,
                l.department,
                l.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrollment_count,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
                COUNT(a.activity_id) AS total_activities_logged
            FROM learners l
            LEFT JOIN enrollments e ON l.learner_id = e.learner_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            WHERE l.learner_id = %s
            GROUP BY l.learner_id, l.roll_no, l.name, l.email, l.department, l.created_at;
        """
        cursor.execute(query, (learner_id,))
        learner = cursor.fetchone()
        cursor.close()
        conn.close()

        if not learner:
            return jsonify({"success": False, "message": "Learner not found."}), 404

        total = int(learner.get("enrollment_count") or 0)
        comp = int(learner.get("completed_count") or 0)
        learner["completion_rate"] = round((comp / total) * 100.0, 1) if total > 0 else 0.0
        if learner.get("created_at"):
            learner["created_at"] = learner["created_at"].strftime("%Y-%m-%d")

        return jsonify({"success": True, "data": learner})
    except Error as e:
        logger.error("Error fetching learner detail: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve learner detail."}), 500


@app.route("/api/learners/<int:learner_id>/progress", methods=["GET"])
def api_get_learner_progress(learner_id):
    """Retrieve detailed course-by-course progress and activity telemetry for a learner."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Check learner exists
        cursor.execute("SELECT learner_id, roll_no, name, email, department FROM learners WHERE learner_id = %s;", (learner_id,))
        learner = cursor.fetchone()
        if not learner:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Learner not found."}), 404

        query = """
            SELECT 
                e.enrollment_id,
                e.course_id,
                c.course_name,
                c.category,
                c.credits,
                e.enrolled_at,
                e.status,
                COUNT(a.activity_id) AS total_activities,
                SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) AS completed_activities,
                AVG(a.score) AS average_score,
                SUM(a.time_spent_minutes) AS total_time_spent_minutes,
                MAX(a.activity_date) AS last_activity_date
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            WHERE e.learner_id = %s
            GROUP BY e.enrollment_id, e.course_id, c.course_name, c.category, c.credits, e.enrolled_at, e.status
            ORDER BY e.enrolled_at DESC;
        """
        cursor.execute(query, (learner_id,))
        courses_progress = cursor.fetchall()
        cursor.close()
        conn.close()

        for cp in courses_progress:
            if cp.get("enrolled_at"):
                cp["enrolled_at"] = cp["enrolled_at"].strftime("%Y-%m-%d")
            if cp.get("last_activity_date"):
                cp["last_activity_date"] = cp["last_activity_date"].strftime("%Y-%m-%d %H:%M")
            if cp.get("average_score") is not None:
                cp["average_score"] = round(float(cp["average_score"]), 1)
            else:
                cp["average_score"] = None
            if cp.get("total_time_spent_minutes") is not None:
                cp["total_time_spent_minutes"] = int(cp["total_time_spent_minutes"])
            else:
                cp["total_time_spent_minutes"] = 0

        return jsonify({
            "success": True,
            "learner": learner,
            "data": courses_progress
        })
    except Error as e:
        logger.error("Error fetching learner progress: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve learner progress."}), 500


@app.route("/api/learners/departments", methods=["GET"])
def api_get_departments():
    """Retrieve list of distinct existing departments for filtering."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT department FROM learners WHERE department IS NOT NULL AND department != '' ORDER BY department ASC;")
        departments = [r["department"] for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": departments})
    except Error as e:
        logger.error("Error fetching departments: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve departments."}), 500


@app.route("/api/learners", methods=["POST"])
@login_required
@role_required("Admin")
def api_create_learner():
    """Register a new learner with roll number, optional name, email, and department."""
    payload = request.get_json(silent=True) or {}
    roll_no = (payload.get("roll_no") or "").strip().upper()
    name = (payload.get("name") or "").strip() or None
    email = (payload.get("email") or "").strip().lower() or None
    department = (payload.get("department") or "").strip() or None

    if not roll_no:
        return jsonify({"success": False, "message": "Roll number is required."}), 400

    if len(roll_no) < 2 or len(roll_no) > 30 or not re.match(r"^[A-Za-z0-9_-]+$", roll_no):
        return jsonify({"success": False, "message": "Roll number must be 2-30 characters (letters, numbers, hyphens, underscores)."}), 400

    if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    if name and len(name) > 100:
        return jsonify({"success": False, "message": "Name cannot exceed 100 characters."}), 400

    if department and len(department) > 50:
        return jsonify({"success": False, "message": "Department cannot exceed 50 characters."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            INSERT INTO learners (roll_no, name, email, department)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (roll_no, name, email, department))
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Learner registered successfully.",
            "data": {
                "learner_id": new_id,
                "roll_no": roll_no,
                "name": name,
                "email": email,
                "department": department
            }
        }), 201
    except Error as e:
        if conn and conn.is_connected():
            conn.close()
        if e.errno == errorcode.ER_DUP_ENTRY:
            return jsonify({
                "success": False,
                "message": f"Roll number '{roll_no}' already exists. Please specify a unique roll number."
            }), 409
        logger.error("Error creating learner: %s", e)
        return jsonify({"success": False, "message": "Failed to register learner."}), 500


@app.route("/api/learners/<int:learner_id>", methods=["PUT"])
@login_required
@role_required("Admin")
def api_update_learner(learner_id):
    """Update learner roll number, name, email, and department."""
    payload = request.get_json(silent=True) or {}
    roll_no = (payload.get("roll_no") or "").strip().upper()
    name = (payload.get("name") or "").strip() or None
    email = (payload.get("email") or "").strip().lower() or None
    department = (payload.get("department") or "").strip() or None

    if not roll_no:
        return jsonify({"success": False, "message": "Roll number is required."}), 400

    if len(roll_no) < 2 or len(roll_no) > 30 or not re.match(r"^[A-Za-z0-9_-]+$", roll_no):
        return jsonify({"success": False, "message": "Roll number must be 2-30 characters (letters, numbers, hyphens, underscores)."}), 400

    if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    if name and len(name) > 100:
        return jsonify({"success": False, "message": "Name cannot exceed 100 characters."}), 400

    if department and len(department) > 50:
        return jsonify({"success": False, "message": "Department cannot exceed 50 characters."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT learner_id FROM learners WHERE learner_id = %s", (learner_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Learner not found."}), 404

        query = """
            UPDATE learners 
            SET roll_no = %s, name = %s, email = %s, department = %s 
            WHERE learner_id = %s
        """
        cursor.execute(query, (roll_no, name, email, department, learner_id))
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Learner updated successfully.",
            "data": {
                "learner_id": learner_id,
                "roll_no": roll_no,
                "name": name,
                "email": email,
                "department": department
            }
        })
    except Error as e:
        if conn and conn.is_connected():
            conn.close()
        if e.errno == errorcode.ER_DUP_ENTRY:
            return jsonify({
                "success": False,
                "message": f"Roll number '{roll_no}' already in use by another learner."
            }), 409
        logger.error("Error updating learner: %s", e)
        return jsonify({"success": False, "message": "Failed to update learner."}), 500


@app.route("/api/learners/<int:learner_id>", methods=["DELETE"])
@login_required
@role_required("Admin")
def api_delete_learner(learner_id):
    """Delete a learner safely. Prevents deletion if enrollments exist."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT roll_no FROM learners WHERE learner_id = %s", (learner_id,))
        learner = cursor.fetchone()
        if not learner:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Learner not found."}), 404

        # Safe deletion check: enrollments attached?
        cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE learner_id = %s", (learner_id,))
        count = cursor.fetchone()["count"]
        if count > 0:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": f"Cannot delete learner '{learner['roll_no']}' because they are enrolled in {count} course(s). Please remove enrollments first."
            }), 400

        cursor.execute("DELETE FROM learners WHERE learner_id = %s", (learner_id,))
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Learner removed successfully."})
    except Error as e:
        logger.error("Error deleting learner: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to delete learner."}), 500


@app.route("/api/learners/<int:learner_id>/enrollments", methods=["GET"])
def api_get_learner_enrollments(learner_id):
    """View all course enrollments for a specific learner."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                e.enrollment_id,
                e.course_id,
                c.course_name,
                c.category,
                e.enrolled_at,
                e.status,
                COUNT(a.activity_id) AS total_activities
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            WHERE e.learner_id = %s
            GROUP BY e.enrollment_id, e.course_id, c.course_name, c.category, e.enrolled_at, e.status
            ORDER BY e.enrolled_at DESC;
        """
        cursor.execute(query, (learner_id,))
        enrollments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": enrollments})
    except Error as e:
        logger.error("Error fetching learner enrollments: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve learner enrollments."}), 500


# ====================================================================
# Enrollment Management APIs
# ====================================================================

@app.route("/api/enrollments", methods=["GET"])
def api_get_enrollments():
    """
    List enrollments with optional filtering by course_id, status, or search query.
    """
    course_id = request.args.get("course_id", type=int)
    status = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if course_id:
            where_clauses.append("e.course_id = %s")
            params.append(course_id)
        if status:
            where_clauses.append("e.status = %s")
            params.append(status)
        if search:
            where_clauses.append("(l.roll_no LIKE %s OR c.course_name LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                e.enrollment_id,
                e.learner_id,
                l.roll_no,
                e.course_id,
                c.course_name,
                c.category,
                e.enrolled_at,
                e.status,
                COUNT(a.activity_id) AS activity_count,
                MAX(a.activity_date) AS last_activity_date
            FROM enrollments e
            JOIN learners l ON e.learner_id = l.learner_id
            JOIN courses c ON e.course_id = c.course_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            {where_sql}
            GROUP BY 
                e.enrollment_id, e.learner_id, l.roll_no, 
                e.course_id, c.course_name, c.category, 
                e.enrolled_at, e.status
            ORDER BY e.enrolled_at DESC;
        """
        cursor.execute(query, tuple(params))
        enrollments = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format dates for JSON
        for row in enrollments:
            if row.get("enrolled_at"):
                row["enrolled_at"] = row["enrolled_at"].strftime("%Y-%m-%d %H:%M")
            if row.get("last_activity_date"):
                row["last_activity_date"] = row["last_activity_date"].strftime("%Y-%m-%d %H:%M")

        return jsonify({"success": True, "data": enrollments})
    except Error as e:
        logger.error("Error fetching enrollments: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve enrollments."}), 500


@app.route("/api/enrollments", methods=["POST"])
@login_required
@role_required("Admin")
def api_create_enrollment():
    """Enroll a learner into a course. Prevents duplicate enrollments."""
    payload = request.get_json(silent=True) or {}
    learner_id = payload.get("learner_id")
    course_id = payload.get("course_id")
    status = payload.get("status", "Enrolled")

    if not learner_id or not course_id:
        return jsonify({"success": False, "message": "Learner and Course selections are required."}), 400

    if status not in ["Enrolled", "In Progress", "Completed"]:
        status = "Enrolled"

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Check if learner exists
        cursor.execute("SELECT roll_no FROM learners WHERE learner_id = %s", (learner_id,))
        learner = cursor.fetchone()
        if not learner:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Selected learner does not exist."}), 404

        # Check if course exists
        cursor.execute("SELECT course_name FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        if not course:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Selected course does not exist."}), 404

        query = "INSERT INTO enrollments (learner_id, course_id, status) VALUES (%s, %s, %s)"
        cursor.execute(query, (learner_id, course_id, status))
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Successfully enrolled {learner['roll_no']} into '{course['course_name']}'.",
            "data": {"enrollment_id": new_id, "learner_id": learner_id, "course_id": course_id, "status": status}
        }), 201
    except Error as e:
        if conn and conn.is_connected():
            conn.close()
        if e.errno == errorcode.ER_DUP_ENTRY:
            return jsonify({
                "success": False,
                "message": "Duplicate Enrollment: This learner is already enrolled in the selected course."
            }), 409
        logger.error("Error creating enrollment: %s", e)
        return jsonify({"success": False, "message": "Failed to create enrollment."}), 500


@app.route("/api/enrollments/<int:enrollment_id>", methods=["PUT"])
@login_required
@role_required("Admin", "Instructor")
def api_update_enrollment_status(enrollment_id):
    """Update enrollment status ('Enrolled', 'In Progress', 'Completed')."""
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")

    if new_status not in ["Enrolled", "In Progress", "Completed"]:
        return jsonify({"success": False, "message": "Invalid status. Allowed values: Enrolled, In Progress, Completed."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT enrollment_id FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Enrollment record not found."}), 404

        cursor.execute("UPDATE enrollments SET status = %s WHERE enrollment_id = %s", (new_status, enrollment_id))
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Enrollment status updated to '{new_status}'.",
            "data": {"enrollment_id": enrollment_id, "status": new_status}
        })
    except Error as e:
        logger.error("Error updating enrollment: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update enrollment."}), 500


@app.route("/api/enrollments/<int:enrollment_id>/activities", methods=["GET"])
def api_get_enrollment_activities(enrollment_id):
    """List historical activities for a specific enrollment."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.*, e.status AS enrollment_status, l.roll_no, c.course_name
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            JOIN learners l ON e.learner_id = l.learner_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE a.enrollment_id = %s
            ORDER BY a.activity_date DESC;
        """
        cursor.execute(query, (enrollment_id,))
        activities = cursor.fetchall()
        cursor.close()
        conn.close()

        for a in activities:
            if a.get("activity_date"):
                a["activity_date"] = a["activity_date"].strftime("%Y-%m-%d %H:%M")
            if a.get("score") is not None:
                a["score"] = float(a["score"])

        return jsonify({"success": True, "data": activities})
    except Error as e:
        logger.error("Error fetching enrollment activities: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve activities."}), 500


# ====================================================================
# Activity Management APIs
# ====================================================================

ALLOWED_ACTIVITY_TYPES = ["Lesson", "Quiz", "Assignment", "Practice", "Project"]


@app.route("/api/activities", methods=["GET"])
def api_get_activities():
    """
    List activities with rich filtering options (learner, course, type, date range).
    """
    enrollment_id = request.args.get("enrollment_id", type=int)
    learner_id = request.args.get("learner_id", type=int)
    course_id = request.args.get("course_id", type=int)
    activity_type = request.args.get("activity_type", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    limit = request.args.get("limit", default=100, type=int)

    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if enrollment_id:
            where_clauses.append("a.enrollment_id = %s")
            params.append(enrollment_id)
        if learner_id:
            where_clauses.append("e.learner_id = %s")
            params.append(learner_id)
        if course_id:
            where_clauses.append("e.course_id = %s")
            params.append(course_id)
        if activity_type:
            where_clauses.append("a.activity_type = %s")
            params.append(activity_type)
        if start_d:
            where_clauses.append("a.activity_date >= %s")
            params.append(f"{start_d} 00:00:00")
        if end_d:
            where_clauses.append("a.activity_date <= %s")
            params.append(f"{end_d} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                a.activity_id,
                a.enrollment_id,
                a.activity_type,
                a.completed,
                a.score,
                a.time_spent_minutes,
                a.activity_date,
                l.learner_id,
                l.roll_no,
                c.course_id,
                c.course_name
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            JOIN learners l ON e.learner_id = l.learner_id
            JOIN courses c ON e.course_id = c.course_id
            {where_sql}
            ORDER BY a.activity_date DESC
            LIMIT %s;
        """
        params.append(limit)
        cursor.execute(query, tuple(params))
        activities = cursor.fetchall()
        cursor.close()
        conn.close()

        for a in activities:
            if a.get("activity_date"):
                a["activity_date"] = a["activity_date"].strftime("%Y-%m-%d %H:%M:%S")
            if a.get("score") is not None:
                a["score"] = float(a["score"])

        return jsonify({"success": True, "data": activities})
    except Error as e:
        logger.error("Error fetching activities: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve activities."}), 500


@app.route("/api/activities", methods=["POST"])
@login_required
@role_required("Admin", "Instructor")
def api_create_activity():
    """
    Record a new learning activity for an existing enrollment.
    Uses actual timestamps or user-provided datetime.
    """
    payload = request.get_json(silent=True) or {}
    enrollment_id = payload.get("enrollment_id")
    activity_type = (payload.get("activity_type") or "").strip()
    completed = bool(payload.get("completed", False))
    activity_date = payload.get("activity_date")
    score = payload.get("score")
    time_spent = payload.get("time_spent_minutes")

    if not enrollment_id or not activity_type:
        return jsonify({"success": False, "message": "Enrollment ID and Activity Type are required."}), 400

    if activity_type not in ALLOWED_ACTIVITY_TYPES:
        return jsonify({
            "success": False,
            "message": f"Invalid activity type '{activity_type}'. Allowed types: {', '.join(ALLOWED_ACTIVITY_TYPES)}"
        }), 400

    score_val = None
    if score not in (None, ""):
        try:
            score_val = float(score)
            if score_val < 0 or score_val > 100:
                return jsonify({"success": False, "message": "Score must be between 0 and 100."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Score must be a valid number."}), 400

    time_val = None
    if time_spent not in (None, ""):
        try:
            time_val = int(time_spent)
            if time_val < 0:
                return jsonify({"success": False, "message": "Time spent cannot be negative."}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Time spent must be a valid whole number."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Verify enrollment exists
        cursor.execute("SELECT enrollment_id, status FROM enrollments WHERE enrollment_id = %s", (enrollment_id,))
        enrollment = cursor.fetchone()
        if not enrollment:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Enrollment record does not exist."}), 404

        if activity_date:
            query = """
                INSERT INTO activities (enrollment_id, activity_type, completed, score, time_spent_minutes, activity_date)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (enrollment_id, activity_type, completed, score_val, time_val, activity_date))
        else:
            query = """
                INSERT INTO activities (enrollment_id, activity_type, completed, score, time_spent_minutes, activity_date)
                VALUES (%s, %s, %s, %s, %s, NOW());
            """
            cursor.execute(query, (enrollment_id, activity_type, completed, score_val, time_val))

        new_activity_id = cursor.lastrowid

        # Automatic status progression: If enrollment was 'Enrolled', advance to 'In Progress' upon activity record
        if enrollment["status"] == "Enrolled":
            cursor.execute("UPDATE enrollments SET status = 'In Progress' WHERE enrollment_id = %s", (enrollment_id,))

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Activity recorded successfully.",
            "data": {
                "activity_id": new_activity_id,
                "enrollment_id": enrollment_id,
                "activity_type": activity_type,
                "completed": completed
            }
        }), 201
    except Error as e:
        logger.error("Error creating activity: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to record activity."}), 500


@app.route("/api/activities/<int:activity_id>", methods=["PUT"])
@login_required
@role_required("Admin", "Instructor")
def api_update_activity(activity_id):
    """Update completion status or activity type of an activity record."""
    payload = request.get_json(silent=True) or {}
    completed = payload.get("completed")
    activity_type = payload.get("activity_type")

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (activity_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Activity not found."}), 404

        updates = []
        params = []
        if completed is not None:
            updates.append("completed = %s")
            params.append(bool(completed))
        if activity_type:
            if activity_type not in ALLOWED_ACTIVITY_TYPES:
                cursor.close()
                conn.close()
                return jsonify({"success": False, "message": "Invalid activity type."}), 400
            updates.append("activity_type = %s")
            params.append(activity_type)
        if "score" in payload:
            raw_s = payload["score"]
            updates.append("score = %s")
            params.append(float(raw_s) if raw_s not in (None, "") else None)
        if "time_spent_minutes" in payload:
            raw_t = payload["time_spent_minutes"]
            updates.append("time_spent_minutes = %s")
            params.append(int(raw_t) if raw_t not in (None, "") else None)

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "No valid fields provided to update."}), 400

        params.append(activity_id)
        query = f"UPDATE activities SET {', '.join(updates)} WHERE activity_id = %s"
        cursor.execute(query, tuple(params))
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Activity updated successfully."})
    except Error as e:
        logger.error("Error updating activity: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update activity."}), 500


# ====================================================================
# CSV Report Exports & Backend Chart Generation
# ====================================================================

def sanitize_csv_cell(value):
    """
    Sanitizes a cell value against CSV formula injection (CWE-1236).
    Neutralizes formula triggers (=, +, -, @, \t, \r, \n) by prefixing with a single quote (').
    Preserves legitimate numeric values (including negative numbers and floats).
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return value

    val_str = str(value)
    if not val_str:
        return ""

    # Check if this string is a legitimate number (e.g. "123", "-45", "3.14", "+5")
    try:
        float(val_str)
        return val_str
    except ValueError:
        pass

    # Inspect first character after stripping whitespace/control characters
    stripped = val_str.lstrip(' \t\r\n')
    if stripped:
        first_char = stripped[0]
        if first_char in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + val_str

    if val_str and val_str[0] in ('\t', '\r', '\n'):
        return "'" + val_str

    return val_str


def generate_csv_response(filename, fieldnames, rows):
    """
    Builds a standardized, sanitized CSV response with CWE-1236 formula injection protection.
    Saves a copy into exports/ and streams attachment to client.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{filename}_{timestamp}.csv"

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for row in rows:
        sanitized_row = {k: sanitize_csv_cell(row.get(k)) for k in fieldnames}
        writer.writerow(sanitized_row)

    csv_content = output.getvalue()
    output.close()

    try:
        exports_dir = os.path.join(os.path.dirname(__file__), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        file_path = os.path.join(exports_dir, clean_filename)
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            f.write(csv_content)
    except Exception as e:
        logger.warning("Could not cache CSV in exports dir: %s", e)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


def generate_json_response(filename, title, filters, summary, rows):
    """
    Builds a standardized JSON report attachment with metadata and records.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{filename}_{timestamp}.json"
    payload = {
        "success": True,
        "report_title": title,
        "generated_at": datetime.now().isoformat(),
        "applied_filters": filters,
        "summary": summary,
        "total_records": len(rows),
        "data": rows
    }
    json_content = json.dumps(payload, indent=2, default=str)
    return Response(
        json_content,
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}",
            "Content-Type": "application/json; charset=utf-8"
        }
    )


def generate_pdf_response(filename, title, field_labels, rows, kpi_items=None, filter_text=None, chart_filename=None):
    """
    Builds a styled PDF analytical document using reports_pdf.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{filename}_{timestamp}.pdf"
    pdf_bytes = reports_pdf.build_pdf_report(
        report_title=title,
        field_labels=field_labels,
        rows=rows,
        kpi_items=kpi_items,
        filter_text=filter_text,
        chart_filename=chart_filename
    )
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={clean_filename}",
            "Content-Type": "application/pdf"
        }
    )


# 1. Course Completion Report Exports
@app.route("/api/reports/course-completion.csv", methods=["GET"])
@login_required
def export_course_completion_csv():
    """Download Course Completion Report as Sanitized CSV."""
    course_id = request.args.get("course_id", type=int)
    data = analytics.get_course_completion_analytics(course_id=course_id)
    fieldnames = [
        "course_id", "course_name", "category",
        "total_enrollments", "completed_enrollments",
        "in_progress_enrollments", "enrolled_enrollments",
        "completion_rate", "performance_status"
    ]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("course_completion_report", fieldnames, rows)


@app.route("/api/reports/course-completion.json", methods=["GET"])
@login_required
def export_course_completion_json():
    """Download Course Completion Report as JSON."""
    course_id = request.args.get("course_id", type=int)
    data = analytics.get_course_completion_analytics(course_id=course_id)
    summary = {
        "total_courses": len(data),
        "total_enrollments": sum(d.get("total_enrollments", 0) for d in data),
        "completed_enrollments": sum(d.get("completed_enrollments", 0) for d in data)
    }
    return generate_json_response("course_completion_report", "Course Completion Analytics", {"course_id": course_id}, summary, data)


@app.route("/api/reports/course-completion.pdf", methods=["GET"])
@login_required
def export_course_completion_pdf():
    """Download Course Completion Report as PDF."""
    course_id = request.args.get("course_id", type=int)
    data = analytics.get_course_completion_analytics(course_id=course_id)
    field_labels = [
        ("course_id", "ID", 35),
        ("course_name", "Course Name", 200),
        ("category", "Category", 110),
        ("total_enrollments", "Enrolled", 65),
        ("completed_enrollments", "Completed", 65),
        ("in_progress_enrollments", "In Progress", 65),
        ("completion_rate", "Rate (%)", 65),
        ("performance_status", "Benchmark", 115)
    ]
    tot = sum(d.get("total_enrollments", 0) for d in data)
    comp = sum(d.get("completed_enrollments", 0) for d in data)
    rate = f"{(comp / tot * 100):.1f}%" if tot > 0 else "0.0%"
    kpis = [
        ("Catalog Courses", len(data)),
        ("Total Enrollments", tot),
        ("Completed Seats", comp),
        ("Platform Completion", rate)
    ]
    return generate_pdf_response(
        "course_completion_report", "Course Completion Analytics Report",
        field_labels, data, kpis, "Active Catalog", "course_completion_bar.png"
    )


# 2. Inactive Enrollments Report Exports
@app.route("/api/reports/inactive-enrollments.csv", methods=["GET"])
@login_required
def export_inactive_enrollments_csv():
    """Download Inactive Enrollments Report as Sanitized CSV."""
    threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
    data = analytics.get_inactive_enrollments(threshold_days=threshold)
    fieldnames = [
        "enrollment_id", "roll_no", "course_name", "category",
        "enrolled_at", "last_activity_date", "days_since_last_activity",
        "status", "inactivity_reason"
    ]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("inactive_enrollments_report", fieldnames, rows)


@app.route("/api/reports/inactive-enrollments.json", methods=["GET"])
@login_required
def export_inactive_enrollments_json():
    """Download Inactive Enrollments Report as JSON."""
    threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
    data = analytics.get_inactive_enrollments(threshold_days=threshold)
    return generate_json_response("inactive_enrollments_report", "Inactive Enrollments Audit", {"threshold_days": threshold}, {"inactive_count": len(data)}, data)


@app.route("/api/reports/inactive-enrollments.pdf", methods=["GET"])
@login_required
def export_inactive_enrollments_pdf():
    """Download Inactive Enrollments Report as PDF."""
    threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
    data = analytics.get_inactive_enrollments(threshold_days=threshold)
    field_labels = [
        ("enrollment_id", "Enr #", 40),
        ("roll_no", "Roll Number", 90),
        ("course_name", "Course Name", 180),
        ("category", "Category", 100),
        ("enrolled_at", "Enrolled Date", 80),
        ("days_since_last_activity", "Inactive Days", 70),
        ("status", "Status", 70),
        ("inactivity_reason", "Reason", 90)
    ]
    kpis = [
        ("Inactivity Threshold", f">{threshold} Days"),
        ("Flagged Enrollments", len(data)),
        ("Review Urgency", "Immediate Action" if len(data) > 0 else "Normal")
    ]
    return generate_pdf_response(
        "inactive_enrollments_report", "Inactive Enrollments Audit Report",
        field_labels, data, kpis, f"Inactivity Threshold: > {threshold} Days", None
    )


# 3. Weekly Learning Activity Report Exports
@app.route("/api/reports/weekly-activity.csv", methods=["GET"])
@login_required
def export_weekly_activity_csv():
    """Download Weekly Learning Activity Report as Sanitized CSV."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_weekly_activity_analytics(start_date=start_d, end_date=end_d)
    fieldnames = ["week_start", "week_label", "iso_week", "total", "completed", "incomplete"]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("weekly_activity_report", fieldnames, rows)


@app.route("/api/reports/weekly-activity.json", methods=["GET"])
@login_required
def export_weekly_activity_json():
    """Download Weekly Learning Activity Report as JSON."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_weekly_activity_analytics(start_date=start_d, end_date=end_d)
    summary = {
        "total_weeks": len(data),
        "total_activities": sum(d.get("total", 0) for d in data),
        "completed_activities": sum(d.get("completed", 0) for d in data)
    }
    return generate_json_response("weekly_activity_report", "Weekly Learning Activity Report", {"start_date": start_d, "end_date": end_d}, summary, data)


@app.route("/api/reports/weekly-activity.pdf", methods=["GET"])
@login_required
def export_weekly_activity_pdf():
    """Download Weekly Learning Activity Report as PDF."""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_weekly_activity_analytics(start_date=start_d, end_date=end_d)
    field_labels = [
        ("week_start", "Week Start", 100),
        ("week_label", "Calendar Label", 180),
        ("iso_week", "ISO Week Code", 100),
        ("total", "Total Submissions", 110),
        ("completed", "Completed", 110),
        ("incomplete", "Incomplete", 120)
    ]
    tot = sum(d.get("total", 0) for d in data)
    comp = sum(d.get("completed", 0) for d in data)
    kpis = [
        ("Calendar Weeks", len(data)),
        ("Total Submissions", tot),
        ("Completed Volume", comp),
        ("Completion Rate", f"{(comp / tot * 100):.1f}%" if tot > 0 else "0.0%")
    ]
    date_filter_text = f"Date Window: {start_d} to {end_d}" if start_d and end_d else "All Time"
    return generate_pdf_response(
        "weekly_activity_report", "Weekly Learning Activity Report",
        field_labels, data, kpis, date_filter_text, "weekly_activity_trend.png"
    )


# 4. Course Comparison Report Exports
@app.route("/api/reports/course-comparison.csv", methods=["GET"])
@login_required
def export_course_comparison_csv():
    """Download Course Comparison Report as Sanitized CSV."""
    data = analytics.get_course_comparison()
    fieldnames = [
        "course_id", "course_name", "category",
        "total_enrollments", "completed_enrollments", "in_progress_enrollments",
        "total_activities", "completed_activities", "avg_activities_per_learner",
        "completion_rate", "performance_status"
    ]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("course_comparison_report", fieldnames, rows)


@app.route("/api/reports/course-comparison.json", methods=["GET"])
@login_required
def export_course_comparison_json():
    """Download Course Comparison Report as JSON."""
    data = analytics.get_course_comparison()
    summary = {
        "total_courses": len(data),
        "total_enrollments": sum(d.get("total_enrollments", 0) for d in data),
        "total_activities": sum(d.get("total_activities", 0) for d in data)
    }
    return generate_json_response("course_comparison_report", "Course Benchmark & Engagement Report", {}, summary, data)


@app.route("/api/reports/course-comparison.pdf", methods=["GET"])
@login_required
def export_course_comparison_pdf():
    """Download Course Comparison Report as PDF."""
    data = analytics.get_course_comparison()
    field_labels = [
        ("course_id", "ID", 30),
        ("course_name", "Course Title", 180),
        ("category", "Category", 100),
        ("total_enrollments", "Enrolled", 60),
        ("completed_enrollments", "Completed", 60),
        ("total_activities", "Activities", 65),
        ("avg_activities_per_learner", "Avg Act/Student", 80),
        ("completion_rate", "Rate (%)", 65),
        ("performance_status", "Status", 80)
    ]
    tot_enr = sum(d.get("total_enrollments", 0) for d in data)
    tot_act = sum(d.get("total_activities", 0) for d in data)
    kpis = [
        ("Courses Benchmarked", len(data)),
        ("Total Enrollments", tot_enr),
        ("Activities Logged", tot_act),
        ("Platform Avg Engagement", f"{(tot_act / tot_enr):.1f} acts/student" if tot_enr > 0 else "0")
    ]
    return generate_pdf_response(
        "course_comparison_report", "Course Benchmark & Comparison Report",
        field_labels, data, kpis, "All Courses Benchmark", "course_engagement_comparison.png"
    )


# 5. Learner Performance Report Exports
@app.route("/api/reports/learner-performance.csv", methods=["GET"])
@login_required
def export_learner_performance_csv():
    """Download Learner Academic Performance Report as Sanitized CSV."""
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    data = analytics.get_learner_performance_analytics(search=search or None, department=department or None)
    fieldnames = [
        "learner_id", "roll_no", "name", "email", "department",
        "enrolled_courses_count", "completed_courses_count", "in_progress_courses_count",
        "completion_rate", "total_activities_logged", "completed_activities_count",
        "average_score", "total_time_spent_minutes", "last_active_date", "engagement_status"
    ]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("learner_performance_report", fieldnames, rows)


@app.route("/api/reports/learner-performance.json", methods=["GET"])
@login_required
def export_learner_performance_json():
    """Download Learner Academic Performance Report as JSON."""
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    data = analytics.get_learner_performance_analytics(search=search or None, department=department or None)
    summary = {
        "learners_count": len(data),
        "total_enrolled_seats": sum(d.get("enrolled_courses_count", 0) for d in data),
        "completed_courses": sum(d.get("completed_courses_count", 0) for d in data)
    }
    return generate_json_response("learner_performance_report", "Learner Academic Performance Report", {"search": search, "department": department}, summary, data)


@app.route("/api/reports/learner-performance.pdf", methods=["GET"])
@login_required
def export_learner_performance_pdf():
    """Download Learner Academic Performance Report as PDF."""
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    data = analytics.get_learner_performance_analytics(search=search or None, department=department or None)
    field_labels = [
        ("roll_no", "Roll No", 75),
        ("name", "Student Name", 110),
        ("department", "Department", 80),
        ("enrolled_courses_count", "Enrolled", 55),
        ("completed_courses_count", "Completed", 55),
        ("completion_rate", "Rate (%)", 60),
        ("total_activities_logged", "Activities", 60),
        ("average_score", "Score", 55),
        ("total_time_spent_minutes", "Time (m)", 60),
        ("engagement_status", "Academic Status", 110)
    ]
    completed_all = sum(1 for d in data if d.get("engagement_status") == "Completed All")
    kpis = [
        ("Total Students", len(data)),
        ("Completed All", completed_all),
        ("Active Engagement Rate", f"{(completed_all / len(data) * 100):.1f}%" if data else "0.0%"),
        ("Filter Scope", department or "All Departments")
    ]
    filter_label = f"Search: '{search}' | Dept: {department}" if search or department else "All Enrolled Students"
    return generate_pdf_response(
        "learner_performance_report", "Learner Academic Performance Report",
        field_labels, data, kpis, filter_label, None
    )


# 6. Activity Participation Report Exports
@app.route("/api/reports/activity-participation.csv", methods=["GET"])
@login_required
def export_activity_participation_csv():
    """Download Activity Participation Report as Sanitized CSV."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_activity_participation_analytics(
        course_id=course_id,
        start_date=start_d,
        end_date=end_d
    )
    fieldnames = [
        "activity_type", "total_count", "completed_count", "pending_count",
        "completion_rate", "percentage_of_all_activities", "average_score", "total_time_spent_minutes"
    ]
    rows = [{k: item.get(k) for k in fieldnames} for item in data]
    return generate_csv_response("activity_participation_report", fieldnames, rows)


@app.route("/api/reports/activity-participation.json", methods=["GET"])
@login_required
def export_activity_participation_json():
    """Download Activity Participation Report as JSON."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_activity_participation_analytics(
        course_id=course_id,
        start_date=start_d,
        end_date=end_d
    )
    summary = {
        "activity_types_count": len(data),
        "total_activities": sum(d.get("total_count", 0) for d in data),
        "completed_activities": sum(d.get("completed_count", 0) for d in data)
    }
    return generate_json_response("activity_participation_report", "Activity Participation Breakdown", {"course_id": course_id, "start_date": start_d, "end_date": end_d}, summary, data)


@app.route("/api/reports/activity-participation.pdf", methods=["GET"])
@login_required
def export_activity_participation_pdf():
    """Download Activity Participation Report as PDF."""
    course_id = request.args.get("course_id", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    start_d, end_d, err = validate_date_range(start_date, end_date)
    if err:
        return jsonify({"success": False, "error": err}), 400

    data = analytics.get_activity_participation_analytics(
        course_id=course_id,
        start_date=start_d,
        end_date=end_d
    )
    field_labels = [
        ("activity_type", "Activity Type", 140),
        ("total_count", "Total Logged", 95),
        ("completed_count", "Completed", 95),
        ("pending_count", "Pending", 95),
        ("completion_rate", "Completion (%)", 95),
        ("percentage_of_all_activities", "Catalog Share (%)", 100),
        ("average_score", "Avg Score", 100)
    ]
    tot = sum(d.get("total_count", 0) for d in data)
    comp = sum(d.get("completed_count", 0) for d in data)
    kpis = [
        ("Activity Categories", len(data)),
        ("Total Submissions", tot),
        ("Completed Volume", comp),
        ("Overall Completion Rate", f"{(comp / tot * 100):.1f}%" if tot > 0 else "0.0%")
    ]
    return generate_pdf_response(
        "activity_participation_report", "Activity Participation & Breakdown Report",
        field_labels, data, kpis, "All Logged Student Activities", "activity_type_distribution.png"
    )


# 7. Printable HTML Report Route
@app.route("/reports/printable/<report_type>", methods=["GET"])
@login_required
def page_printable_report(report_type):
    """
    Renders high-contrast, clean printable HTML analytical document with
    browser print and PDF export support.
    """
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    report_type = report_type.lower().replace("-", "_")

    if report_type == "course_completion":
        course_id = request.args.get("course_id", type=int)
        data = analytics.get_course_completion_analytics(course_id=course_id)
        headers = [
            ("course_id", "ID"), ("course_name", "Course Name"), ("category", "Category"),
            ("total_enrollments", "Total Enrolled"), ("completed_enrollments", "Completed"),
            ("in_progress_enrollments", "In Progress"), ("completion_rate", "Completion Rate"),
            ("performance_status", "Status")
        ]
        tot = sum(d.get("total_enrollments", 0) for d in data)
        comp = sum(d.get("completed_enrollments", 0) for d in data)
        kpis = [("Total Courses", len(data)), ("Total Enrollments", tot), ("Completed", comp), ("Completion Rate", f"{(comp / tot * 100):.1f}%" if tot > 0 else "0%")]
        return render_template("printable_report.html", title="Course Completion Analytics Report", generated_at=now_str, filter_summary="Active Catalog", kpis=kpis, headers=headers, rows=data)

    elif report_type == "inactive_enrollments":
        threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
        data = analytics.get_inactive_enrollments(threshold_days=threshold)
        headers = [
            ("roll_no", "Roll Number"), ("course_name", "Course Name"), ("category", "Category"),
            ("enrolled_at", "Enrolled Date"), ("last_activity_date", "Last Active"),
            ("days_since_last_activity", "Inactive Days"), ("status", "Status"), ("inactivity_reason", "Reason")
        ]
        kpis = [("Threshold", f">{threshold} Days"), ("Flagged Enrollments", len(data))]
        return render_template("printable_report.html", title="Inactive Enrollments Audit Report", generated_at=now_str, filter_summary=f"Threshold: > {threshold} Days", kpis=kpis, headers=headers, rows=data)

    elif report_type == "weekly_activity":
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        start_d, end_d, _ = validate_date_range(start_date, end_date)
        data = analytics.get_weekly_activity_analytics(start_date=start_d, end_date=end_d)
        headers = [
            ("week_start", "Week Start"), ("week_label", "Calendar Week"), ("iso_week", "ISO Week"),
            ("total", "Total Submissions"), ("completed", "Completed"), ("incomplete", "Incomplete")
        ]
        tot = sum(d.get("total", 0) for d in data)
        comp = sum(d.get("completed", 0) for d in data)
        kpis = [("Total Weeks", len(data)), ("Total Submissions", tot), ("Completed Submissions", comp)]
        return render_template("printable_report.html", title="Weekly Learning Activity Report", generated_at=now_str, filter_summary=f"Date Range: {start_d} to {end_d}" if start_d else "All Time", kpis=kpis, headers=headers, rows=data)

    elif report_type == "course_comparison":
        data = analytics.get_course_comparison()
        headers = [
            ("course_id", "ID"), ("course_name", "Course Title"), ("category", "Category"),
            ("total_enrollments", "Enrolled"), ("completed_enrollments", "Completed"),
            ("total_activities", "Activities"), ("avg_activities_per_learner", "Avg Act/Student"),
            ("completion_rate", "Completion Rate"), ("performance_status", "Status")
        ]
        tot_enr = sum(d.get("total_enrollments", 0) for d in data)
        tot_act = sum(d.get("total_activities", 0) for d in data)
        kpis = [("Courses", len(data)), ("Total Enrollments", tot_enr), ("Total Activities", tot_act)]
        return render_template("printable_report.html", title="Course Performance Comparison Report", generated_at=now_str, filter_summary="All Active Courses", kpis=kpis, headers=headers, rows=data)

    elif report_type == "learner_performance":
        search = request.args.get("search", "").strip()
        department = request.args.get("department", "").strip()
        data = analytics.get_learner_performance_analytics(search=search or None, department=department or None)
        headers = [
            ("roll_no", "Roll Number"), ("name", "Student Name"), ("department", "Department"),
            ("enrolled_courses_count", "Enrolled"), ("completed_courses_count", "Completed"),
            ("completion_rate", "Completion Rate"), ("total_activities_logged", "Activities"),
            ("average_score", "Avg Score"), ("total_time_spent_minutes", "Study Time (m)"),
            ("engagement_status", "Status")
        ]
        completed_all = sum(1 for d in data if d.get("engagement_status") == "Completed All")
        kpis = [("Total Students", len(data)), ("Completed All", completed_all)]
        return render_template("printable_report.html", title="Learner Academic Performance Report", generated_at=now_str, filter_summary=f"Department: {department or 'All'}", kpis=kpis, headers=headers, rows=data)

    elif report_type == "activity_participation":
        course_id = request.args.get("course_id", type=int)
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        start_d, end_d, _ = validate_date_range(start_date, end_date)
        data = analytics.get_activity_participation_analytics(course_id=course_id, start_date=start_d, end_date=end_d)
        headers = [
            ("activity_type", "Activity Type"), ("total_count", "Total Logged"),
            ("completed_count", "Completed"), ("pending_count", "Pending"),
            ("completion_rate", "Completion Rate"), ("percentage_of_all_activities", "Catalog Share (%)"),
            ("average_score", "Average Score")
        ]
        tot = sum(d.get("total_count", 0) for d in data)
        comp = sum(d.get("completed_count", 0) for d in data)
        kpis = [("Activity Types", len(data)), ("Total Logged", tot), ("Completed", comp)]
        return render_template("printable_report.html", title="Activity Participation & Breakdown Report", generated_at=now_str, filter_summary="All Activity Types", kpis=kpis, headers=headers, rows=data)

    flash("Unknown report type requested.", "warning")
    return redirect(url_for("page_reports"))


@app.route("/api/reports/generate-charts", methods=["POST"])
@login_required
@role_required("Admin", "Academic Analyst")
def api_generate_charts():
    """Generates backend Matplotlib charts and returns their filenames."""
    charts = analytics.generate_analytics_charts()
    return jsonify({
        "success": True,
        "message": f"Generated {len(charts)} chart(s) successfully.",
        "charts": charts,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ====================================================================
# Global Error Handlers (Return structured JSON for API, HTML for pages)
# ====================================================================

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "API endpoint not found."}), 404
    return render_template("base.html", page_title="Page Not Found"), 404


@app.errorhandler(500)
def internal_server_error(error):
    logger.error("Internal Server Error: %s", error)
    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "message": "An internal server error occurred. Please check database connection and server logs."
        }), 500
    return render_template("base.html", page_title="Server Error"), 500


# ====================================================================
# Application Entry Point
# ====================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  E-Learning Course Analytics System")
    print(f"  Starting Flask server on port {config.FLASK_PORT}")
    print(f"  Access dashboard at: http://127.0.0.1:{config.FLASK_PORT}")
    print("=" * 70)
    # threaded=True allows concurrent request processing without serial queuing
    # use_reloader=False avoids creating zombie orphan processes on Windows
    # Binding to 0.0.0.0 allows access via both 127.0.0.1 and localhost
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=False, threaded=True, use_reloader=False)
