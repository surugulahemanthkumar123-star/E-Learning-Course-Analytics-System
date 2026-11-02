"""
====================================================================
E-Learning Course Analytics System - Presentation Generator
File: create_presentation.py
Generates a professional, 16:9 widescreen PowerPoint presentation (.pptx)
designed for a 5-member college B.Tech project submission and defense.
====================================================================
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Initialize Presentation
prs = Presentation()
# Set 16:9 Widescreen dimensions
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette
COLOR_NAVY_DARK = RGBColor(15, 23, 42)      # #0f172a
COLOR_NAVY_LIGHT = RGBColor(30, 41, 59)     # #1e293b
COLOR_PRIMARY_BLUE = RGBColor(37, 99, 235)  # #2563eb
COLOR_ACCENT_BLUE = RGBColor(56, 189, 248)  # #38bdf8
COLOR_EMERALD = RGBColor(16, 185, 129)      # #10b981
COLOR_AMBER = RGBColor(245, 158, 11)        # #f59e0b
COLOR_CRIMSON = RGBColor(239, 68, 68)       # #ef4444
COLOR_BG_CARD = RGBColor(255, 255, 255)     # #ffffff
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)      # #0f172a
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)  # #64748b
COLOR_LIGHT_GRAY = RGBColor(241, 245, 249)  # #f1f5f9
COLOR_BORDER = RGBColor(226, 232, 240)      # #e2e8f0

blank_layout = prs.slide_layouts[6]  # Blank layout


def create_header(slide, title_text, category_text="B.TECH CAPSTONE PROJECT PRESENTATION"):
    """Creates a consistent, professional header across slides."""
    # Top Accent Bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_PRIMARY_BLUE
    bar.line.fill.background()

    # Category Pill / Supertitle
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(8), Inches(0.3))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = category_text.upper()
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_PRIMARY_BLUE

    # Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.5), Inches(0.7))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(22)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_NAVY_DARK


def add_card(slide, left, top, width, height, bg_color=COLOR_BG_CARD, border_color=COLOR_BORDER):
    """Creates a card box container."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape


# ====================================================================
# SLIDE 1: Title Slide (Dark Theme)
# ====================================================================
slide1 = prs.slides.add_slide(blank_layout)

# Dark Background
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = COLOR_NAVY_DARK
bg1.line.fill.background()

# Decorative Accent Ribbon
ribbon = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.1))
ribbon.fill.solid()
ribbon.fill.fore_color.rgb = COLOR_PRIMARY_BLUE
ribbon.line.fill.background()

# Title text
title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.1), Inches(11.733), Inches(1.8))
tf = title_box.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "E-Learning Course Analytics System"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)

p_sub = tf.add_paragraph()
p_sub.text = "A Full-Stack Educational Intelligence, Engagement Monitoring & Course Completion Analytics Platform"
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = COLOR_ACCENT_BLUE

# Sub-info Card: Academic Department
dept_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.733), Inches(0.6))
tf_d = dept_box.text_frame
p_d = tf_d.paragraphs[0]
p_d.text = "Department of Computer Science & Engineering / Information Technology  |  B.Tech Final Year Project"
p_d.font.size = Pt(12)
p_d.font.color.rgb = RGBColor(203, 213, 225)

# 5 Team Member Cards
members = [
    ("Team Member 1 (Lead)", "Frontend UI/UX & Chart.js", "Roll: [Your Roll 1]"),
    ("Team Member 2", "Flask REST API Architect", "Roll: [Your Roll 2]"),
    ("Team Member 3", "MySQL Database Engineer", "Roll: [Your Roll 3]"),
    ("Team Member 4", "Pandas Analytics Engine", "Roll: [Your Roll 4]"),
    ("Team Member 5", "QA, Testing & Security", "Roll: [Your Roll 5]"),
]

card_w = Inches(2.2)
card_gap = Inches(0.18)
start_x = Inches(0.8)

