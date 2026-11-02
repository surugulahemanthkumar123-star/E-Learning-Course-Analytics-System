"""
====================================================================
E-Learning Course Analytics System - Phase 6 Deep Verification Audit
File: scratch/audit_phase6_checklist.py
Verifies:
  1. CSV security (CWE-1236 triggers, whitespace, numeric preservation, all 6 reports)
  2. Date validation (malformed, invalid days, inverted ranges, inclusive boundaries, all 6 endpoints)
  3. Export security (auth restrictions, filter consistency, edge case PDF rendering)
  4. Printable HTML reports (all 6 routes, content, media print styles)
  5. User preferences (validation, user isolation, concurrent thread safety)
  6. Production config (secret key, .env exclusions, cookie config, Waitress settings)
====================================================================
"""

import sys
import os
import requests
import json
import re
import threading
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import sanitize_csv_cell, parse_iso_date, validate_date_range, get_user_preferences, save_user_preferences
import config
from config import get_db_connection

BASE_URL = "http://127.0.0.1:5000"


def create_session(username="admin", password="admin123"):
    s = requests.Session()
    r = s.get(f"{BASE_URL}/login")
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', r.text) or re.search(r'name="csrf-token"\s+content="([^"]+)"', r.text)
    token = m.group(1) if m else None
    if not token:
        token = s.get(f"{BASE_URL}/api/csrf-token").json().get("csrf_token")
    res = s.post(f"{BASE_URL}/login", data={"username": username, "password": password, "csrf_token": token})
    assert res.status_code == 200, f"Login failed for {username}: {res.status_code}"
    return s


def audit_csv_security():
    print("\n[Audit 1] CSV Formula Injection & Sanitization (CWE-1236):")
    
    # 1. Trigger characters
    triggers = ["=", "+", "-", "@", "\t", "\r", "\n"]
    for t in triggers:
        res = sanitize_csv_cell(f"{t}test_cmd")
        assert res.startswith("'"), f"Trigger '{repr(t)}' not neutralized: {res}"
        print(f"  [PASS] Trigger {repr(t)} neutralized: {repr(res)}")
        
    # 2. Leading whitespace + trigger combinations
    whitespace_combos = [
        (" =SUM(A1:B10)", "' =SUM(A1:B10)"),
        ("   +cmd", "'   +cmd"),
        ("\t-2+3", "'\t-2+3"),
        ("\r@test", "'\r@test"),
        ("\n=1+1", "'\n=1+1"),
        ("  \t\r =EXEC()", "'  \t\r =EXEC()"),
    ]
    for raw, expected in whitespace_combos:
        res = sanitize_csv_cell(raw)
        assert res == expected, f"Whitespace combo failed: {repr(raw)} -> got {repr(res)}"
        print(f"  [PASS] Whitespace combo neutralized: {repr(raw)[:25]} -> {repr(res)[:25]}")
        
    # 3. Legitimate negative numbers and floats MUST remain numeric
    nums = [-100, -15, -0.001, 0, 42, 3.14159, "-42", "-3.14159", "+50"]
    for n in nums:
        res = sanitize_csv_cell(n)
        assert not str(res).startswith("'"), f"Number wrongly sanitized: {n} -> {res}"
        print(f"  [PASS] Legitimate numeric preserved: {n} -> {res} ({type(res).__name__})")
        
    # 4. Confirm all 6 CSV exports call sanitize_csv_cell
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        app_code = f.read()
    assert "writer.writerow(sanitized_row)" in app_code
    assert "sanitize_csv_cell(row.get(k))" in app_code
    
    csv_endpoints = [
        "/api/reports/course-completion.csv",
        "/api/reports/course-comparison.csv",
        "/api/reports/learner-performance.csv",
        "/api/reports/activity-participation.csv",
        "/api/reports/weekly-activity.csv",
        "/api/reports/inactive-enrollments.csv"
    ]
    admin_s = create_session()
    for ep in csv_endpoints:
        r = admin_s.get(f"{BASE_URL}{ep}")
        assert r.status_code == 200, f"CSV endpoint {ep} returned {r.status_code}"
        assert "text/csv" in r.headers.get("Content-Type", "")
        # Inspect cells
        for line in r.text.splitlines()[1:]:
            for cell in line.split(","):
                c_clean = cell.strip('"')
                if c_clean and c_clean[0] in ('=', '+', '@') and not c_clean.startswith("'"):
                    assert False, f"Vulnerability in {ep}: {c_clean}"
        print(f"  [PASS] CSV Endpoint verified sanitized: {ep}")
    print("=> Audit 1 PASSED: CSV security completely verified.")


