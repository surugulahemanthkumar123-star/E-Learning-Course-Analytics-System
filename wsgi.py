"""
====================================================================
E-Learning Course Analytics System - Production WSGI Entry Point
File: wsgi.py
Enables production deployment via Waitress (Windows/Cross-platform)
or Gunicorn (Linux/POSIX), avoiding Flask development server warnings.
====================================================================
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import app as application

if __name__ == "__main__":
    from waitress import serve
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    threads = int(os.getenv("WAITRESS_THREADS", 6))
    print("=" * 70)
    print("  E-Learning Course Analytics System - Production WSGI Server")
    print(f"  Serving on: http://{host}:{port} (Threads: {threads})")
    print("=" * 70)
    serve(application, host=host, port=port, threads=threads)
