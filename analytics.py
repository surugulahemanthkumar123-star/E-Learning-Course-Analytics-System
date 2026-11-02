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
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logger = logging.getLogger("analytics")

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


def get_dashboard_summary():
    """
    Calculates summary card figures across the entire platform.
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
            "database_connected": False
        }

    try:
        cursor = conn.cursor(dictionary=True)

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

        # Calculate inactive enrollments count using the threshold
        inactive_list = get_inactive_enrollments(config.INACTIVITY_DAYS_THRESHOLD)
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


def get_course_completion_analytics():
    """
    Computes per-course enrollment numbers and completion percentages.
    Uses Pandas DataFrame when available, or native MySQL aggregation.
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
                COUNT(e.enrollment_id) AS total_enrollments,
                SUM(CASE WHEN e.status = 'Completed' THEN 1 ELSE 0 END) AS completed_enrollments,
                SUM(CASE WHEN e.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_enrollments,
                SUM(CASE WHEN e.status = 'Enrolled' THEN 1 ELSE 0 END) AS just_enrolled
            FROM courses c
            LEFT JOIN enrollments e ON c.course_id = e.course_id
            GROUP BY c.course_id, c.course_name, c.category
            ORDER BY c.course_name ASC;
        """

        if HAS_PANDAS:
            df = pd.read_sql_query(query, conn)
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
        cursor.execute(query)
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
            HAVING last_activity_date IS NULL OR days_since_last_activity > %s
            ORDER BY 
                CASE WHEN last_activity_date IS NULL THEN 1 ELSE 0 END DESC,
                days_since_last_activity DESC,
                e.enrolled_at ASC;
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (threshold_days,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for r in rows:
            last_date = r["last_activity_date"]
            days_inactive = r["days_since_last_activity"]

            if last_date is None:
                last_activity_str = "No activity recorded"
                days_display = int(r["days_since_enrolled"]) if r["days_since_enrolled"] is not None else "N/A"
                reason = "No activity recorded since enrollment"
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


def generate_analytics_charts(output_dir=None):
    """
    Generates backend Matplotlib charts saved as PNG images in static/charts/.
    Produces:
      1. course_completion_bar.png
      2. weekly_activity_trend.png
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

    return generated_files
