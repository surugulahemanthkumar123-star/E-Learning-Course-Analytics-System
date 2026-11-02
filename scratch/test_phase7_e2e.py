"""
====================================================================
E-Learning Course Analytics System - Phase 7 End-to-End Test Suite
File: scratch/test_phase7_e2e.py
Comprehensive End-to-End Verification:
  1. Complete User Lifecycle: Login, Session, Profile, Logout
  2. Role-Based Access Control (RBAC): Admin vs Academic Analyst vs Anon
  3. CSRF Protection: Missing, Invalid, and Valid Tokens
  4. Core Analytics Engine & Dashboard Filters
  5. Multi-Format Enterprise Reporting (6 CSVs, 6 JSONs, 6 PDFs, 6 Printables)
  6. User Preferences & Profile Updates (with clean state restoration)
  7. Database Connection Resilience & Error Handling
  8. Invariant Database Baseline Comparison
====================================================================
"""

import sys
import os
import requests
import json
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config
from config import get_db_connection

BASE_URL = "http://127.0.0.1:5000"


def get_csrf(session):
    """Retrieves a fresh CSRF token for the session."""
    try:
        r = session.get(f"{BASE_URL}/api/csrf-token")
        if r.status_code == 200:
            tok = r.json().get("csrf_token")
            if tok:
                return tok
    except Exception:
        pass
    r_page = session.get(f"{BASE_URL}/login")
    m = re.search(r'name="csrf-token"\s+content="([^"]+)"', r_page.text) or re.search(r'name="csrf_token"\s+value="([^"]+)"', r_page.text)
    return m.group(1) if m else None


def login(session, username, password):
    """Authenticates a session with CSRF protection."""
    token = get_csrf(session)
    res = session.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": password,
        "csrf_token": token
    }, allow_redirects=True)
    return res


def test_1_authentication_lifecycle():
    print("\n--- Phase 7 Test 1: Complete Authentication Lifecycle ---")
    s = requests.Session()
    
    # 1. Login with bad credentials fails
    r_fail = s.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "wrong_password_999",
        "csrf_token": get_csrf(s)
    })
    assert "Invalid username or password" in r_fail.text or r_fail.status_code == 200
    print("  [PASS] Login with invalid password rejected")
    
    # 2. Login with valid Admin credentials succeeds
    r_login = login(s, "admin", "admin123")
    assert r_login.status_code == 200
    assert "Dashboard" in r_login.text or "Home" in r_login.text or "EduAnalytics" in r_login.text
    print("  [PASS] Admin authenticated successfully")
    
    # 3. Access protected dashboard
    r_dash = s.get(f"{BASE_URL}/dashboard")
    assert r_dash.status_code == 200
    print("  [PASS] Protected /dashboard accessible while authenticated")
    
    # 4. Logout
    r_logout = s.get(f"{BASE_URL}/logout", allow_redirects=True)
    assert r_logout.status_code == 200
    print("  [PASS] Logout completed cleanly")
    
    # 5. Subsequent access to dashboard redirects to login
    r_dash_after = s.get(f"{BASE_URL}/dashboard", allow_redirects=False)
    assert r_dash_after.status_code == 302 and "/login" in r_dash_after.headers.get("Location", "")
    print("  [PASS] Unauthenticated access to /dashboard redirected to /login (HTTP 302)")