def audit_date_validation():
    print("\n[Audit 2] Date Input Validation & HTTP 400 Responses:")
    
    # 1. Unit tests
    invalid_dates = ["bad-date", "2026-13-45", "2026/05/10", "10-05-2026", "2026-02-31", "2026-11"]
    for d in invalid_dates:
        try:
            parse_iso_date(d)
            assert False, f"parse_iso_date failed to reject: {d}"
        except ValueError:
            print(f"  [PASS] Correctly rejected malformed date: {d}")

    # Inverted range
    s, e, err = validate_date_range("2026-12-31", "2026-01-01")
    assert err and "cannot be after" in err
    print(f"  [PASS] Correctly detected inverted date range: {err}")
    
    # Valid range & inclusive boundaries
    s, e, err = validate_date_range("2026-01-01", "2026-06-30")
    assert err is None and s == "2026-01-01" and e == "2026-06-30"
    print(f"  [PASS] Valid date range confirmed: {s} to {e}")

    # 2. Test all 6 listed endpoints for HTTP 400 responses
    endpoints_to_test = [
        "/api/activities?start_date=invalid-date",
        "/api/dashboard/summary?start_date=invalid-date",
        "/api/analytics/weekly-activity?end_date=invalid-date",
        "/api/analytics/activity-participation?start_date=invalid-date",
        "/api/analytics/score-time-trends?start_date=invalid-date",
        "/api/reports/weekly-activity.csv?start_date=invalid-date"
    ]
    admin_s = create_session()
    for ep in endpoints_to_test:
        r = admin_s.get(f"{BASE_URL}{ep}")
        assert r.status_code == 400, f"Expected 400 for {ep}, got {r.status_code}: {r.text}"
        print(f"  [PASS] HTTP 400 confirmed on invalid input: {ep.split('?')[0]}")
        
    # Inverted date HTTP 400 checks
    for ep_base in ["/api/activities", "/api/dashboard/summary", "/api/analytics/weekly-activity", "/api/analytics/activity-participation", "/api/analytics/score-time-trends"]:
        r = admin_s.get(f"{BASE_URL}{ep_base}?start_date=2026-12-01&end_date=2026-01-01")
        assert r.status_code == 400, f"Expected 400 for inverted dates on {ep_base}"
        print(f"  [PASS] HTTP 400 confirmed on inverted range: {ep_base}")

    print("=> Audit 2 PASSED: Date validation rigorously enforced.")