for i, (name, role, roll) in enumerate(members):
    x = start_x + i * (card_w + card_gap)
    c = add_card(slide1, x, Inches(3.7), card_w, Inches(2.3), bg_color=COLOR_NAVY_LIGHT, border_color=COLOR_PRIMARY_BLUE)
    
    tb = slide1.shapes.add_textbox(x + Inches(0.1), Inches(3.8), card_w - Inches(0.2), Inches(2.1))
    tframe = tb.text_frame
    tframe.word_wrap = True
    
    p1 = tframe.paragraphs[0]
    p1.text = name
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    
    p2 = tframe.add_paragraph()
    p2.text = role
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_ACCENT_BLUE
    
    p3 = tframe.add_paragraph()
    p3.text = roll
    p3.font.size = Pt(10)
    p3.font.color.rgb = RGBColor(148, 163, 184)

# Project Guide Box
guide_box = slide1.shapes.add_textbox(Inches(0.8), Inches(6.3), Inches(11.733), Inches(0.6))
tf_g = guide_box.text_frame
p_g = tf_g.paragraphs[0]
p_g.text = "Under the Guidance of: [Faculty Guide / Mentor Name, Designation, Department]"
p_g.font.size = Pt(12)
p_g.font.color.rgb = COLOR_EMERALD
p_g.font.bold = True

slide1.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Lead (Member 1)\n"
    "Good morning respected evaluators, professors, and faculty guides. "
    "Today, our 5-member team is proud to present our college capstone project: "
    "'E-Learning Course Analytics System'. Our team consists of 5 members, each responsible for "
    "frontend design, backend REST APIs, database architecture, analytics, and software quality assurance."
)


# ====================================================================
# SLIDE 2: Problem Statement & Motivation
# ====================================================================
slide2 = prs.slides.add_slide(blank_layout)
create_header(slide2, "Problem Statement & Educational Motivation")

# Left Column: Problem Cards
add_card(slide2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb2_left = slide2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf2_l = tb2_left.text_frame
tf2_l.word_wrap = True

p = tf2_l.paragraphs[0]
p.text = "The E-Learning Engagement Dilemma"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_CRIMSON

bullets_left = [
    ("Explosive Online Enrollment", "Higher education institutions & colleges have adopted MOOCs, LMS, and online modules at scale."),
    ("High Student Dropout Rates", "Global e-learning data shows 70%–85% of registered learners fail to finish courses due to disengagement."),
    ("Lack of Proactive Early Warnings", "Instructors only discover dropouts after end-of-semester exams, when intervention is already too late."),
    ("Data Fragmentation", "Course registers, student IDs, and activity logs are trapped in disparate spreadsheets without automated insights.")
]

for title, desc in bullets_left:
    p_t = tf2_l.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf2_l.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

# Right Column: The Solution Vision
add_card(slide2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb2_right = slide2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf2_r = tb2_right.text_frame
tf2_r.word_wrap = True

p = tf2_r.paragraphs[0]
p.text = "Our Engineering Solution & Vision"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

bullets_right = [
    ("Dynamic Full-Stack Web Architecture", "Unified single-page admin portal connecting MySQL 8, Flask, and interactive Chart.js widgets."),
    ("Accurate Mathematical Analytics", "Real-time calculation of course completion rates without misleading percentage averaging."),
    ("Automated 14-Day Inactivity Flagging", "Instant algorithmic detection of uncompleted students with no activity for over 14 days."),
    ("Chronological Learning Trends", "Weekly activity tracking to visualize student study momentum over calendar weeks."),
    ("Exportable Academic Reports", "One-click streaming CSV exports and server-side Matplotlib chart generation.")
]

for title, desc in bullets_right:
    p_t = tf2_r.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf2_r.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide2.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 1 / Member 2\n"
    "In slide 2, we highlight why this project is critical for colleges. Traditional LMS solutions simply record that a student registered. "
    "They do not proactively identify when a student stops participating. Our system solves this with real-time analytics and automatic inactivity alerts."
)


# ====================================================================
# SLIDE 3: Existing Systems vs Proposed System
# ====================================================================
slide3 = prs.slides.add_slide(blank_layout)
create_header(slide3, "Comparative Analysis: Existing Systems vs. Proposed Solution")

# Add comparison container card
add_card(slide3, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))

# Create Table
rows, cols = 6, 3
left, top, width, height = Inches(1.1), Inches(1.9), Inches(11.133), Inches(4.5)
table_shape = slide3.shapes.add_table(rows, cols, left, top, width, height)
table = table_shape.table

# Set Column Widths
table.columns[0].width = Inches(2.6)
table.columns[1].width = Inches(4.2)
table.columns[2].width = Inches(4.333)

