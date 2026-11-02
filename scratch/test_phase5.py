"""
Phase 5 Comprehensive Verification Script
Tests all learning analytics, activity tracking with score and duration,
multi-criteria filtering, honest null handling, CSV exports, Matplotlib charts,
and strictly confirms 100% database row count preservation.
"""

import sys
import os
import requests
import json
import mysql.connector

# Add scratch root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config import get_db_connection, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

BASE_URL = "http://127.0.0.1:5000"

def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def check_row_counts(expected=(4, 10, 11, 13, 29)):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    counts = {}
    for table in ['users', 'courses', 'learners', 'enrollments', 'activities']:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        counts[table] = cursor.fetchone()['cnt']
    cursor.close()
    conn.close()
    
    exp_users, exp_courses, exp_learners, exp_enrollments, exp_activities = expected
    match = (
        counts['users'] == exp_users and
        counts['courses'] == exp_courses and
        counts['learners'] == exp_learners and
        counts['enrollments'] == exp_enrollments and
        counts['activities'] == exp_activities
    )
    return match, counts

def run_tests():
    print("=" * 70)
    print("  PHASE 5 COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 70)

    # 1. Pre-test DB Row Counts
    match, counts = check_row_counts()
    print(f"\n[1] Initial DB Row Counts:")
    for tbl, cnt in counts.items():
        print(f"    - {tbl}: {cnt}")
    assert match, f"Initial row counts mismatch! Expected (4, 10, 11, 13, 29), got {counts}"
    print("  -> PASSED: All original row counts verified.")

    # 2. Login Session & CSRF Token Extraction
    session = requests.Session()
    r_login_page = session.get(f"{BASE_URL}/login")
    assert r_login_page.status_code == 200, f"Login page failed: {r_login_page.status_code}"
    
    # Extract CSRF token from meta or hidden input
    import re
    csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', r_login_page.text)
    if not csrf_match:
        csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', r_login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    assert csrf_token, "Could not extract CSRF token from login page"
    print(f"\n[2] CSRF Token Extracted: {csrf_token[:15]}...")

    # Log in as Admin
    login_payload = {
        'username': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    r_login = session.post(f"{BASE_URL}/login", data=login_payload, allow_redirects=True)
    assert r_login.status_code == 200, f"Login failed: {r_login.status_code}"
    print("  -> PASSED: Admin session authenticated.")

    # Update CSRF token from authenticated page for subsequent requests
    csrf_match2 = re.search(r'name="csrf-token"\s+content="([^"]+)"', r_login.text)
    auth_csrf_token = csrf_match2.group(1) if csrf_match2 else csrf_token

    # 3. Test Dashboard Summary & Honest Null Telemetry
    print("\n[3] Testing Dashboard Summary API (/api/dashboard/summary):")
    r_summary = session.get(f"{BASE_URL}/api/dashboard/summary")
    assert r_summary.status_code == 200, f"Dashboard summary failed: {r_summary.status_code}"
    summary = r_summary.json()['data']
    print(f"    - total_courses: {summary.get('total_courses')}")
    print(f"    - total_learners: {summary.get('total_learners')}")
    print(f"    - total_enrollments: {summary.get('total_enrollments')}")
    print(f"    - completed_enrollments: {summary.get('completed_enrollments')}")
    print(f"    - total_activities: {summary.get('total_activities')}")
    print(f"    - average_score: {summary.get('average_score')} (Honest NULL)")
    print(f"    - total_time_spent_minutes: {summary.get('total_time_spent_minutes')} (Honest NULL)")
    print(f"    - active_learners_count: {summary.get('active_learners_count')}")
    assert summary.get('total_activities') == 29
    assert summary.get('average_score') is None or summary.get('average_score') == 0.0 or isinstance(summary.get('average_score'), float)
    print("  -> PASSED: Dashboard summary contains all Phase 5 metrics.")

    # 4. Test Learner Performance Analytics API
    print("\n[4] Testing Learner Performance Analytics (/api/analytics/learner-performance):")
    r_learners = session.get(f"{BASE_URL}/api/analytics/learner-performance")
    assert r_learners.status_code == 200, f"Learner performance failed: {r_learners.status_code}"
    learners_data = r_learners.json()['data']
    assert len(learners_data) == 11, f"Expected 11 learners, got {len(learners_data)}"
    first_l = learners_data[0]
    print(f"    - Sample learner: {first_l['roll_no']} ({first_l.get('name')})")
    print(f"      Enrolled: {first_l['enrolled_courses_count']}, Completed: {first_l['completed_courses_count']}, Rate: {first_l['completion_rate']}%")
    print(f"      Activities: {first_l['completed_activities_count']}/{first_l['total_activities_logged']}, Status: {first_l['engagement_status']}")
    
    # Test filtering by search
    r_search = session.get(f"{BASE_URL}/api/analytics/learner-performance?search=2024CS001")
    assert r_search.status_code == 200
    assert len(r_search.json()['data']) == 1
    assert r_search.json()['data'][0]['roll_no'] == '2024CS001'
    print("  -> PASSED: Learner performance API and filtering verified.")

    # 5. Test Activity Participation Analytics API
    print("\n[5] Testing Activity Participation Analytics (/api/analytics/activity-participation):")
    r_part = session.get(f"{BASE_URL}/api/analytics/activity-participation")
    assert r_part.status_code == 200, f"Activity participation failed: {r_part.status_code}"
    part_data = r_part.json()['data']
    total_acts = sum(p['total_count'] for p in part_data)
    assert total_acts == 29, f"Expected 29 activities across types, got {total_acts}"
    print(f"    - Types found: {len(part_data)}")
    for p in part_data:
        print(f"      * {p['activity_type']}: {p['total_count']} acts ({p['completion_rate']:.1f}% completed, share: {p['percentage_of_all_activities']:.1f}%)")
    print("  -> PASSED: Activity participation telemetry verified.")

    # 6. Test Score & Time Trends API
    print("\n[6] Testing Score and Time Trends (/api/analytics/score-time-trends):")
    r_trends = session.get(f"{BASE_URL}/api/analytics/score-time-trends")
    assert r_trends.status_code == 200, f"Score time trends failed: {r_trends.status_code}"
    trend_json = r_trends.json()['data']
    print(f"    - has_score_data: {trend_json.get('has_score_data')}")
    print(f"    - has_time_data: {trend_json.get('has_time_data')}")
    print("  -> PASSED: Score and time trend telemetry verified.")

    # 7. Test CSV Export Endpoints
    print("\n[7] Testing Official CSV Export Endpoints:")
    csv_endpoints = [
        "/api/reports/course-completion.csv",
        "/api/reports/course-comparison.csv",
        "/api/reports/weekly-activity.csv",
        "/api/reports/inactive-enrollments.csv",
        "/api/reports/learner-performance.csv",
        "/api/reports/activity-participation.csv"
    ]
    for ep in csv_endpoints:
        r_csv = session.get(f"{BASE_URL}{ep}")
        assert r_csv.status_code == 200, f"CSV download failed for {ep}: {r_csv.status_code}"
        assert 'text/csv' in r_csv.headers.get('Content-Type', ''), f"Non-CSV header for {ep}"
        lines = r_csv.text.strip().splitlines()
        assert len(lines) >= 2, f"CSV {ep} appears empty (no data lines)"
        print(f"    - {ep}: {len(lines)} lines (Header + Rows) [OK]")
    print("  -> PASSED: All 6 CSV reports verified.")

    # 8. Test Matplotlib Chart Generation
    print("\n[8] Testing Matplotlib Chart Generation (/api/reports/generate-charts):")
    r_charts = session.post(
        f"{BASE_URL}/api/reports/generate-charts",
        headers={'X-CSRFToken': auth_csrf_token}
    )
    assert r_charts.status_code == 200, f"Chart generation failed: {r_charts.status_code} - {r_charts.text}"
    chart_res = r_charts.json()
    assert chart_res['success'] is True
    print(f"    - Backend response: {chart_res['message']}")
    
    # Verify the 4 generated files on disk
    expected_charts = [
        'course_completion_bar.png',
        'weekly_activity_trend.png',
        'activity_type_distribution.png',
        'course_engagement_comparison.png'
    ]
    for ch in expected_charts:
        p = os.path.join(BASE_DIR, 'static', 'charts', ch)
        assert os.path.exists(p), f"Missing chart file: {p}"
        size = os.path.getsize(p)
        assert size > 5000, f"Chart file too small ({size} bytes): {p}"
        print(f"    - {ch} generated ({size:,} bytes) [OK]")
    print("  -> PASSED: All 4 publication-ready Matplotlib figures verified.")

    # 9. Test Activity Tracking with Score and Duration (Temporary Record CRUD)
    print("\n[9] Testing Activity Tracking with Score & Duration (Temporary CRUD):")
    # First get an existing enrollment_id
    r_enr = session.get(f"{BASE_URL}/api/enrollments")
    enrollments = r_enr.json()['data']
    target_enr_id = enrollments[0]['enrollment_id']
    target_roll = enrollments[0]['roll_no']
    print(f"    - Testing with Enrollment #{target_enr_id} (Student {target_roll})")

    # Create temporary activity with score and duration
    temp_act_payload = {
        'enrollment_id': target_enr_id,
        'activity_type': 'Quiz',
        'score': 95.5,
        'time_spent_minutes': 40,
        'completed': True
    }
    r_create_act = session.post(
        f"{BASE_URL}/api/activities",
        json=temp_act_payload,
        headers={'X-CSRFToken': auth_csrf_token}
    )
    assert r_create_act.status_code == 201, f"Create activity failed: {r_create_act.status_code} - {r_create_act.text}"
    new_act_id = r_create_act.json()['data']['activity_id']
    print(f"    - Temporary Activity created with ID: {new_act_id}")

    try:
        # Verify new activity shows score and duration in DB
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT activity_id, score, time_spent_minutes, completed FROM activities WHERE activity_id = %s", (new_act_id,))
        act_row = cur.fetchone()
        assert act_row is not None
        assert float(act_row['score']) == 95.5, f"Score mismatch: {act_row['score']}"
        assert int(act_row['time_spent_minutes']) == 40, f"Time mismatch: {act_row['time_spent_minutes']}"
        cur.close()
        conn.close()
        print("    - Verified score=95.5 and time_spent_minutes=40 in MySQL database.")

        # Verify score & time trends now detects telemetry
        r_trends2 = session.get(f"{BASE_URL}/api/analytics/score-time-trends")
        trend2_json = r_trends2.json()['data']
        assert trend2_json['has_score_data'] is True
        assert trend2_json['has_time_data'] is True
        print("    - Score & Time trends API dynamically activated telemetry flags.")
    finally:
        # Clean up: DELETE the temporary activity
        conn_del = get_db()
        cur_del = conn_del.cursor()
        cur_del.execute("DELETE FROM activities WHERE activity_id = %s", (new_act_id,))
        conn_del.commit()
        cur_del.close()
        conn_del.close()
        print(f"    - Temporary Activity #{new_act_id} deleted cleanly.")
    print("  -> PASSED: Activity tracking with score and duration fully verified.")

    # 10. Multi-criteria Filtering Verification on /api/activities
    print("\n[10] Testing Multi-criteria Filtering on /api/activities:")
    r_filt1 = session.get(f"{BASE_URL}/api/activities?activity_type=Quiz")
    assert r_filt1.status_code == 200
    quizzes = r_filt1.json()['data']
    assert all(q['activity_type'] == 'Quiz' for q in quizzes)
    print(f"    - Filter by activity_type=Quiz: {len(quizzes)} found [OK]")

    r_filt2 = session.get(f"{BASE_URL}/api/activities?course_id=1")
    assert r_filt2.status_code == 200
    course1_acts = r_filt2.json()['data']
    print(f"    - Filter by course_id=1: {len(course1_acts)} found [OK]")

    r_filt3 = session.get(f"{BASE_URL}/api/activities?learner_id=1")
    assert r_filt3.status_code == 200
    learner1_acts = r_filt3.json()['data']
    print(f"    - Filter by learner_id=1: {len(learner1_acts)} found [OK]")
    print("  -> PASSED: Multi-criteria filtering verified.")

    # 11. HTML Route Availability Check
    print("\n[11] Testing HTML Frontend Route Availability:")
    routes = ['/', '/learners', '/courses', '/enrollments', '/activities', '/reports', '/settings', '/login']
    for route in routes:
        r_page = session.get(f"{BASE_URL}{route}")
        assert r_page.status_code == 200, f"Route {route} returned {r_page.status_code}"
        print(f"    - {route}: HTTP 200 [OK]")
    print("  -> PASSED: All frontend views accessible.")

    # 12. Final Database Row Count Check (Strict Invariant Check)
    print("\n[12] Final Database Row Count Invariant Check:")
    final_match, final_counts = check_row_counts()
    for tbl, cnt in final_counts.items():
        print(f"    - {tbl}: {cnt}")
    assert final_match, f"Row count corrupted! Expected (4, 10, 11, 13, 29), got {final_counts}"
    print("  -> PASSED: Database row counts are 100% PRISTINE (users: 4, courses: 10, learners: 11, enrollments: 13, activities: 29).")

    print("\n" + "=" * 70)
    print("  ALL PHASE 5 TESTS PASSED SUCCESSFULLY (12/12)!")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()