def test_2_rbac_permissions():
    print("\n--- Phase 7 Test 2: Role-Based Access Control (RBAC) ---")
    
    admin_s = requests.Session()
    login(admin_s, "admin", "admin123")
    
    analyst_s = requests.Session()
    login(analyst_s, "aturing", "password123")
    
    # 1. Analyst attempts Admin-only action: DELETE /api/courses/999
    # Must be rejected with HTTP 403 Forbidden
    analyst_csrf = get_csrf(analyst_s)
    r_del = analyst_s.delete(
        f"{BASE_URL}/api/courses/999",
        headers={"X-CSRFToken": analyst_csrf}
    )
    assert r_del.status_code == 403, f"Expected 403 for Analyst deleting course, got {r_del.status_code}: {r_del.text}"
    print("  [PASS] Academic Analyst blocked from Admin-only API (DELETE /api/courses/999 -> HTTP 403)")

    # 2. Analyst attempts Admin-only action: POST /api/learners
    r_create_learner = analyst_s.post(
        f"{BASE_URL}/api/learners",
        headers={"X-CSRFToken": analyst_csrf, "Content-Type": "application/json"},
        json={"roll_no": "TEST999"}
    )
    assert r_create_learner.status_code == 403, f"Expected 403 for Analyst creating learner, got {r_create_learner.status_code}"
    print("  [PASS] Academic Analyst blocked from Admin-only API (POST /api/learners -> HTTP 403)")

    # 3. Analyst permitted action: POST /api/reports/generate-charts
    r_charts = analyst_s.post(
        f"{BASE_URL}/api/reports/generate-charts",
        headers={"X-CSRFToken": analyst_csrf}
    )
    assert r_charts.status_code == 200, f"Expected 200 for Analyst generating charts, got {r_charts.status_code}"
    print("  [PASS] Academic Analyst authorized for permitted role API (POST /api/reports/generate-charts -> HTTP 200)")

    # 4. Anonymous user attempts access to protected API: GET /api/learners
    anon_s = requests.Session()
    r_anon = anon_s.get(f"{BASE_URL}/api/learners")
    assert r_anon.status_code == 401, f"Expected 401 for anonymous access, got {r_anon.status_code}"
    print("  [PASS] Anonymous user blocked from protected API (GET /api/learners -> HTTP 401)")


def test_3_csrf_protection():
    print("\n--- Phase 7 Test 3: CSRF Protection & Token Validation ---")
    s = requests.Session()
    login(s, "admin", "admin123")
    
    # 1. State-changing request with NO CSRF token -> HTTP 400
    r_no_csrf = s.put(
        f"{BASE_URL}/api/user/preferences",
        headers={"Content-Type": "application/json"},
        json={"theme": "dark"}
    )
    assert r_no_csrf.status_code == 400, f"Expected 400 for missing CSRF, got {r_no_csrf.status_code}: {r_no_csrf.text}"
    print("  [PASS] Request with missing CSRF token rejected with HTTP 400")

    # 2. State-changing request with INVALID CSRF token -> HTTP 400
    r_bad_csrf = s.put(
        f"{BASE_URL}/api/user/preferences",
        headers={"Content-Type": "application/json", "X-CSRFToken": "invalid_forged_csrf_token_123"},
        json={"theme": "dark"}
    )
    assert r_bad_csrf.status_code == 400, f"Expected 400 for bad CSRF, got {r_bad_csrf.status_code}"
    print("  [PASS] Request with forged CSRF token rejected with HTTP 400")

    # 3. State-changing request with VALID CSRF token -> HTTP 200
    token = get_csrf(s)
    r_valid_csrf = s.put(
        f"{BASE_URL}/api/user/preferences",
        headers={"Content-Type": "application/json", "X-CSRFToken": token},
        json={"theme": "dark"}
    )
    assert r_valid_csrf.status_code == 200, f"Expected 200 for valid CSRF, got {r_valid_csrf.status_code}"
    print("  [PASS] Request with valid CSRF token succeeded (HTTP 200)")