headers = ["Feature / Capability", "Conventional / Existing Approaches", "Our Proposed Analytics System"]
for col_idx, h in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY_DARK
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(255, 255, 255)

data = [
    ("Data Architecture", "Static spreadsheets or heavy proprietary LMS", "Relational MySQL 8.0 schema with normalized entities & referential integrity"),
    ("Completion Metric Calculation", "Manual calculations or naive averaging of course percentages", "Rigorous math: (Total Completed / Total Enrolled) * 100 with zero-division safety"),
    ("Inactive Learner Detection", "Manual audit; dropouts discovered only after final grading", "Automated SQL HAVING rule flagging >14 days of silence in real-time"),
    ("Activity Visualizations", "Static offline tables without temporal progression", "Live interactive Chart.js charts & server-side Matplotlib figures"),
    ("Extensibility & Auditing", "Closed vendor ecosystems; hard to export clean data", "REST API architecture with dynamic search & one-click CSV report exports")
]

for row_idx, (feat, exist, prop) in enumerate(data, start=1):
    c0 = table.cell(row_idx, 0)
    c0.text = feat
    c0.text_frame.paragraphs[0].font.bold = True
    c0.text_frame.paragraphs[0].font.size = Pt(11)
    
    c1 = table.cell(row_idx, 1)
    c1.text = exist
    c1.text_frame.paragraphs[0].font.size = Pt(10.5)
    c1.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_MUTED
    
    c2 = table.cell(row_idx, 2)
    c2.text = prop
    c2.text_frame.paragraphs[0].font.size = Pt(10.5)
    c2.text_frame.paragraphs[0].font.color.rgb = COLOR_PRIMARY_BLUE
    c2.text_frame.paragraphs[0].font.bold = True

slide3.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 2\n"
    "This slide demonstrates our literature review and gap analysis. "
    "We compared conventional spreadsheets and heavy vendor LMS tools against our purpose-built system. "
    "Notice how our system prevents mathematical flaws like averaging percentages across courses of unequal class sizes."
)


# ====================================================================
# SLIDE 4: System Architecture (3-Tier Layered Design)
# ====================================================================
slide4 = prs.slides.add_slide(blank_layout)
create_header(slide4, "System Architecture: 3-Tier Multi-Layer Design")

# 3 Column Architecture Cards
tiers = [
    ("1. PRESENTATION LAYER (FRONTEND)", COLOR_PRIMARY_BLUE, [
        "Bootstrap 5.3 Responsive Framework",
        "Modern SaaS Sidebar & Navigation",
        "Chart.js 4.4 Multi-dataset Bar Charts",
        "Chart.js Chronological Trend Lines",
        "Asynchronous Fetch API (Vanilla ES6+)",
        "Zero Page Reload CRUD Operations",
        "Real-Time Database Health Status Pill"
    ]),
    ("2. APPLICATION & ANALYTICS LAYER", COLOR_NAVY_LIGHT, [
        "Python 3.14 + Flask 3.1 REST Server",
        "Multi-threaded Request Handling (threaded=True)",
        "Dual-Engine Computation (Pandas & Native)",
        "Calendar Week Aggregation Engine",
        "Matplotlib Headless Chart Generator",
        "Safe CSV Report Streaming Pipeline",
        "Clean Error Handling (No Stacktraces)"
    ]),
    ("3. PERSISTENCE & DATA LAYER", COLOR_EMERALD, [
        "MySQL Server 8.0 Relational DBMS",
        "InnoDB ACID-Compliant Storage Engine",
        "UTF8MB4 Full Multilingual Encoding",
        "Referential Integrity & Foreign Keys",
        "Unique Key Duplicate Protections",
        "Optimized Indexes on Dates & Status",
        "Safe Cascading & Restricted Deletions"
    ])
]

col_w = Inches(3.7)
start_x = Inches(0.8)