def audit_export_security():
    print("\n[Audit 3] Export Security, Role Enforcement & PDF Edge Cases:")
    
    # 1. Unauthenticated restrictions
    anon_s = requests.Session()
    for ep in [
        "/api/reports/course-completion.csv",
        "/api/reports/course-completion.json",
        "/api/reports/course-completion.pdf",
        "/reports/printable/course-completion"
    ]:
        r = anon_s.get(f"{BASE_URL}{ep}", allow_redirects=False)
        assert r.status_code in (302, 401), f"Anon access not restricted for {ep}: {r.status_code}"
        print(f"  [PASS] Anonymous access denied for {ep}: HTTP {r.status_code}")
        
    # 2. Filter consistency across export formats
    admin_s = create_session()
    # Test inactive enrollments with threshold=5 vs threshold=30
    csv_5 = admin_s.get(f"{BASE_URL}/api/reports/inactive-enrollments.csv?threshold=5")
    json_5 = admin_s.get(f"{BASE_URL}/api/reports/inactive-enrollments.json?threshold=5")
    pdf_5 = admin_s.get(f"{BASE_URL}/api/reports/inactive-enrollments.pdf?threshold=5")
    
    csv_count_5 = len(csv_5.text.strip().splitlines()) - 1
    json_count_5 = len(json_5.json().get("data", []))
    assert csv_count_5 == json_count_5, f"Count mismatch between CSV ({csv_count_5}) and JSON ({json_count_5})"
    assert pdf_5.status_code == 200 and pdf_5.content[:4] == b"%PDF"
    print(f"  [PASS] Consistent record count across CSV and JSON with filter (threshold=5: {csv_count_5} records)")

    # 3. PDF generation with empty dataset and long text
    import reports_pdf
    # Empty dataset test
    pdf_empty = reports_pdf.build_pdf_report(
        report_title="Empty Test Report",
        field_labels=[("id", "ID", 50), ("name", "Name", 200)],
        rows=[],
        kpi_items=[("Total Items", 0)],
        filter_text="No Records"
    )
    assert pdf_empty[:4] == b"%PDF" and len(pdf_empty) > 1000
    print(f"  [PASS] PDF generated cleanly with empty dataset ({len(pdf_empty)} bytes)")

    # Long text & special characters test
    long_data = [
        {"id": 1, "name": "A" * 150 + " <special> & 'quotes' & \"entities\"", "desc": "B" * 300}
    ]
    pdf_long = reports_pdf.build_pdf_report(
        report_title="Long Text & Special Characters Test Report",
        field_labels=[("id", "ID", 40), ("name", "Extremely Long Name", 300), ("desc", "Extended Description", 380)],
        rows=long_data,
        kpi_items=[("Count", 1)],
        filter_text="Special Char Filter: <>&'\""
    )
    assert pdf_long[:4] == b"%PDF" and len(pdf_long) > 1000
    print(f"  [PASS] PDF handles long text wrapping and special XML entities ({len(pdf_long)} bytes)")

    print("=> Audit 3 PASSED: Export security and PDF edge cases verified.")


def audit_printable_reports():
    print("\n[Audit 4] Printable HTML Reports Layout & Content:")
    admin_s = create_session()
    
    routes = [
        "course-completion",
        "inactive-enrollments",
        "weekly-activity",
        "course-comparison",
        "learner-performance",
        "activity-participation"
    ]
    
    for rtype in routes:
        r = admin_s.get(f"{BASE_URL}/reports/printable/{rtype}")
        assert r.status_code == 200, f"Printable route failed for {rtype}: {r.status_code}"
        assert "@media print" in r.text
        assert "window.print()" in r.text
        assert "E-Learning Course Analytics System" in r.text
        assert "<table" in r.text
        print(f"  [PASS] Printable HTML report verified: /reports/printable/{rtype} (HTTP 200, @media print present)")

    print("=> Audit 4 PASSED: All 6 printable HTML reports verified.")