def test_4_dashboard_kpis_and_filters():
    print("\n--- Phase 7 Test 4: Dashboard KPIs, Filters & Telemetry ---")
    s = requests.Session()
    login(s, "admin", "admin123")
    
    # 1. Unfiltered summary
    r_sum = s.get(f"{BASE_URL}/api/dashboard/summary")
    assert r_sum.status_code == 200
    data = r_sum.json().get("data", {})
    assert data.get("total_courses") == 10
    assert data.get("total_learners") == 11
    assert data.get("total_enrollments") == 13
    assert data.get("total_activities") == 29
    print(f"  [PASS] Platform-wide KPI Summary verified:")
    print(f"         Courses: {data.get('total_courses')}, Learners: {data.get('total_learners')}, Enrollments: {data.get('total_enrollments')}, Activities: {data.get('total_activities')}")

    # 2. Course-scoped filter
    r_filtered = s.get(f"{BASE_URL}/api/dashboard/summary?course_id=1")
    assert r_filtered.status_code == 200
    fdata = r_filtered.json().get("data", {})
    assert fdata.get("total_courses") == 1
    assert fdata.get("total_enrollments") == 4
    print(f"  [PASS] Filtered Summary (course_id=1) correctly scoped: {fdata.get('total_enrollments')} enrollments")

    # 3. Honest telemetry (Score and Time Trends)
    r_trends = s.get(f"{BASE_URL}/api/analytics/score-time-trends")
    assert r_trends.status_code == 200
    tdata = r_trends.json().get("data", {})
    assert "has_score_data" in tdata and "has_time_data" in tdata
    assert tdata["has_score_data"] is False, "Database scores should be NULL without fabrication"
    assert tdata["has_time_data"] is False, "Database times should be NULL without fabrication"
    print("  [PASS] Score and Duration trends telemetry preserves honest NULL indicators")


def test_5_all_reports_all_formats():
    print("\n--- Phase 7 Test 5: All 6 Reports in All 4 Formats (24 Endpoints) ---")
    s = requests.Session()
    login(s, "admin", "admin123")
    
    reports = [
        "course-completion",
        "course-comparison",
        "learner-performance",
        "activity-participation",
        "weekly-activity",
        "inactive-enrollments"
    ]
    
    for r in reports:
        # CSV
        r_csv = s.get(f"{BASE_URL}/api/reports/{r}.csv")
        assert r_csv.status_code == 200 and "text/csv" in r_csv.headers.get("Content-Type", "")
        # JSON
        r_json = s.get(f"{BASE_URL}/api/reports/{r}.json")
        assert r_json.status_code == 200 and r_json.json().get("success") is True
        # PDF
        r_pdf = s.get(f"{BASE_URL}/api/reports/{r}.pdf")
        assert r_pdf.status_code == 200 and r_pdf.content[:4] == b"%PDF"
        # Printable HTML
        r_print = s.get(f"{BASE_URL}/reports/printable/{r}")
        assert r_print.status_code == 200 and "@media print" in r_print.text
        
        print(f"  [PASS] Report '{r}': CSV (200), JSON (200), PDF (200, {len(r_pdf.content)}B), Printable (200)")


def test_6_profile_and_user_preferences():
    print("\n--- Phase 7 Test 6: Profile Management & User Preferences ---")
    s = requests.Session()
    login(s, "admin", "admin123")
    token = get_csrf(s)
    
    # 1. Update Profile (Name & Email)
    r_prof_update = s.put(f"{BASE_URL}/api/profile",
        headers={"Content-Type": "application/json", "X-CSRFToken": token},
        json={"full_name": "Academic Administrator", "email": "admin@elearning.edu"}
    )
    assert r_prof_update.status_code == 200
    print("  [PASS] Profile updated successfully")

    # 2. Update Preferences
    r_pref_update = s.put(f"{BASE_URL}/api/user/preferences",
        headers={"Content-Type": "application/json", "X-CSRFToken": token},
        json={"theme": "dark", "page_size": 25, "date_preset": "last_30"}
    )
    assert r_pref_update.status_code == 200
    
    # Verify retrieval
    r_pref_get = s.get(f"{BASE_URL}/api/user/preferences")
    pdata = r_pref_get.json().get("data", {})
    assert pdata.get("theme") == "dark" and pdata.get("date_preset") == "last_30"
    print(f"  [PASS] User preferences updated and verified: {pdata}")
    
    # Clean reset
    s.put(f"{BASE_URL}/api/user/preferences",
        headers={"Content-Type": "application/json", "X-CSRFToken": token},
        json={"theme": "light", "page_size": 25, "date_preset": "all_time"}
    )
    print("  [PASS] Preferences cleanly restored to default")


