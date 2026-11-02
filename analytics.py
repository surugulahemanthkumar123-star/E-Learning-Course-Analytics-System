"""
====================================================================
E-Learning Course Analytics System - Analytics Engine
File: analytics.py
Performs computational analysis using MySQL, Pandas, NumPy, and
Matplotlib for course completion rates, weekly trend aggregation,
and inactive enrollment detection.
Includes resilient dual-engine processing with native Python/NumPy
fallback if platform security policies restrict Pandas C-extensions.
====================================================================
"""

import os
import logging
import warnings
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logger = logging.getLogger("analytics")

# Suppress DBAPI2 deprecation user-warning from Pandas while preserving full functionality
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pandas.*")

# Optional Pandas import with graceful fallback
try:
    import pandas as pd
    HAS_PANDAS = True
except (ImportError, Exception) as pe:
    logger.warning("Pandas C-extension unavailable (%s); using native NumPy & datetime processing engine.", pe)
    pd = None
    HAS_PANDAS = False

# NumPy import
try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, Exception) as ne:
    logger.warning("NumPy unavailable (%s); using standard math functions.", ne)
    np = None
    HAS_NUMPY = False

# Matplotlib with headless Agg backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def classify_performance(rate, total_enrollments):
    """
    Classifies course performance based on completion percentage.
    Thresholds:
      - Total enrollments == 0: 'No Enrollments' (secondary)
      - Rate >= 75%: 'Excellent' (success)
      - Rate >= 50%: 'Good' (primary)
      - Rate >= 25%: 'Average' (warning)
      - Rate < 25%:  'Needs Attention' (danger)
    """
    if total_enrollments == 0:
        return "No Enrollments", "secondary"
    if rate >= 75.0:
        return "Excellent", "success"
    if rate >= 50.0:
        return "Good", "primary"
    if rate >= 25.0:
        return "Average", "warning"
    return "Needs Attention", "danger"


