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
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, Response,
    send_from_directory, session, redirect, url_for, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error, errorcode

import config
import analytics

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["JSON_SORT_KEYS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Setup logger
logger = logging.getLogger("app")

# Auto-verify users table on startup
try:
    config.ensure_auth_table()
except Exception as _e:
    logger.warning("Could not auto-verify users table on startup: %s", _e)


# Context processor injects the permanently locked theme & active user into all rendered templates
@app.context_processor
def inject_global_settings():
    user_id = session.get("user_id")
    return {
        "active_theme": config.get_app_theme(),
        "current_user": {
            "id": user_id,
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "email": session.get("email"),
            "role": session.get("role", "Administrator"),
            "is_authenticated": bool(user_id)
        }
    }


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
        "/api/settings/theme"
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
                if request.path in ["/api/health", "/api/settings/theme"]:
                    return f(*args, **kwargs)
                return jsonify({
                    "success": False,
                    "message": "Authentication required. Please sign in."
                }), 401
            return redirect(url_for("page_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# API endpoint to persist theme server-wide across all devices
@app.route("/api/settings/theme", methods=["GET", "POST"])
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
                SELECT a.activity_id, a.activity_type, a.score, a.time_spent_minutes, a.activity_date,
                       l.name AS learner_name, c.course_name
                FROM activities a
                JOIN enrollments e ON a.enrollment_id = e.enrollment_id
                JOIN learners l ON e.learner_id = l.learner_id
                JOIN courses c ON e.course_id = c.course_id
                ORDER BY a.activity_date DESC, a.activity_id DESC
                LIMIT 5;
            """)
            recent_activities = cursor.fetchall()

            cursor.execute("""
                SELECT c.course_id, c.course_name, c.category,
                       COUNT(e.enrollment_id) AS total_enrolled,
                       SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count
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
    """Returns top summary metrics for dashboard cards."""
    data = analytics.get_dashboard_summary()
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/course-completion", methods=["GET"])
def api_analytics_course_completion():
    """Returns per-course completion statistics for bar charts."""
    data = analytics.get_course_completion_analytics()
    return jsonify({"success": True, "data": data})


@app.route("/api/analytics/weekly-activity", methods=["GET"])
def api_analytics_weekly_activity():
    """Returns weekly aggregated learning activity counts."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = analytics.get_weekly_activity_analytics(start_date=start_date, end_date=end_date)
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


# ====================================================================
# Course Management APIs
# ====================================================================

@app.route("/api/courses", methods=["GET"])
def api_get_courses():
    """Lists courses with optional search by course name or category."""
    search = request.args.get("search", "").strip()
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        if search:
            query = """
                SELECT c.*, COUNT(e.enrollment_id) AS enrollment_count
                FROM courses c
                LEFT JOIN enrollments e ON c.course_id = e.course_id
                WHERE c.course_name LIKE %s OR c.category LIKE %s
                GROUP BY c.course_id
                ORDER BY c.course_id DESC;
            """
            wildcard = f"%{search}%"
            cursor.execute(query, (wildcard, wildcard))
        else:
            query = """
                SELECT c.*, COUNT(e.enrollment_id) AS enrollment_count
                FROM courses c
                LEFT JOIN enrollments e ON c.course_id = e.course_id
                GROUP BY c.course_id
                ORDER BY c.course_id DESC;
            """
            cursor.execute(query)

        courses = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": courses})
    except Error as e:
        logger.error("Error fetching courses: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve courses."}), 500


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def api_get_course_detail(course_id):
    """Retrieve details for a single course."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        course = cursor.fetchone()
        cursor.close()
        conn.close()

        if not course:
            return jsonify({"success": False, "message": "Course not found."}), 404
        return jsonify({"success": True, "data": course})
    except Error as e:
        logger.error("Error fetching course detail: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve course detail."}), 500


@app.route("/api/courses", methods=["POST"])
def api_create_course():
    """Create a new course."""
    payload = request.get_json(silent=True) or {}
    course_name = (payload.get("course_name") or "").strip()
    category = (payload.get("category") or "").strip()

    if not course_name or not category:
        return jsonify({"success": False, "message": "Course name and category are required."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO courses (course_name, category) VALUES (%s, %s)"
        cursor.execute(query, (course_name, category))
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Course created successfully.",
            "data": {"course_id": new_id, "course_name": course_name, "category": category}
        }), 201
    except Error as e:
        logger.error("Error creating course: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to create course."}), 500


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def api_update_course(course_id):
    """Update an existing course."""
    payload = request.get_json(silent=True) or {}
    course_name = (payload.get("course_name") or "").strip()
    category = (payload.get("category") or "").strip()

    if not course_name or not category:
        return jsonify({"success": False, "message": "Course name and category are required."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Check course exists
        cursor.execute("SELECT course_id FROM courses WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Course not found."}), 404

        query = "UPDATE courses SET course_name = %s, category = %s WHERE course_id = %s"
        cursor.execute(query, (course_name, category, course_id))
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Course updated successfully.",
            "data": {"course_id": course_id, "course_name": course_name, "category": category}
        })
    except Error as e:
        logger.error("Error updating course: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to update course."}), 500


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def api_delete_course(course_id):
    """Delete a course. Prevents deletion if existing enrollments are attached."""
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        # Check if course exists
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
    """Lists learners with optional search by roll number."""
    search = request.args.get("search", "").strip()
    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        if search:
            query = """
                SELECT l.*, COUNT(e.enrollment_id) AS enrollment_count
                FROM learners l
                LEFT JOIN enrollments e ON l.learner_id = e.learner_id
                WHERE l.roll_no LIKE %s
                GROUP BY l.learner_id
                ORDER BY l.learner_id DESC;
            """
            cursor.execute(query, (f"%{search}%",))
        else:
            query = """
                SELECT l.*, COUNT(e.enrollment_id) AS enrollment_count
                FROM learners l
                LEFT JOIN enrollments e ON l.learner_id = e.learner_id
                GROUP BY l.learner_id
                ORDER BY l.learner_id DESC;
            """
            cursor.execute(query)

        learners = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": learners})
    except Error as e:
        logger.error("Error fetching learners: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve learners."}), 500