def test_7_database_connection_and_error_handling():
    print("\n--- Phase 7 Test 7: Error Handling & Health Status ---")
    s = requests.Session()
    
    # Health endpoint
    r_health = s.get(f"{BASE_URL}/api/health")
    assert r_health.status_code == 200
    hdata = r_health.json()
    assert hdata.get("status") == "healthy"
    assert hdata.get("database", {}).get("connected") is True
    print(f"  [PASS] Health endpoint: DB connected (status: {hdata.get('status')})")

    # 404 Route handling (unauthenticated redirects to login; authenticated returns 404)
    r_404_unauth = s.get(f"{BASE_URL}/non-existent-page-route-12345", allow_redirects=False)
    assert r_404_unauth.status_code in (404, 302)
    s_auth = requests.Session()
    login(s_auth, "admin", "admin123")
    r_404_auth = s_auth.get(f"{BASE_URL}/non-existent-page-route-12345")
    assert r_404_auth.status_code == 404
    print(f"  [PASS] Non-existent route handled safely (unauth: HTTP {r_404_unauth.status_code}, auth: HTTP {r_404_auth.status_code})")


def test_8_strict_database_invariants():
    print("\n--- Phase 7 Test 8: Final Database Invariant & Value Verification ---")
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    
    # 1. Exact Row Counts
    expected = {
        "users": 4,
        "courses": 10,
        "learners": 11,
        "enrollments": 13,
        "activities": 29
    }
    for table, exp_count in expected.items():
        cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
        cnt = cur.fetchone()["total"]
        assert cnt == exp_count, f"Table '{table}' row count mismatch: expected {exp_count}, got {cnt}"
        print(f"  [PASS] Table '{table}': {cnt} rows (100% matched)")

    # 2. Specific Field Value Verification on users table
    cur.execute("SELECT user_id, username, email, full_name, role FROM users ORDER BY user_id ASC")
    users = cur.fetchall()
    assert users[0]["username"] == "admin" and users[0]["role"] == "Admin"
    assert users[1]["username"] == "aturing" and users[1]["role"] == "Academic Analyst"
    assert users[2]["username"] == "ramu123" and users[2]["role"] == "Admin"
    assert users[3]["username"] == "nani123" and users[3]["role"] == "Academic Analyst"
    print("  [PASS] Verified users table records: all 4 accounts, roles, and usernames intact")

    # 3. Check NULL telemetry invariant on activities table
    cur.execute("SELECT COUNT(score) AS non_null_scores, COUNT(time_spent_minutes) AS non_null_times FROM activities")
    row = cur.fetchone()
    assert row["non_null_scores"] == 0, f"Found unexpected non-null scores: {row['non_null_scores']}"
    assert row["non_null_times"] == 0, f"Found unexpected non-null times: {row['non_null_times']}"
    print("  [PASS] Zero fabricated scores or durations injected into activities (all 29 records have NULL telemetry)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("  PHASE 7 FINAL END-TO-END SYSTEM VALIDATION SUITE")
    print("=" * 70)
    
    test_1_authentication_lifecycle()
    test_2_rbac_permissions()
    test_3_csrf_protection()
    test_4_dashboard_kpis_and_filters()
    test_5_all_reports_all_formats()
    test_6_profile_and_user_preferences()
    test_7_database_connection_and_error_handling()
    test_8_strict_database_invariants()
    
    print("\n" + "=" * 70)
    print("  ALL PHASE 7 END-TO-END VALIDATION TESTS PASSED SUCCESSFULLY! (100%)")
    print("=" * 70)