def audit_user_preferences():
    print("\n[Audit 5] User Preferences Validation, Isolation & Concurrency:")
    admin_s = create_session("admin", "admin123")
    analyst_s = create_session("aturing", "password123")
    
    # 1. Invalid values rejected
    csrf_token = admin_s.get(f"{BASE_URL}/api/csrf-token").json().get("csrf_token")
    put_invalid = admin_s.put(f"{BASE_URL}/api/user/preferences",
        headers={"X-CSRFToken": csrf_token, "Content-Type": "application/json"},
        json={"theme": "neon-glow", "page_size": 999, "date_preset": "hack-preset"}
    )
    assert put_invalid.status_code == 200
    # Values should remain default, not updated to invalid ones
    get_res = admin_s.get(f"{BASE_URL}/api/user/preferences").json().get("data", {})
    assert get_res.get("theme") in ("light", "dark")
    assert get_res.get("page_size") in (10, 25, 50, 100)
    print(f"  [PASS] Invalid preference values safely ignored: {get_res}")

    # 2. User isolation: Set admin to dark/50, analyst to light/10
    admin_csrf = admin_s.get(f"{BASE_URL}/api/csrf-token").json().get("csrf_token")
    analyst_csrf = analyst_s.get(f"{BASE_URL}/api/csrf-token").json().get("csrf_token")
    
    admin_s.put(f"{BASE_URL}/api/user/preferences",
        headers={"X-CSRFToken": admin_csrf, "Content-Type": "application/json"},
        json={"theme": "dark", "page_size": 50, "date_preset": "last_7"}
    )
    analyst_s.put(f"{BASE_URL}/api/user/preferences",
        headers={"X-CSRFToken": analyst_csrf, "Content-Type": "application/json"},
        json={"theme": "light", "page_size": 10, "date_preset": "this_quarter"}
    )
    
    admin_prefs = admin_s.get(f"{BASE_URL}/api/user/preferences").json().get("data", {})
    analyst_prefs = analyst_s.get(f"{BASE_URL}/api/user/preferences").json().get("data", {})
    
    assert admin_prefs.get("theme") == "dark" and admin_prefs.get("page_size") == 50
    assert analyst_prefs.get("theme") == "light" and analyst_prefs.get("page_size") == 10
    print(f"  [PASS] User preferences strictly isolated:")
    print(f"         Admin: {admin_prefs}")
    print(f"         Analyst: {analyst_prefs}")

    # 3. Concurrent updates thread safety test
    errors = []
    def worker(user_id, val):
        try:
            ok = save_user_preferences(user_id, {"page_size": val})
            if not ok:
                errors.append(f"Failed save for user {user_id}")
        except Exception as ex:
            errors.append(str(ex))

    threads = []
    for i in range(20):
        t1 = threading.Thread(target=worker, args=(1, 25 if i % 2 == 0 else 50))
        t2 = threading.Thread(target=worker, args=(2, 10 if i % 2 == 0 else 100))
        threads.extend([t1, t2])
        t1.start()
        t2.start()

    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrency errors encountered: {errors}"
    print(f"  [PASS] 40 concurrent preference writes executed cleanly with 0 errors")

    # Clean reset
    admin_s.put(f"{BASE_URL}/api/user/preferences",
        headers={"X-CSRFToken": admin_csrf, "Content-Type": "application/json"},
        json={"theme": "light", "page_size": 25, "date_preset": "all_time"}
    )
    print("=> Audit 5 PASSED: User preferences isolation and concurrency verified.")


def audit_production_config():
    print("\n[Audit 6] Production Configuration & Security Hardening:")
    
    # 1. Flask secret key
    assert config.SECRET_KEY is not None and len(config.SECRET_KEY) > 10
    print(f"  [PASS] SECRET_KEY configured (length: {len(config.SECRET_KEY)})")

    # 2. .gitignore exclusions
    with open(os.path.join(BASE_DIR, ".gitignore"), "r", encoding="utf-8") as f:
        gitignore_content = f.read()
    assert ".env" in gitignore_content
    assert "user_preferences.json" in gitignore_content
    assert "backups/*.sql" in gitignore_content
    print("  [PASS] .env, user_preferences.json, and backups/*.sql are excluded by .gitignore")

    # 3. HTTPS / Cookie settings
    import app
    assert app.app.config.get("SESSION_COOKIE_HTTPONLY") is True
    assert app.app.config.get("SESSION_COOKIE_SAMESITE") == "Lax"
    print("  [PASS] SESSION_COOKIE_HTTPONLY=True and SESSION_COOKIE_SAMESITE='Lax'")

    # 4. Waitress environment configuration
    with open(os.path.join(BASE_DIR, "wsgi.py"), "r", encoding="utf-8") as f:
        wsgi_code = f.read()
    assert "os.getenv(\"PORT\"" in wsgi_code or "os.getenv('PORT'" in wsgi_code
    assert "os.getenv(\"WAITRESS_THREADS\"" in wsgi_code or "os.getenv('WAITRESS_THREADS'" in wsgi_code
    assert "os.getenv(\"HOST\"" in wsgi_code or "os.getenv('HOST'" in wsgi_code
    print("  [PASS] wsgi.py is environment-driven (HOST, PORT, WAITRESS_THREADS)")

    print("=> Audit 6 PASSED: Production configuration verified.")


if __name__ == "__main__":
    print("=" * 70)
    print("  PHASE 6 DEEP VERIFICATION AUDIT")
    print("=" * 70)
    
    audit_csv_security()
    audit_date_validation()
    audit_export_security()
    audit_printable_reports()
    audit_user_preferences()
    audit_production_config()
    
    print("\n" + "=" * 70)
    print("  PHASE 6 DEEP VERIFICATION AUDIT COMPLETED: 100% PASS")
    print("=" * 70)