def get_dashboard_summary(course_id=None, start_date=None, end_date=None):
    """
    Calculates summary card figures across the entire platform or filtered by
    course_id and date range (start_date, end_date).
    Ensures safe handling of empty database states.
    """
    conn = config.get_db_connection()
    if not conn:
        return {
            "total_courses": 0,
            "total_learners": 0,
            "total_enrollments": 0,
            "completed_enrollments": 0,
            "in_progress_enrollments": 0,
            "overall_completion_rate": 0.0,
            "inactive_enrollments": 0,
            "total_activities": 0,
            "average_score": None,
            "total_time_spent_minutes": None,
            "active_learners_count": 0,
            "database_connected": False
        }

    try:
        cursor = conn.cursor(dictionary=True)

        if course_id:
            total_courses = 1
            cursor.execute("SELECT COUNT(DISTINCT learner_id) AS cnt FROM enrollments WHERE course_id = %s", (course_id,))
            total_learners = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE course_id = %s", (course_id,))
            total_enrollments = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE course_id = %s AND status = 'Completed'", (course_id,))
            completed_enrollments = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE course_id = %s AND status = 'In Progress'", (course_id,))
            in_progress_enrollments = cursor.fetchone()["count"]
        else:
            cursor.execute("SELECT COUNT(*) AS count FROM courses")
            total_courses = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM learners")
            total_learners = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments")
            total_enrollments = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE status = 'Completed'")
            completed_enrollments = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) AS count FROM enrollments WHERE status = 'In Progress'")
            in_progress_enrollments = cursor.fetchone()["count"]

        # Calculate overall completion rate without averaging course percentages
        if total_enrollments > 0:
            overall_rate = round((completed_enrollments / total_enrollments) * 100.0, 1)
        else:
            overall_rate = 0.0

        # Activity Telemetry with optional course and date range filtering
        act_where = []
        act_params = []
        if course_id:
            act_where.append("e.course_id = %s")
            act_params.append(course_id)
        if start_date:
            act_where.append("a.activity_date >= %s")
            act_params.append(f"{start_date} 00:00:00")
        if end_date:
            act_where.append("a.activity_date <= %s")
            act_params.append(f"{end_date} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(act_where)) if act_where else ""

        # Total activities
        query_acts = f"""
            SELECT COUNT(a.activity_id) AS count
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_sql}
        """
        cursor.execute(query_acts, tuple(act_params))
        total_activities = cursor.fetchone()["count"]

        # Average score
        where_score = list(act_where)
        where_score.append("a.score IS NOT NULL")
        where_score_sql = "WHERE " + " AND ".join(where_score)
        query_score = f"""
            SELECT AVG(a.score) AS avg_score
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_score_sql}
        """
        cursor.execute(query_score, tuple(act_params))
        score_row = cursor.fetchone()
        avg_score = round(float(score_row["avg_score"]), 1) if score_row and score_row["avg_score"] is not None else None

        # Total study time
        where_time = list(act_where)
        where_time.append("a.time_spent_minutes IS NOT NULL")
        where_time_sql = "WHERE " + " AND ".join(where_time)
        query_time = f"""
            SELECT SUM(a.time_spent_minutes) AS total_time
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_time_sql}
        """
        cursor.execute(query_time, tuple(act_params))
        time_row = cursor.fetchone()
        total_time_spent = int(time_row["total_time"]) if time_row and time_row["total_time"] is not None else None

        # Active learners
        where_active = list(act_where)
        where_active.append("a.activity_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        where_active_sql = "WHERE " + " AND ".join(where_active)
        query_active = f"""
            SELECT COUNT(DISTINCT e.learner_id) AS cnt
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_active_sql}
        """
        cursor.execute(query_active, tuple(act_params))
        active_learners_row = cursor.fetchone()
        active_learners_count = int(active_learners_row["cnt"]) if active_learners_row else 0

        # Calculate inactive enrollments count using the threshold
        inactive_list = get_inactive_enrollments(config.INACTIVITY_DAYS_THRESHOLD)
        if course_id:
            inactive_list = [i for i in inactive_list if i.get("course_id") == course_id]
        inactive_count = len(inactive_list)

        cursor.close()
        conn.close()

        return {
            "total_courses": total_courses,
            "total_learners": total_learners,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "in_progress_enrollments": in_progress_enrollments,
            "overall_completion_rate": overall_rate,
            "inactive_enrollments": inactive_count,
            "total_activities": total_activities,
            "average_score": avg_score,
            "total_time_spent_minutes": total_time_spent,
            "active_learners_count": active_learners_count,
            "database_connected": True
        }
    except Exception as e:
        logger.error("Error in get_dashboard_summary: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return {
            "total_courses": 0,
            "total_learners": 0,
            "total_enrollments": 0,
            "completed_enrollments": 0,
            "in_progress_enrollments": 0,
            "overall_completion_rate": 0.0,
            "inactive_enrollments": 0,
            "database_connected": False,
            "error": str(e)
        }


def get_course_completion_analytics(course_id=None):
    """
    Computes per-course enrollment numbers and completion percentages.
    Uses Pandas DataFrame when available, or native MySQL aggregation.
    Supports optional course_id filtering.
    """
    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        where_sql = "WHERE c.course_id = %s" if course_id else ""
        params = (course_id,) if course_id else None

        query = f"""
            SELECT 
                c.course_id,
                c.course_name,
                c.category,
                COUNT(e.enrollment_id) AS total_enrollments,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_enrollments,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_enrollments,
                SUM(CASE WHEN e.status = 'Enrolled' THEN 1 ELSE 0 END) AS just_enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            {where_sql}
            GROUP BY c.course_id, c.course_name, c.category
            ORDER BY c.course_name ASC;
        """

        if HAS_PANDAS:
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            if df.empty:
                return []

            df["total_enrollments"] = df["total_enrollments"].fillna(0).astype(int)
            df["completed_enrollments"] = df["completed_enrollments"].fillna(0).astype(int)
            df["in_progress_enrollments"] = df["in_progress_enrollments"].fillna(0).astype(int)
            df["just_enrolled"] = df["just_enrolled"].fillna(0).astype(int)

            if HAS_NUMPY:
                df["completion_rate"] = np.where(
                    df["total_enrollments"] > 0,
                    np.round((df["completed_enrollments"] / df["total_enrollments"]) * 100.0, 1),
                    0.0
                )
            else:
                df["completion_rate"] = df.apply(
                    lambda r: round((r["completed_enrollments"] / r["total_enrollments"]) * 100.0, 1)
                    if r["total_enrollments"] > 0 else 0.0, axis=1
                )

            results = []
            for _, row in df.iterrows():
                total = int(row["total_enrollments"])
                rate = float(row["completion_rate"])
                status_label, badge_color = classify_performance(rate, total)
                results.append({
                    "course_id": int(row["course_id"]),
                    "course_name": row["course_name"],
                    "category": row["category"],
                    "total_enrollments": total,
                    "completed_enrollments": int(row["completed_enrollments"]),
                    "in_progress_enrollments": int(row["in_progress_enrollments"]),
                    "enrolled_enrollments": int(row["just_enrolled"]),
                    "completion_rate": rate,
                    "performance_status": status_label,
                    "badge_color": badge_color
                })
            return results

        # Native Python & SQL Cursor Engine
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for r in rows:
            total = int(r["total_enrollments"] or 0)
            completed = int(r["completed_enrollments"] or 0)
            in_prog = int(r["in_progress_enrollments"] or 0)
            enrolled = int(r["just_enrolled"] or 0)
            rate = round((completed / total) * 100.0, 1) if total > 0 else 0.0
            status_label, badge_color = classify_performance(rate, total)

            results.append({
                "course_id": int(r["course_id"]),
                "course_name": r["course_name"],
                "category": r["category"],
                "total_enrollments": total,
                "completed_enrollments": completed,
                "in_progress_enrollments": in_prog,
                "enrolled_enrollments": enrolled,
                "completion_rate": rate,
                "performance_status": status_label,
                "badge_color": badge_color
            })
        return results

    except Exception as e:
        logger.error("Error in get_course_completion_analytics: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_course_comparison():
    """
    Produces detailed comparison metrics including total logged activities
    and average activities per enrolled learner.
    """
    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        query = """
            SELECT 
                c.course_id,
                c.course_name,
                c.category,
                COUNT(DISTINCT e.enrollment_id) AS total_enrollments,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_enrollments,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_enrollments,
                COUNT(a.activity_id) AS total_activities,
                SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) AS completed_activities
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            GROUP BY c.course_id, c.course_name, c.category
            ORDER BY completed_enrollments DESC, total_enrollments DESC;
        """

        if HAS_PANDAS:
            df = pd.read_sql_query(query, conn)
            conn.close()
            if df.empty:
                return []

            df["total_enrollments"] = df["total_enrollments"].fillna(0).astype(int)
            df["completed_enrollments"] = df["completed_enrollments"].fillna(0).astype(int)
            df["in_progress_enrollments"] = df["in_progress_enrollments"].fillna(0).astype(int)
            df["total_activities"] = df["total_activities"].fillna(0).astype(int)
            df["completed_activities"] = df["completed_activities"].fillna(0).astype(int)

            if HAS_NUMPY:
                df["completion_rate"] = np.where(
                    df["total_enrollments"] > 0,
                    np.round((df["completed_enrollments"] / df["total_enrollments"]) * 100.0, 1),
                    0.0
                )
                df["avg_activities"] = np.where(
                    df["total_enrollments"] > 0,
                    np.round(df["total_activities"] / df["total_enrollments"], 1),
                    0.0
                )
            else:
                df["completion_rate"] = df.apply(
                    lambda r: round((r["completed_enrollments"] / r["total_enrollments"]) * 100.0, 1)
                    if r["total_enrollments"] > 0 else 0.0, axis=1
                )
                df["avg_activities"] = df.apply(
                    lambda r: round(r["total_activities"] / r["total_enrollments"], 1)
                    if r["total_enrollments"] > 0 else 0.0, axis=1
                )

            comparison = []
            for _, row in df.iterrows():
                total = int(row["total_enrollments"])
                rate = float(row["completion_rate"])
                status_label, badge_color = classify_performance(rate, total)
                comparison.append({
                    "course_id": int(row["course_id"]),
                    "course_name": row["course_name"],
                    "category": row["category"],
                    "total_enrollments": total,
                    "completed_enrollments": int(row["completed_enrollments"]),
                    "in_progress_enrollments": int(row["in_progress_enrollments"]),
                    "total_activities": int(row["total_activities"]),
                    "completed_activities": int(row["completed_activities"]),
                    "avg_activities_per_learner": float(row["avg_activities"]),
                    "completion_rate": rate,
                    "performance_status": status_label,
                    "badge_color": badge_color
                })
            return comparison

        # Native Python & SQL Cursor Engine
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        comparison = []
        for r in rows:
            total = int(r["total_enrollments"] or 0)
            completed = int(r["completed_enrollments"] or 0)
            in_prog = int(r["in_progress_enrollments"] or 0)
            tot_act = int(r["total_activities"] or 0)
            comp_act = int(r["completed_activities"] or 0)

            rate = round((completed / total) * 100.0, 1) if total > 0 else 0.0
            avg_act = round(tot_act / total, 1) if total > 0 else 0.0
            status_label, badge_color = classify_performance(rate, total)

            comparison.append({
                "course_id": int(r["course_id"]),
                "course_name": r["course_name"],
                "category": r["category"],
                "total_enrollments": total,
                "completed_enrollments": completed,
                "in_progress_enrollments": in_prog,
                "total_activities": tot_act,
                "completed_activities": comp_act,
                "avg_activities_per_learner": avg_act,
                "completion_rate": rate,
                "performance_status": status_label,
                "badge_color": badge_color
            })
        return comparison

    except Exception as e:
        logger.error("Error in get_course_comparison: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_weekly_activity_analytics(start_date=None, end_date=None):
    """
    Aggregates learning activities chronologically by calendar week.
    Counts total, completed, and incomplete activities.
    """
    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        params = []
        where_clauses = []

        if start_date:
            where_clauses.append("activity_date >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            where_clauses.append("activity_date <= %s")
            params.append(f"{end_date} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                activity_id,
                activity_date,
                activity_type,
                completed
            FROM activities
            {where_sql}
            ORDER BY activity_date ASC;
        """

        if HAS_PANDAS:
            df = pd.read_sql_query(query, conn, params=params if params else None)
            conn.close()

            if df.empty:
                return []

            df["activity_date"] = pd.to_datetime(df["activity_date"])
            df["week_start"] = df["activity_date"].dt.to_period("W-SUN").apply(lambda r: r.start_time)
            df["completed_int"] = df["completed"].astype(int)
            df["incomplete_int"] = (1 - df["completed_int"]).astype(int)

            grouped = df.groupby("week_start").agg(
                total=("activity_id", "count"),
                completed=("completed_int", "sum"),
                incomplete=("incomplete_int", "sum")
            ).reset_index().sort_values(by="week_start", ascending=True)

            weekly_results = []
            for _, row in grouped.iterrows():
                week_dt = row["week_start"]
                weekly_results.append({
                    "week_start": week_dt.strftime("%Y-%m-%d"),
                    "week_label": week_dt.strftime("Week of %b %d, %Y"),
                    "iso_week": week_dt.strftime("%Y-W%U"),
                    "total": int(row["total"]),
                    "completed": int(row["completed"]),
                    "incomplete": int(row["incomplete"])
                })
            return weekly_results

        # Native Python datetime aggregation
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(params) if params else None)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return []

        weekly_buckets = defaultdict(lambda: {"total": 0, "completed": 0, "incomplete": 0})
        for r in rows:
            dt = r["activity_date"]
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            # Find the Monday of that calendar week
            monday = dt - timedelta(days=dt.weekday())
            week_date = monday.date()

            weekly_buckets[week_date]["total"] += 1
            if r["completed"]:
                weekly_buckets[week_date]["completed"] += 1
            else:
                weekly_buckets[week_date]["incomplete"] += 1

        weekly_results = []
        for week_date in sorted(weekly_buckets.keys()):
            data = weekly_buckets[week_date]
            weekly_results.append({
                "week_start": week_date.strftime("%Y-%m-%d"),
                "week_label": week_date.strftime("Week of %b %d, %Y"),
                "iso_week": week_date.strftime("%Y-W%U"),
                "total": data["total"],
                "completed": data["completed"],
                "incomplete": data["incomplete"]
            })
        return weekly_results

    except Exception as e:
        logger.error("Error in get_weekly_activity_analytics: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_inactive_enrollments(threshold_days=None):
    """
    Identifies enrollments that are not 'Completed' and either:
      1. Have recorded NO learning activities, OR
      2. Their most recent activity is older than threshold_days (default: 14 days).
    Uses GROUP BY on enrollment to prevent duplicate rows.
    """
    if threshold_days is None:
        threshold_days = config.INACTIVITY_DAYS_THRESHOLD

    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        query = """
            SELECT 
                e.enrollment_id,
                e.learner_id,
                l.roll_no,
                e.course_id,
                c.course_name,
                c.category,
                e.enrolled_at,
                e.status,
                MAX(a.activity_date) AS last_activity_date,
                DATEDIFF(NOW(), MAX(a.activity_date)) AS days_since_last_activity,
                DATEDIFF(NOW(), e.enrolled_at) AS days_since_enrolled,
                COUNT(a.activity_id) AS total_activities_logged
            FROM enrollments e
            JOIN learners l ON e.learner_id = l.learner_id
            JOIN courses c ON e.course_id = c.course_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            WHERE e.status != 'Completed'
            GROUP BY 
                e.enrollment_id, 
                e.learner_id, 
                l.roll_no, 
                e.course_id, 
                c.course_name, 
                c.category, 
                e.enrolled_at, 
                e.status
            HAVING (last_activity_date IS NULL AND days_since_enrolled > %s)
                OR (last_activity_date IS NOT NULL AND days_since_last_activity > %s)
            ORDER BY 
                CASE WHEN last_activity_date IS NULL THEN 1 ELSE 0 END DESC,
                days_since_last_activity DESC,
                e.enrolled_at ASC;
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (threshold_days, threshold_days))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for r in rows:
            last_date = r["last_activity_date"]
            days_inactive = r["days_since_last_activity"]

            if last_date is None:
                last_activity_str = "No activity recorded"
                days_display = int(r["days_since_enrolled"]) if r["days_since_enrolled"] is not None else 0
                reason = f"No activity recorded in {days_display} days since enrollment"
            else:
                last_activity_str = last_date.strftime("%Y-%m-%d %H:%M")
                days_display = int(days_inactive) if days_inactive is not None else 0
                reason = f"Inactive for {days_display} days (threshold: {threshold_days} days)"

            results.append({
                "enrollment_id": r["enrollment_id"],
                "learner_id": r["learner_id"],
                "roll_no": r["roll_no"],
                "course_id": r["course_id"],
                "course_name": r["course_name"],
                "category": r["category"],
                "enrolled_at": r["enrolled_at"].strftime("%Y-%m-%d") if r["enrolled_at"] else "Unknown",
                "last_activity_date": last_activity_str,
                "days_since_last_activity": days_display,
                "status": r["status"],
                "total_activities_logged": r["total_activities_logged"],
                "inactivity_reason": reason
            })

        return results
    except Exception as e:
        logger.error("Error in get_inactive_enrollments: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_learner_performance_analytics(search=None, department=None):
    """
    Computes comprehensive academic performance telemetry for each learner.
    Includes course completion, activities volume, average scores (or None),
    and learning duration (or None).
    Uses parameterized SQL and clean fallback.
    """
    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if department:
            where_clauses.append("l.department = %s")
            params.append(department)
        if search:
            where_clauses.append("(l.roll_no LIKE %s OR l.name LIKE %s OR l.email LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                l.learner_id,
                l.roll_no,
                l.name,
                l.email,
                l.department,
                l.created_at,
                COUNT(DISTINCT e.enrollment_id) AS enrolled_courses_count,
                COUNT(DISTINCT CASE WHEN e.status = 'Completed' THEN e.enrollment_id END) AS completed_courses_count,
                COUNT(DISTINCT CASE WHEN e.status = 'In Progress' THEN e.enrollment_id END) AS in_progress_courses_count,
                COUNT(DISTINCT a.activity_id) AS total_activities_logged,
                COUNT(DISTINCT CASE WHEN a.completed = 1 THEN a.activity_id END) AS completed_activities_count,
                AVG(a.score) AS average_score,
                SUM(a.time_spent_minutes) AS total_time_spent_minutes,
                MAX(a.activity_date) AS last_active_date
            FROM learners l
            LEFT JOIN enrollments e ON l.learner_id = e.learner_id
            LEFT JOIN activities a ON e.enrollment_id = a.enrollment_id
            {where_sql}
            GROUP BY l.learner_id, l.roll_no, l.name, l.email, l.department, l.created_at
            ORDER BY completed_courses_count DESC, total_activities_logged DESC, l.roll_no ASC;
        """
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for r in rows:
            enrolled = int(r["enrolled_courses_count"] or 0)
            completed_c = int(r["completed_courses_count"] or 0)
            comp_rate = round((completed_c / enrolled) * 100.0, 1) if enrolled > 0 else 0.0

            avg_score = round(float(r["average_score"]), 1) if r["average_score"] is not None else None
            tot_time = int(r["total_time_spent_minutes"]) if r["total_time_spent_minutes"] is not None else None
            last_date = r["last_active_date"].strftime("%Y-%m-%d %H:%M") if r.get("last_active_date") else None

            # Academic Engagement Status
            if enrolled == 0:
                engagement_status = "Unenrolled"
                badge_class = "badge-soft-secondary"
            elif completed_c == enrolled:
                engagement_status = "Completed All"
                badge_class = "badge-soft-success"
            elif r["total_activities_logged"] == 0:
                engagement_status = "Inactive"
                badge_class = "badge-soft-danger"
            elif comp_rate >= 50.0:
                engagement_status = "On Track"
                badge_class = "badge-soft-primary"
            else:
                engagement_status = "Needs Attention"
                badge_class = "badge-soft-warning"

            results.append({
                "learner_id": r["learner_id"],
                "roll_no": r["roll_no"],
                "name": r["name"],
                "email": r["email"],
                "department": r["department"],
                "enrolled_courses_count": enrolled,
                "completed_courses_count": completed_c,
                "in_progress_courses_count": int(r["in_progress_courses_count"] or 0),
                "completion_rate": comp_rate,
                "total_activities_logged": int(r["total_activities_logged"] or 0),
                "completed_activities_count": int(r["completed_activities_count"] or 0),
                "average_score": avg_score,
                "total_time_spent_minutes": tot_time,
                "last_active_date": last_date,
                "engagement_status": engagement_status,
                "badge_class": badge_class
            })
        return results
    except Exception as e:
        logger.error("Error in get_learner_performance_analytics: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_activity_participation_analytics(course_id=None, start_date=None, end_date=None):
    """
    Computes activity engagement metrics broken down by activity_type.
    Calculates total volume, completion count, average score, and total duration.
    """
    conn = config.get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []

        if course_id:
            where_clauses.append("e.course_id = %s")
            params.append(course_id)
        if start_date:
            where_clauses.append("a.activity_date >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            where_clauses.append("a.activity_date <= %s")
            params.append(f"{end_date} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                a.activity_type,
                COUNT(a.activity_id) AS total_count,
                SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) AS completed_count,
                SUM(CASE WHEN a.completed = 0 THEN 1 ELSE 0 END) AS pending_count,
                AVG(a.score) AS average_score,
                SUM(a.time_spent_minutes) AS total_time_spent_minutes
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_sql}
            GROUP BY a.activity_type
            ORDER BY total_count DESC;
        """
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        total_all = sum(r["total_count"] for r in rows) or 1
        results = []
        for r in rows:
            tot = int(r["total_count"])
            comp = int(r["completed_count"] or 0)
            rate = round((comp / tot) * 100.0, 1) if tot > 0 else 0.0
            pct_of_total = round((tot / total_all) * 100.0, 1)
            avg_s = round(float(r["average_score"]), 1) if r["average_score"] is not None else None
            tot_t = int(r["total_time_spent_minutes"]) if r["total_time_spent_minutes"] is not None else None

            results.append({
                "activity_type": r["activity_type"],
                "total_count": tot,
                "completed_count": comp,
                "pending_count": int(r["pending_count"] or 0),
                "completion_rate": rate,
                "percentage_of_all_activities": pct_of_total,
                "average_score": avg_s,
                "total_time_spent_minutes": tot_t
            })
        return results
    except Exception as e:
        logger.error("Error in get_activity_participation_analytics: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return []


def get_score_and_time_trends(course_id=None, start_date=None, end_date=None):
    """
    Returns time-series telemetry for activity counts, average score, and learning time.
    Honestly indicates whether numerical score and duration data exists in the database.
    Supports optional course_id, start_date, and end_date filtering.
    """
    conn = config.get_db_connection()
    if not conn:
        return {"has_score_data": False, "has_time_data": False, "trends": []}

    try:
        cursor = conn.cursor(dictionary=True)
        where_clauses = []
        params = []
        if course_id:
            where_clauses.append("e.course_id = %s")
            params.append(course_id)
        if start_date:
            where_clauses.append("a.activity_date >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            where_clauses.append("a.activity_date <= %s")
            params.append(f"{end_date} 23:59:59")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = f"""
            SELECT 
                DATE(a.activity_date) AS activity_day,
                COUNT(a.activity_id) AS total_activities,
                SUM(CASE WHEN a.completed = 1 THEN 1 ELSE 0 END) AS completed_activities,
                AVG(a.score) AS avg_score,
                SUM(a.time_spent_minutes) AS total_time
            FROM activities a
            JOIN enrollments e ON a.enrollment_id = e.enrollment_id
            {where_sql}
            GROUP BY DATE(a.activity_date)
            ORDER BY activity_day ASC;
        """
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        has_score = any(r["avg_score"] is not None for r in rows)
        has_time = any(r["total_time"] is not None for r in rows)

        trends = []
        for r in rows:
            trends.append({
                "date": r["activity_day"].strftime("%Y-%m-%d") if r.get("activity_day") else "Unknown",
                "total_activities": int(r["total_activities"]),
                "completed_activities": int(r["completed_activities"] or 0),
                "average_score": round(float(r["avg_score"]), 1) if r["avg_score"] is not None else None,
                "total_time_minutes": int(r["total_time"]) if r["total_time"] is not None else None
            })

        return {
            "has_score_data": has_score,
            "has_time_data": has_time,
            "trends": trends
        }
    except Exception as e:
        logger.error("Error in get_score_and_time_trends: %s", e)
        if conn and conn.is_connected():
            conn.close()
        return {"has_score_data": False, "has_time_data": False, "trends": []}


def generate_analytics_charts(output_dir=None):
    """
    Generates backend Matplotlib charts saved as PNG images in static/charts/.
    Produces:
      1. course_completion_bar.png
      2. weekly_activity_trend.png
      3. activity_type_distribution.png
      4. course_engagement_comparison.png
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "static", "charts")

    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    # Chart 1: Course Completion Rates Bar Chart
    courses_data = get_course_completion_analytics()
    if courses_data:
        try:
            fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
            names = [c["course_name"][:20] + ("..." if len(c["course_name"]) > 20 else "") for c in courses_data]
            rates = [c["completion_rate"] for c in courses_data]
            colors = ["#198754" if r >= 75 else "#0d6efd" if r >= 50 else "#ffc107" if r >= 25 else "#dc3545" for r in rates]

            bars = ax.bar(names, rates, color=colors, width=0.55, edgecolor="#333333", linewidth=0.8)
            ax.set_title("Course Completion Rates (%)", fontsize=14, fontweight="bold", pad=15, color="#1a2530")
            ax.set_ylabel("Completion Rate (%)", fontsize=11, fontweight="bold")
            ax.set_ylim(0, 105)
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            plt.xticks(rotation=25, ha="right", fontsize=9)

            for bar in bars:
                height = bar.get_height()
                ax.annotate(f"{height:.1f}%",
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, fontweight="bold")

            plt.tight_layout()
            chart1_path = os.path.join(output_dir, "course_completion_bar.png")
            fig.savefig(chart1_path, format="png")
            plt.close(fig)
            generated_files.append("course_completion_bar.png")
        except Exception as e:
            logger.error("Failed to generate course completion chart: %s", e)

    # Chart 2: Weekly Activity Trend Line Chart
    weekly_data = get_weekly_activity_analytics()
    if weekly_data:
        try:
            fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
            labels = [w["week_label"].replace("Week of ", "") for w in weekly_data]
            totals = [w["total"] for w in weekly_data]
            completed = [w["completed"] for w in weekly_data]

            ax.plot(labels, totals, marker="o", color="#0d6efd", linewidth=2.5, label="Total Activities")
            ax.plot(labels, completed, marker="s", color="#198754", linewidth=2, linestyle="--", label="Completed Activities")

            ax.set_title("Weekly Learning Activity Trends", fontsize=14, fontweight="bold", pad=15, color="#1a2530")
            ax.set_ylabel("Number of Activities", fontsize=11, fontweight="bold")
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.legend(loc="upper left")
            plt.xticks(rotation=20, ha="right", fontsize=9)
            plt.tight_layout()

            chart2_path = os.path.join(output_dir, "weekly_activity_trend.png")
            fig.savefig(chart2_path, format="png")
            plt.close(fig)
            generated_files.append("weekly_activity_trend.png")
        except Exception as e:
            logger.error("Failed to generate weekly activity chart: %s", e)

    # Chart 3: Activity Type Distribution (Pie Chart)
    act_data = get_activity_participation_analytics()
    if act_data:
        try:
            fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
            types = [a["activity_type"] for a in act_data]
            counts = [a["total_count"] for a in act_data]
            palette = ["#0d6efd", "#198754", "#ffc107", "#0dcaf0", "#6f42c1"]

            wedges, texts, autotexts = ax.pie(
                counts,
                labels=types,
                autopct="%1.1f%%",
                startangle=140,
                colors=palette[:len(types)],
                textprops=dict(color="#1a2530", fontweight="bold", fontsize=10)
            )
            ax.set_title("Learning Activity Type Distribution", fontsize=14, fontweight="bold", pad=15, color="#1a2530")
            plt.tight_layout()

            chart3_path = os.path.join(output_dir, "activity_type_distribution.png")
            fig.savefig(chart3_path, format="png")
            plt.close(fig)
            generated_files.append("activity_type_distribution.png")
        except Exception as e:
            logger.error("Failed to generate activity distribution chart: %s", e)

    # Chart 4: Course Engagement Comparison (Horizontal Bar Chart)
    comparison_data = get_course_comparison()
    if comparison_data:
        try:
            fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
            # Filter courses with activity or top 8
            sorted_comp = sorted(comparison_data, key=lambda x: x["total_activities"], reverse=True)[:8]
            c_names = [c["course_name"][:22] + ("..." if len(c["course_name"]) > 22 else "") for c in sorted_comp]
            c_activities = [c["total_activities"] for c in sorted_comp]

            y_pos = range(len(c_names))
            bars = ax.barh(y_pos, c_activities, color="#4f46e5", height=0.55, edgecolor="#333333", linewidth=0.8)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(c_names, fontsize=9, fontweight="medium")
            ax.invert_yaxis()
            ax.set_xlabel("Total Activities Logged", fontsize=11, fontweight="bold")
            ax.set_title("Course Engagement Intensity (Total Activities)", fontsize=14, fontweight="bold", pad=15, color="#1a2530")
            ax.grid(axis="x", linestyle="--", alpha=0.5)

            for bar in bars:
                width = bar.get_width()
                ax.annotate(f"{int(width)}",
                            xy=(width, bar.get_y() + bar.get_height() / 2),
                            xytext=(5, 0),
                            textcoords="offset points",
                            ha="left", va="center", fontsize=9, fontweight="bold")

            plt.tight_layout()
            chart4_path = os.path.join(output_dir, "course_engagement_comparison.png")
            fig.savefig(chart4_path, format="png")
            plt.close(fig)
            generated_files.append("course_engagement_comparison.png")
        except Exception as e:
            logger.error("Failed to generate course engagement chart: %s", e)

    return generated_files
