# 🎓 E-Learning Course Analytics System

A full-stack, data-driven web application built with **Python Flask**, **MySQL 8.0**, **Pandas**, **NumPy**, **Matplotlib**, **Bootstrap 5**, and **Chart.js** designed for academic administrators to analyze student learning trajectories, course completion metrics, weekly engagement trends, and inactive enrollments.

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Technology Stack](#-technology-stack)
3. [Folder Structure](#-folder-structure)
4. [Prerequisites & Installations](#-prerequisites--installations)
5. [Step-by-Step Setup Guide in VS Code](#-step-by-step-setup-guide-in-vs-code)
   - [Step 1: Open Project in VS Code](#step-1-open-the-project-in-vs-code)
   - [Step 2: Database Setup via MySQL Workbench](#step-2-database-setup-via-mysql-workbench)
   - [Step 3: Create Local .env Configuration](#step-3-create-your-local-env-file)
   - [Step 4: Create & Activate Virtual Environment](#step-4-create--activate-python-virtual-environment)
   - [Step 5: Install Project Dependencies](#step-5-install-python-dependencies)
   - [Step 6: Run the Flask Application](#step-6-start-the-flask-application)
   - [Step 7: Access the Dashboard](#step-7-open-the-web-application)
6. [Testing & Verification Guide](#-testing--verification-guide)
7. [System Architecture & Analytics Engine](#-system-architecture--analytics-engine)
8. [REST API Documentation](#-rest-api-documentation)
9. [Troubleshooting Common Issues](#-troubleshooting-common-issues)

---

## 🌟 Project Overview

The **E-Learning Course Analytics System** enables educators and administrators to:
- **Manage Courses**: Register, search, edit, and safely delete educational courses across categories.
- **Manage Learners**: Maintain college student profiles uniquely identified by college roll numbers.
- **Manage Enrollments**: Register learners into courses with progression tracking (`Enrolled`, `In Progress`, `Completed`) and duplicate prevention.
- **Track Learning Activities**: Record granular timestamped submissions (`Lesson`, `Quiz`, `Assignment`, `Practice`, `Project`).
- **Course Completion Analytics**: Calculate real course completion rates using:
  $$\text{Course Completion Rate} = \left(\frac{\text{Completed Enrollments}}{\text{Total Enrollments}}\right) \times 100$$
- **Overall Completion Rate**: Accurately calculated as $(\text{Total Completed} / \text{Total Enrollments}) \times 100$ without false averaging.
- **Weekly Learning Activity Trends**: Aggregates activity dates chronologically by calendar week using Pandas.
- **Inactive Enrollment Detection**: Automatically detects at-risk enrollments where status is not completed and either **no activity is recorded** or **last activity was $> 14$ days ago**.
- **Automated CSV & Matplotlib Exports**: Instant streaming of official CSV reports and on-demand server-side Matplotlib chart generation.

---

## 🛠 Required Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| **Backend** | Python 3.10+, Flask 3.0+, Flask REST API |
| **Data Engine** | Pandas, NumPy, Matplotlib (Headless Agg backend) |
| **Database** | MySQL Server 8.0+ (InnoDB Engine, utf8mb4), MySQL Connector/Python |
| **Dev Environment** | Visual Studio Code, Windows 10/11, Python `venv` |

---

## 📁 Folder Structure

```
elearning_analytics/
│
├── app.py                     # Main Flask application with Web & REST API routes
├── config.py                  # Database connection, pooling, & environment parser
├── analytics.py               # Pandas, NumPy & Matplotlib analytics engine
├── requirements.txt           # Python package specifications
├── database.sql               # MySQL 8.0 schema DDL & demonstration seed data
├── .env.example               # Template for environment credentials
├── .gitignore                 # Excludes venv, pycache, .env, and exports
├── README.md                  # Comprehensive setup and user guide
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Shared responsive SaaS layout & navigation
│   ├── index.html             # Main analytics dashboard with Chart.js
│   ├── courses.html           # Course catalog & CRUD modal operations
│   ├── learners.html          # Learner directory & enrollment inspector
│   ├── enrollments.html       # Enrollment manager & status tracking
│   ├── activities.html        # Learning activity logger & timestamp filter
│   ├── reports.html           # Analytics reports viewer & CSV exports
│   └── settings.html          # Database health & table verification panel
│
├── static/                    # Frontend assets
│   ├── css/
│   │   └── style.css          # Modern dashboard stylesheet
│   ├── js/
│   │   ├── dashboard.js       # Live dashboard charts and counters
│   │   ├── courses.js         # Course CRUD & client validation
│   │   ├── learners.js        # Learner registration & lookup
│   │   ├── enrollments.js     # Enrollment workflows & status editor
│   │   ├── activities.js      # Activity tracking & completion toggler
│   │   └── reports.js         # Report tab switching & Matplotlib trigger
│   └── charts/
│       └── .gitkeep           # Target folder for generated Matplotlib PNGs
│
└── exports/
    └── .gitkeep               # Target folder for archived CSV exports
```

---

## ⚙ Prerequisites & Installations

Before running the application on Windows, verify that **Python** and **MySQL** are installed:

### 1. Install Python (Version 3.10, 3.11, or 3.12)
1. Download Python from the official site: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer.
3. ⚠️ **CRITICAL STEP**: On the very first installation screen, check the box:
   **`☑ Add python.exe to PATH`**.
4. Complete the installation with default options.

### 2. Install MySQL Server & MySQL Workbench
1. Download the **MySQL Installer for Windows**: [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/)
2. Choose **Developer Default** or install **MySQL Server 8.0** and **MySQL Workbench 8.0**.
3. During setup, set a password for the `root` user (e.g., `admin123` or your chosen password) and remember it.
4. Ensure the MySQL Windows Service (default: `MySQL80`) is set to start automatically.

---

## 🚀 Step-by-Step Setup Guide in VS Code

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Click **File** &rarr; **Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Navigate to and open the project directory:
   `C:\Users\surug\.gemini\antigravity\scratch\elearning_analytics`
4. Open the integrated terminal in VS Code:
   Press `` Ctrl + ` `` (Backtick) or click **Terminal** &rarr; **New Terminal**.

---

### Step 2: Database Setup via MySQL Workbench
1. Open **MySQL Workbench**.
2. Click your local connection (**Local instance MySQL80**, user: `root`).
3. Press `Ctrl + Shift + O` (or **File** &rarr; **Open SQL Script...**).
4. Select `database.sql` located inside the `elearning_analytics` folder.
5. Click the **Lightning Bolt Icon** (`Execute SQL Script` or press `Ctrl + Shift + Enter`).
6. In the left **Schemas** panel, right-click and select **Refresh All**.
7. You will see the database `elearning_db` with all 4 tables created and populated with realistic college demonstration records:
   - `courses`
   - `learners`
   - `enrollments`
   - `activities`

---

### Step 3: Create your Local `.env` File
1. In VS Code Explorer, right-click `.env.example` and select **Copy**, then paste it and rename it to `.env` (or run in PowerShell):
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` and enter your actual local MySQL password:
   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_actual_mysql_password
   DB_NAME=elearning_db

   FLASK_PORT=5000
   FLASK_DEBUG=True
   SECRET_KEY=college-project-secret-key-2026

   INACTIVITY_DAYS_THRESHOLD=14
   ```
3. Save the `.env` file (`Ctrl + S`).

---

### Step 4: Create & Activate Python Virtual Environment

In the VS Code PowerShell terminal, execute:

1. **Create the virtual environment**:
   ```powershell
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   > 💡 **Tip:** If PowerShell displays a `Script Execution Policy` error, run:
   > ```powershell
   > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   > .\venv\Scripts\Activate.ps1
   > ```
   When active, your prompt will show `(venv)`.

---

### Step 5: Install Python Dependencies

With the virtual environment activated, install all required packages:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This installs:
- `Flask` — Lightweight Python web framework and REST API server
- `mysql-connector-python` — Official Oracle MySQL database driver
- `pandas` & `numpy` — Fast vector math, date resampling, and aggregation
- `matplotlib` — Statistical charts generator
- `python-dotenv` — Secure environment variable parser

---

### Step 6: Start the Flask Application

Run the server with:
```powershell
python app.py
```

You will see:
```text
======================================================================
  E-Learning Course Analytics System
  Starting Flask server on port 5000
  Access dashboard at: http://127.0.0.1:5000
======================================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 7: Open the Web Application
Open your web browser (Chrome, Edge, or Firefox) and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔍 Testing & Verification Guide

Follow this sequence to test all features:

| Test Case | How to Test | Expected Result |
| :--- | :--- | :--- |
| **1. Database Health Check** | Navigate to `/settings` or `GET /api/health` | Status displays `Connected (Online)` and all 4 tables are marked `Verified`. |
| **2. Dashboard Summary** | View `/` (Dashboard) | Summary cards load real figures from MySQL (Courses, Learners, Enrollments, Inactive count). |
| **3. Course Completion Chart** | View `/` | Chart.js renders completion rate bars and learner distribution with tooltips. |
| **4. Weekly Activity Trend** | View `/` | Chronological line chart displays total and completed activities per calendar week. |
| **5. Inactive Detection (14d)** | View `/` bottom table | Lists students with no activity or last activity $> 14$ days ago. Enter threshold `20` and click **Filter** to test dynamic thresholding. |
| **6. Course Management** | Go to `/courses`, click **Add Course** | New course appears in catalog; search input filters results dynamically. |
| **7. Learner Registration** | Go to `/learners`, click **Register Learner** | Registers new roll number; attempting duplicate roll number displays friendly warning banner. |
| **8. Safe Deletion Rule** | Attempt to delete a course with enrollments | Action is safely rejected with an informative notice preventing orphaned records. |
| **9. Activity Logging** | Go to `/activities`, click **Log Activity** | Select enrollment and type (`Lesson`, `Quiz`, etc.); saves real timestamp and advances enrollment status. |
| **10. CSV Exports** | Go to `/reports`, click **Export to CSV** | Browser downloads sanitized `.csv` file and caches copy in `exports/`. |
| **11. Matplotlib Charts** | Go to `/reports`, click **Generate Backend Matplotlib Charts** | Matplotlib renders high-resolution figures into `static/charts/` and displays previews immediately. |

---

## 🏗 System Architecture & Analytics Engine

### 1. Course Completion Formula
$$\text{Course Completion Rate} = \left(\frac{\text{Completed Enrollments}}{\text{Total Enrollments}}\right) \times 100$$
- If `Total Enrollments == 0`, safe division protects against divide-by-zero errors and returns `0.0%`.
- Performance thresholds:
  - $\ge 75\%$: **Excellent** (`success`)
  - $\ge 50\%$: **Good** (`primary`)
  - $\ge 25\%$: **Average** (`warning`)
  - $< 25\%$: **Needs Attention** (`danger`)
  - $0$ enrollments: **No Enrollments** (`secondary`)

### 2. Inactive Enrollment Calculation
An enrollment is flagged as inactive if:
1. Status is **not** `'Completed'`, **AND**
2. Either:
   - It has **zero** recorded activities in the `activities` table (`last_activity_date IS NULL`), **OR**
   - $\text{DATEDIFF}(\text{NOW}(), \text{MAX}(\text{activity\_date})) > 14\text{ days}$.

A SQL `GROUP BY e.enrollment_id` with `HAVING` avoids duplicate rows when an enrollment has multiple past activities.

---

## 📡 REST API Documentation

### System Diagnostics
- `GET /api/health` — Returns application health and MySQL table verification status without leaking passwords.

### Dashboard & Analytics
- `GET /api/dashboard/summary` — Overview metrics for dashboard cards.
- `GET /api/analytics/course-completion` — Per-course completion breakdown for Chart.js.
- `GET /api/analytics/weekly-activity?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` — Weekly aggregated activities.
- `GET /api/analytics/inactive-enrollments?threshold=14` — Filtered list of inactive enrollments.
- `GET /api/analytics/course-comparison` — Comparative performance table data.

### Course Endpoints
- `GET /api/courses?search=term` — Search and list all courses.
- `POST /api/courses` — JSON body: `{"course_name": "...", "category": "..."}`.
- `GET /api/courses/<id>` — Fetch single course details.
- `PUT /api/courses/<id>` — Update course information.
- `DELETE /api/courses/<id>` — Delete course (with safe check preventing deletion if enrollments exist).

### Learner Endpoints
- `GET /api/learners?search=roll` — Search and list learners.
- `POST /api/learners` — JSON body: `{"roll_no": "2024CS001"}`. Returns HTTP `409 Conflict` if duplicate.
- `PUT /api/learners/<id>` — Update roll number.
- `DELETE /api/learners/<id>` — Safe delete learner.
- `GET /api/learners/<id>/enrollments` — View all courses enrolled by a student.

### Enrollment Endpoints
- `GET /api/enrollments?course_id=...&status=...&search=...` — Filtered list of enrollments.
- `POST /api/enrollments` — JSON body: `{"learner_id": 1, "course_id": 2, "status": "Enrolled"}`.
- `PUT /api/enrollments/<id>` — JSON body: `{"status": "In Progress"}`.
- `GET /api/enrollments/<id>/activities` — Activity timeline for a specific enrollment.

### Learning Activity Endpoints
- `GET /api/activities?activity_type=...&start_date=...` — Query activity log.
- `POST /api/activities` — JSON body: `{"enrollment_id": 1, "activity_type": "Quiz", "completed": true}`.
- `PUT /api/activities/<id>` — Update completion state.

### CSV & Reporting Endpoints
- `GET /api/reports/course-completion.csv`
- `GET /api/reports/inactive-enrollments.csv?threshold=14`
- `GET /api/reports/weekly-activity.csv`
- `GET /api/reports/course-comparison.csv`
- `POST /api/reports/generate-charts` — Generates backend Matplotlib figures.

---

## 🔧 Troubleshooting Common Issues

### 1. `ModuleNotFoundError: No module named 'flask'` (or `mysql`)
- **Cause:** Python virtual environment is not activated or packages were not installed into it.
- **Fix:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  ```

### 2. MySQL `Access denied for user 'root'@'localhost'` (Error 1045)
- **Cause:** Incorrect MySQL password in `.env`.
- **Fix:** Open `.env` and verify `DB_PASSWORD=your_actual_password`. Test connecting to MySQL Workbench with the same password.

### 3. `Unknown database 'elearning_db'` (Error 1049)
- **Cause:** `database.sql` has not been executed yet.
- **Fix:** Open `database.sql` in MySQL Workbench and execute the full script (Lightning Bolt icon).

### 4. `Table 'elearning_db.courses' doesn't exist` (Error 1146)
- **Cause:** Partial script execution.
- **Fix:** Re-run `database.sql` from the top in MySQL Workbench. Check `/settings` to verify all 4 tables are present.

### 5. `TemplateNotFound: base.html` (or `index.html`)
- **Cause:** Running `python app.py` from outside the `elearning_analytics` directory.
- **Fix:** Ensure your terminal is in the folder containing `app.py` before running:
  ```powershell
  cd C:\Users\surug\.gemini\antigravity\scratch\elearning_analytics
  python app.py
  ```

### 6. `OSError: [WinError 10048] Only one usage of each socket address is normally permitted`
- **Cause:** Port 5000 is already in use by another running Flask or web process.
- **Fix:** Either change `FLASK_PORT=5001` in your `.env` file, or stop the existing process in PowerShell:
  ```powershell
  Stop-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess -Force
  ```

### 7. MySQL Server Not Running
- **Cause:** The Windows MySQL service is stopped.
- **Fix:** Open Windows **Services** (`services.msc`), locate **MySQL80**, right-click and select **Start**.

---

## 📄 Academic Project Details
- **Project Name:** E-Learning Course Analytics System
- **Level:** Intermediate College B.Tech Mini / Major Project
- **Architecture:** Client-Server Multi-tier Architecture with Separation of Concerns
- **Database Engine:** MySQL 8.0 Relational DBMS with Referential Integrity