@app.route("/api/learners", methods=["POST"])
def api_create_learner():
    """Register a new learner with a unique roll number."""
    payload = request.get_json(silent=True) or {}
    roll_no = (payload.get("roll_no") or "").strip().upper()

    if not roll_no:
        return jsonify({"success": False, "message": "Roll number is required."}), 400

    conn = config.get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    try:
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO learners (roll_no) VALUES (%s)"
        cursor.execute(query, (roll_no,))
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Learner registered successfully.",
            "data": {"learner_id": new_id, "roll_no": roll_no}
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
def api_update_learner(learner_id):
    """Update learner roll number."""
    payload = request.get_json(silent=True) or {}
    roll_no = (payload.get("roll_no") or "").strip().upper()

    if not roll_no:
        return jsonify({"success": False, "message": "Roll number is required."}), 400

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

        cursor.execute("UPDATE learners SET roll_no = %s WHERE learner_id = %s", (roll_no, learner_id))
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Learner updated successfully.",
            "data": {"learner_id": learner_id, "roll_no": roll_no}
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
        if start_date:
            where_clauses.append("a.activity_date >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            where_clauses.append("a.activity_date <= %s")
            params.append(f"{end_date} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                a.activity_id,
                a.enrollment_id,
                a.activity_type,
                a.completed,
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

        return jsonify({"success": True, "data": activities})
    except Error as e:
        logger.error("Error fetching activities: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return jsonify({"success": False, "message": "Failed to retrieve activities."}), 500


@app.route("/api/activities", methods=["POST"])
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

    if not enrollment_id or not activity_type:
        return jsonify({"success": False, "message": "Enrollment ID and Activity Type are required."}), 400

    if activity_type not in ALLOWED_ACTIVITY_TYPES:
        return jsonify({
            "success": False,
            "message": f"Invalid activity type '{activity_type}'. Allowed types: {', '.join(ALLOWED_ACTIVITY_TYPES)}"
        }), 400

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
                INSERT INTO activities (enrollment_id, activity_type, completed, activity_date)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(query, (enrollment_id, activity_type, completed, activity_date))
        else:
            query = """
                INSERT INTO activities (enrollment_id, activity_type, completed, activity_date)
                VALUES (%s, %s, %s, NOW());
            """
            cursor.execute(query, (enrollment_id, activity_type, completed))

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

def generate_csv_response(filename, fieldnames, rows):
    """
    Helper function to build a standardized, sanitized CSV response.
    Saves a copy into exports/ and streams attachment to client.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{filename}_{timestamp}.csv"

    # Write to memory stream
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    csv_content = output.getvalue()
    output.close()

    # Also save a copy in the exports directory safely
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


@app.route("/api/reports/course-completion.csv", methods=["GET"])
def export_course_completion_csv():
    """Download Course Completion Report as CSV."""
    data = analytics.get_course_completion_analytics()
    fieldnames = [
        "course_id", "course_name", "category",
        "total_enrollments", "completed_enrollments",
        "in_progress_enrollments", "enrolled_enrollments",
        "completion_rate", "performance_status"
    ]
    # Filter only desired export columns
    rows = []
    for item in data:
        rows.append({k: item.get(k) for k in fieldnames})

    return generate_csv_response("course_completion_report", fieldnames, rows)


@app.route("/api/reports/inactive-enrollments.csv", methods=["GET"])
def export_inactive_enrollments_csv():
    """Download Inactive Enrollments Report as CSV."""
    threshold = request.args.get("threshold", default=config.INACTIVITY_DAYS_THRESHOLD, type=int)
    data = analytics.get_inactive_enrollments(threshold_days=threshold)
    fieldnames = [
        "enrollment_id", "roll_no", "course_name", "category",
        "enrolled_at", "last_activity_date", "days_since_last_activity",
        "status", "inactivity_reason"
    ]
    rows = []
    for item in data:
        rows.append({k: item.get(k) for k in fieldnames})

    return generate_csv_response("inactive_enrollments_report", fieldnames, rows)


@app.route("/api/reports/weekly-activity.csv", methods=["GET"])
def export_weekly_activity_csv():
    """Download Weekly Learning Activity Report as CSV."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    data = analytics.get_weekly_activity_analytics(start_date=start_date, end_date=end_date)
    fieldnames = ["week_start", "week_label", "iso_week", "total", "completed", "incomplete"]
    rows = []
    for item in data:
        rows.append({k: item.get(k) for k in fieldnames})

    return generate_csv_response("weekly_activity_report", fieldnames, rows)


@app.route("/api/reports/course-comparison.csv", methods=["GET"])
def export_course_comparison_csv():
    """Download Course Comparison Report as CSV."""
    data = analytics.get_course_comparison()
    fieldnames = [
        "course_id", "course_name", "category",
        "total_enrollments", "completed_enrollments", "in_progress_enrollments",
        "total_activities", "completed_activities", "avg_activities_per_learner",
        "completion_rate", "performance_status"
    ]
    rows = []
    for item in data:
        rows.append({k: item.get(k) for k in fieldnames})

    return generate_csv_response("course_comparison_report", fieldnames, rows)


@app.route("/api/reports/generate-charts", methods=["POST"])
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