for i, (title, color, items) in enumerate(tiers):
    x = start_x + i * (col_w + Inches(0.3))
    add_card(slide4, x, Inches(1.6), col_w, Inches(5.2))
    
    # Header tag
    header_box = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.6), col_w, Inches(0.65))
    header_box.fill.solid()
    header_box.fill.fore_color.rgb = color
    header_box.line.fill.background()
    
    tf_h = header_box.text_frame
    p_h = tf_h.paragraphs[0]
    p_h.text = title
    p_h.font.bold = True
    p_h.font.size = Pt(11)
    p_h.font.color.rgb = RGBColor(255, 255, 255)
    p_h.alignment = PP_ALIGN.CENTER
    
    # Content
    tb = slide4.shapes.add_textbox(x + Inches(0.2), Inches(2.35), col_w - Inches(0.4), Inches(4.3))
    tframe = tb.text_frame
    tframe.word_wrap = True
    for idx, item in enumerate(items):
        p = tframe.add_paragraph() if idx > 0 else tframe.paragraphs[0]
        p.text = f"✔  {item}"
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_NAVY_DARK
        p.space_after = Pt(8)

slide4.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 2 & Member 3\n"
    "Here we illustrate our multi-tier architecture. "
    "The presentation layer utilizes Bootstrap 5 and Chart.js. "
    "The application layer is powered by Flask and our analytics engine. "
    "The persistence layer is backed by MySQL 8.0 InnoDB with strict referential constraints."
)


# ====================================================================
# SLIDE 5: Database Schema & Entity Relationships
# ====================================================================
slide5 = prs.slides.add_slide(blank_layout)
create_header(slide5, "Relational Database Design & Schema Architecture")

# 4 Table Cards
tables_info = [
    ("courses (Table 1)", "Stores academic course catalog", [
        ("course_id", "INT AUTO_INCREMENT [PK]"),
        ("course_name", "VARCHAR(100) NOT NULL"),
        ("category", "VARCHAR(50) NOT NULL"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_PRIMARY_BLUE),
    
    ("learners (Table 2)", "Stores unique college roll numbers", [
        ("learner_id", "INT AUTO_INCREMENT [PK]"),
        ("roll_no", "VARCHAR(30) NOT NULL [UNIQUE]"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_NAVY_LIGHT),
    
    ("enrollments (Table 3)", "Learner course registrations & status", [
        ("enrollment_id", "INT AUTO_INCREMENT [PK]"),
        ("learner_id", "INT [FK -> learners.learner_id]"),
        ("course_id", "INT [FK -> courses.course_id]"),
        ("status", "ENUM('Enrolled','In Progress','Completed')"),
        ("CONSTRAINT", "UNIQUE KEY (learner_id, course_id)")
    ], COLOR_EMERALD),
    
    ("activities (Table 4)", "Timestamped learning submissions", [
        ("activity_id", "INT AUTO_INCREMENT [PK]"),
        ("enrollment_id", "INT [FK -> enrollments.enrollment_id]"),
        ("activity_type", "VARCHAR(50) [Lesson/Quiz/Project]"),
        ("completed", "BOOLEAN DEFAULT FALSE"),
        ("activity_date", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_AMBER)
]

w5 = Inches(5.6)
h5 = Inches(2.45)

positions = [
    (Inches(0.8), Inches(1.6)),
    (Inches(6.8), Inches(1.6)),
    (Inches(0.8), Inches(4.3)),
    (Inches(6.8), Inches(4.3))
]

for (tbl_name, desc, cols, col_tag), (pos_x, pos_y) in zip(tables_info, positions):
    add_card(slide5, pos_x, pos_y, w5, h5)
    
    # Tag
    tag_box = slide5.shapes.add_shape(MSO_SHAPE.RECTANGLE, pos_x, pos_y, w5, Inches(0.45))
    tag_box.fill.solid()
    tag_box.fill.fore_color.rgb = col_tag
    tag_box.line.fill.background()
    
    p = tag_box.text_frame.paragraphs[0]
    p.text = f"{tbl_name} — {desc}"
    p.font.bold = True
    p.font.size = Pt(10.5)
    p.font.color.rgb = RGBColor(255, 255, 255)
    
    tb = slide5.shapes.add_textbox(pos_x + Inches(0.2), pos_y + Inches(0.5), w5 - Inches(0.4), h5 - Inches(0.55))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, (col, ctype) in enumerate(cols):
        p_c = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p_c.text = f"• {col}: {ctype}"
        p_c.font.size = Pt(9.5)
        p_c.font.color.rgb = COLOR_NAVY_DARK

slide5.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 3 (Database Engineer)\n"
    "In slide 5, I will explain our MySQL schema design. "
    "We have 4 normalized tables. Notice the critical unique constraint on (learner_id, course_id) in enrollments: "
    "this guarantees at the database level that a student cannot be accidentally enrolled in the same course twice. "
    "All foreign keys enforce referential integrity."
)


# ====================================================================
# SLIDE 6: Key Analytics Formulas & Algorithms
# ====================================================================
slide6 = prs.slides.add_slide(blank_layout)
create_header(slide6, "Core Analytical Formulations & Detection Algorithms")

# Box 1: Course Completion Formula
add_card(slide6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(2.45))
tb6_1 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(2.2))
tf1 = tb6_1.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "1. Course Completion Rate Formula"
p.font.bold = True
p.font.size = Pt(14)
p.font.color.rgb = COLOR_PRIMARY_BLUE

bullets1 = [
    "Mathematical Definition: (Completed Enrollments / Total Enrollments) * 100",
    "Zero Division Guard: Evaluated with np.where() and fallback to 0.0% if total = 0",
    "Performance Benchmarking Thresholds:",
    "  • >= 75%: Excellent (Green)      • >= 50%: Good (Blue)",
    "  • >= 25%: Average (Amber)        • < 25%: Needs Attention (Red)"
]
for b in bullets1:
    p_b = tf1.add_paragraph()
    p_b.text = b
    p_b.font.size = Pt(10.5)
    p_b.font.color.rgb = COLOR_NAVY_DARK

# Box 2: Overall Platform Completion
add_card(slide6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(2.45))
tb6_2 = slide6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(2.2))
tf2 = tb6_2.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "2. Overall Completion Rate (No False Averaging)"
p.font.bold = True
p.font.size = Pt(14)
p.font.color.rgb = COLOR_EMERALD

bullets2 = [
    "Formula: (Total Completed Enrollments / Total Platform Enrollments) * 100",
    "Critical Academic Rule: Never average individual course percentages! Courses have unequal enrollment sizes (e.g. 50 students vs 5 students).",
    "Calculated directly from aggregated MySQL enrollment status counts."
]
for b in bullets2:
    p_b = tf2.add_paragraph()
    p_b.text = b
    p_b.font.size = Pt(10.5)
    p_b.font.color.rgb = COLOR_NAVY_DARK

# Box 3: Inactive Detection
add_card(slide6, Inches(0.8), Inches(4.3), Inches(11.733), Inches(2.5), bg_color=COLOR_LIGHT_GRAY)
tb6_3 = slide6.shapes.add_textbox(Inches(1.0), Inches(4.4), Inches(11.333), Inches(2.3))
tf3 = tb6_3.text_frame
tf3.word_wrap = True
p = tf3.paragraphs[0]
p.text = "3. Inactive Enrollment Detection Algorithm (14-Day Inactivity Rule)"
p.font.bold = True
p.font.size = Pt(14)
p.font.color.rgb = COLOR_CRIMSON

bullets3 = [
    "Definition of Inactivity: An enrollment is classified as Inactive if status != 'Completed' AND (has 0 activities OR latest activity is > 14 days old).",
    "Eliminating Duplicates with SQL Aggregation:",
    "   SELECT e.enrollment_id, l.roll_no, c.course_name, MAX(a.activity_date) AS last_activity, DATEDIFF(NOW(), MAX(a.activity_date)) AS days_inactive",
    "   FROM enrollments e JOIN learners l ON ... LEFT JOIN activities a ON ... WHERE e.status != 'Completed'",
    "   GROUP BY e.enrollment_id ... HAVING last_activity IS NULL OR days_inactive > 14;",
    "Dynamic Configurable Threshold: Instructors can adjust the 14-day threshold on the fly via API & UI."
]
for b in bullets3:
    p_b = tf3.add_paragraph()
    p_b.text = b
    p_b.font.size = Pt(10.5)
    p_b.font.color.rgb = COLOR_NAVY_DARK

slide6.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 4 (Data Analytics Specialist)\n"
    "In slide 6, I present our core computational logic. "
    "We pay special attention to mathematical rigor: overall completion rate is computed across all enrollments directly, "
    "rather than averaging course percentages. Our 14-day inactivity query uses GROUP BY and HAVING to ensure zero duplicate records."
)


# ====================================================================
# SLIDE 7: Dashboard Features & Visualizations
# ====================================================================
slide7 = prs.slides.add_slide(blank_layout)
create_header(slide7, "Admin Dashboard Features & Interactive Visualizations")

features = [
    ("Summary Metric Cards", "6 Live Real-Time KPI Cards", [
        "Total Courses, Total Learners",
        "Total Enrollments, Completed count",
        "Overall Platform Completion %",
        "Inactive Enrollments (> 14 days)"
    ], COLOR_PRIMARY_BLUE),
    ("Course Completion Analytics", "Chart.js Multi-Dataset Bar Chart", [
        "X-axis: Course Name",
        "Dual Y-axes: Completion % & Learner count",
        "Color-coded bars by completion bracket",
        "Interactive hover tooltips"
    ], COLOR_EMERALD),
    ("Weekly Activity Trends", "Chart.js Chronological Line Chart", [
        "Grouped by Calendar Week (Monday start)",
        "Tracks total learning submissions",
        "Distinguishes completed vs incomplete",
        "Date range filtering capabilities"
    ], COLOR_NAVY_LIGHT),
    ("Inactivity & Benchmarking", "Detection Tables & Actions", [
        "Dynamic threshold filter (default 14 days)",
        "Badges for performance tiers",
        "One-click 'Log Activity' shortcut",
        "Empty-state friendly messages"
    ], COLOR_AMBER)
]

card_w7 = Inches(2.7)
start_x7 = Inches(0.8)

for i, (title, sub, bullets, col_t) in enumerate(features):
    x = start_x7 + i * (card_w7 + Inches(0.3))
    add_card(slide7, x, Inches(1.6), card_w7, Inches(5.2))
    
    # Tag
    top_t = slide7.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.6), card_w7, Inches(0.7))
    top_t.fill.solid()
    top_t.fill.fore_color.rgb = col_t
    top_t.line.fill.background()
    p = top_t.text_frame.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER
    
    tb = slide7.shapes.add_textbox(x + Inches(0.15), Inches(2.4), card_w7 - Inches(0.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_s = tf.paragraphs[0]
    p_s.text = sub
    p_s.font.size = Pt(10.5)
    p_s.font.bold = True
    p_s.font.color.rgb = COLOR_TEXT_MUTED
    p_s.space_after = Pt(8)
    
    for b in bullets:
        p_b = tf.add_paragraph()
        p_b.text = f"✔ {b}"
        p_b.font.size = Pt(10)
        p_b.font.color.rgb = COLOR_NAVY_DARK
        p_b.space_after = Pt(6)

slide7.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 1 (Frontend UI/UX)\n"
    "Slide 7 walks through our interactive dashboard. "
    "All cards and charts reflect live MySQL state. "
    "The bar chart visualizes completion percentage alongside student counts, while the weekly line chart shows engagement trends over time."
)


# ====================================================================
# SLIDE 8: Team Roles & Work Distribution (5 Members)
# ====================================================================
slide8 = prs.slides.add_slide(blank_layout)
create_header(slide8, "5-Member Team Work Distribution & Technical Contributions")

team_details = [
    ("MEMBER 1: PROJECT LEAD & UI/UX", COLOR_PRIMARY_BLUE, [
        "Designed responsive SaaS interface in Bootstrap 5.3",
        "Developed interactive Chart.js visualizations (bar & line)",
        "Built dynamic search & filtering scripts (courses.js, dashboard.js)",
        "Implemented real-time database connection health indicator"
    ]),
    ("MEMBER 2: BACKEND & API ARCHITECT", COLOR_NAVY_LIGHT, [
        "Developed Flask application routes & HTTP status codes",
        "Built REST endpoints for Courses, Learners & Enrollments",
        "Engineered multi-threaded async execution (threaded=True)",
        "Implemented global JSON error handlers (400, 404, 409, 500)"
    ]),
    ("MEMBER 3: DATABASE & SQL ENGINEER", COLOR_EMERALD, [
        "Architected MySQL 8.0 schema with 4 normalized tables",
        "Implemented UNIQUE KEY constraints & cascade relationships",
        "Optimized indexes on dates, enrollment status & categories",
        "Authored database.sql with realistic academic seed data"
    ]),
    ("MEMBER 4: DATA ANALYTICS SPECIALIST", COLOR_AMBER, [
        "Programmed computational engine in analytics.py",
        "Developed calendar-week activity aggregation algorithm",
        "Built 14-day inactive enrollment detection SQL query",
        "Implemented dual-engine fallback (Pandas + native NumPy)"
    ]),
    ("MEMBER 5: QA, SECURITY & EXPORTS", COLOR_CRIMSON, [
        "Engineered streaming CSV export pipeline for 4 reports",
        "Implemented Matplotlib backend figure generation (Agg)",
        "Conducted unit tests, SQL injection validation & safe delete rules",
        "Benchmarked system latency: 14ms DB loopback & 94ms page render"
    ])
]

card_w8 = Inches(2.18)
start_x8 = Inches(0.8)

for i, (title, color_b, contribs) in enumerate(team_details):
    x = start_x8 + i * (card_w8 + Inches(0.18))
    add_card(slide8, x, Inches(1.6), card_w8, Inches(5.2))
    
    header = slide8.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.6), card_w8, Inches(0.75))
    header.fill.solid()
    header.fill.fore_color.rgb = color_b
    header.line.fill.background()
    p = header.text_frame.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(10)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER
    
    tb = slide8.shapes.add_textbox(x + Inches(0.12), Inches(2.45), card_w8 - Inches(0.24), Inches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, c in enumerate(contribs):
        p_c = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p_c.text = f"• {c}"
        p_c.font.size = Pt(9.5)
        p_c.font.color.rgb = COLOR_NAVY_DARK
        p_c.space_after = Pt(6)

slide8.notes_slide.notes_text_frame.text = (
    "SPEAKER: All Team Members (Each speaks for 30 seconds on their role)\n"
    "Member 1 explains UI/UX and Chart.js.\n"
    "Member 2 explains Flask REST endpoints and request flow.\n"
    "Member 3 explains MySQL schema design and constraints.\n"
    "Member 4 explains Pandas/NumPy analytics and math formulations.\n"
    "Member 5 explains CSV report streaming, testing, and security."
)


# ====================================================================
# SLIDE 9: Testing, Security & Benchmarking Results
# ====================================================================
slide9 = prs.slides.add_slide(blank_layout)
create_header(slide9, "Testing Verification, Security Hardening & Benchmarks")

# Card 1: Verified Benchmarks
add_card(slide9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb9_l = slide9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf9_l = tb9_l.text_frame
tf9_l.word_wrap = True

p = tf9_l.paragraphs[0]
p.text = "Verified Performance Benchmarks"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_EMERALD

benchmarks = [
    ("HTML Dashboard Load", "94 ms", "Sub-100 millisecond instantaneous page render"),
    ("Summary Analytics API", "216 ms", "Live calculation over real MySQL records"),
    ("MySQL Loopback Latency", "14 ms", "Direct IPv4 loopback connection speed"),
    ("Automated Test Suite", "14/14 Passed", "Unit tests for routing, templates, and analytics formulas")
]

for title, val, desc in benchmarks:
    p_t = tf9_l.add_paragraph()
    p_t.text = f"• {title}: {val}"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf9_l.add_paragraph()
    p_d.text = f"   ({desc})"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

# Card 2: Security Hardening
add_card(slide9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb9_r = slide9.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf9_r = tb9_r.text_frame
tf9_r.word_wrap = True

p = tf9_r.paragraphs[0]
p.text = "Security Hardening & Data Integrity"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

sec_points = [
    ("SQL Injection Prevention", "100% of user inputs use parameterized SQL queries (%s) across all routes."),
    ("Credential Protection", "Database passwords stored strictly in .env, never logged or exposed in client payloads."),
    ("Safe Deletion Checks", "Courses and learners with active enrollments cannot be deleted, preventing orphaned records."),
    ("Duplicate Prevention", "Database UNIQUE constraints on roll numbers and (learner_id, course_id) return HTTP 409 Conflict."),
    ("Clean Error Sanitization", "Database failures return structured user-friendly JSON without leaking server stack traces.")
]

for title, desc in sec_points:
    p_t = tf9_r.add_paragraph()
    p_t.text = f"🔒 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf9_r.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide9.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Member 5 (QA & Security Lead)\n"
    "In slide 9, we highlight our testing and security verification. "
    "All database operations use parameterized statements to prevent SQL injection. "
    "We verified 14 unit and integration tests, and our latency benchmark showed a 94ms page render time."
)


# ====================================================================
# SLIDE 10: Future Enhancements & Conclusion
# ====================================================================
slide10 = prs.slides.add_slide(blank_layout)
create_header(slide10, "Future Enhancements, Academic Impact & Conclusion")

# Left Column: Future Scope
add_card(slide10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb10_l = slide10.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf10_l = tb10_l.text_frame
tf10_l.word_wrap = True

p = tf10_l.paragraphs[0]
p.text = "Future Research & Expansion Scope"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

futures = [
    ("Machine Learning Predictive Dropout Model", "Train Random Forest / Logistic Regression classifier on activity frequency to predict dropout 3 weeks in advance."),
    ("Automated Nudge Notifications", "Automated email/SMS alerts sent via SMTP/Twilio when a student hits the 14-day inactivity mark."),
    ("Role-Based Access Control (RBAC)", "Dedicated portals for Students (self-progress) and Instructors (grading)."),
    ("Automated Digital Certificate Generation", "PDF certificate emission upon 100% course completion.")
]

for title, desc in futures:
    p_t = tf10_l.add_paragraph()
    p_t.text = f"🚀 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf10_l.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

# Right Column: Conclusion
add_card(slide10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb10_r = slide10.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf10_r = tb10_r.text_frame
tf10_r.word_wrap = True

p = tf10_r.paragraphs[0]
p.text = "Project Summary & Conclusion"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_EMERALD

conclusions = [
    ("Fully Realized B.Tech Project", "Successfully engineered a complete, production-grade 3-tier web application using Python, Flask, MySQL, and Chart.js."),
    ("Zero Hardcoding Principle", "100% of dashboard cards, charts, and tables are dynamically driven by real MySQL queries and Pandas/NumPy analytics."),
    ("Academic Problem Solved", "Provides administrators with actionable, early-warning insights into student retention and course effectiveness."),
    ("Collaborative Team Engineering", "Demonstrated clear division of technical responsibilities across frontend, backend, database, analytics, and QA.")
]

for title, desc in conclusions:
    p_t = tf10_r.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    
    p_d = tf10_r.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide10.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Lead (Member 1)\n"
    "In conclusion, our project demonstrates a full-stack, data-driven approach to solving online student dropouts. "
    "We have delivered an efficient, secure, and responsive platform that solves a real academic challenge."
)


# ====================================================================
# SLIDE 11: Thank You & Q&A Slide (Dark Theme)
# ====================================================================
slide11 = prs.slides.add_slide(blank_layout)

bg11 = slide11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg11.fill.solid()
bg11.fill.fore_color.rgb = COLOR_NAVY_DARK
bg11.line.fill.background()

tb_q = slide11.shapes.add_textbox(Inches(1.5), Inches(2.2), Inches(10.333), Inches(3.0))
tf_q = tb_q.text_frame
tf_q.word_wrap = True

p_q1 = tf_q.paragraphs[0]
p_q1.text = "Thank You!"
p_q1.font.size = Pt(44)
p_q1.font.bold = True
p_q1.font.color.rgb = RGBColor(255, 255, 255)
p_q1.alignment = PP_ALIGN.CENTER

p_q2 = tf_q.add_paragraph()
p_q2.text = "Questions & Faculty Feedback Are Welcome"
p_q2.font.size = Pt(22)
p_q2.font.color.rgb = COLOR_ACCENT_BLUE
p_q2.alignment = PP_ALIGN.CENTER
p_q2.space_before = Pt(15)

p_q3 = tf_q.add_paragraph()
p_q3.text = "Project Workspace: C:\\Users\\surug\\.gemini\\antigravity\\scratch\\elearning_analytics\nLive Server: http://127.0.0.1:5000"
p_q3.font.size = Pt(13)
p_q3.font.color.rgb = RGBColor(148, 163, 184)
p_q3.alignment = PP_ALIGN.CENTER
p_q3.space_before = Pt(25)

slide11.notes_slide.notes_text_frame.text = (
    "SPEAKER: Team Lead (Member 1)\n"
    "Thank you esteemed evaluators and professors for your time. "
    "We are now open to any technical, architectural, or analytical questions you may have."
)

# Save the presentation
output_path = os.path.join(os.path.dirname(__file__), "E_Learning_Course_Analytics_System_Presentation.pptx")
prs.save(output_path)
print(f"Presentation saved successfully at: {output_path}")
