"""
====================================================================
E-Learning Course Analytics System - Continuous Team PPT Generator
File: generate_continuous_ppt.py
Generates a structured 16:9 widescreen presentation organized with
continuous sequential slides for each of the 5 team members.
====================================================================
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
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

# Color mapping per team member
MEMBER_COLORS = {
    "MEMBER 1": COLOR_PRIMARY_BLUE,
    "MEMBER 2": COLOR_NAVY_LIGHT,
    "MEMBER 3": COLOR_EMERALD,
    "MEMBER 4": COLOR_AMBER,
    "MEMBER 5": COLOR_CRIMSON,
    "ALL": COLOR_PRIMARY_BLUE
}

blank_layout = prs.slide_layouts[6]


def create_slide_header(slide, title_text, speaker_tag, speaker_color=COLOR_PRIMARY_BLUE):
    """Creates a unified header with a prominent Speaker Identification Pill."""
    # Top Thin Bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = speaker_color
    bar.line.fill.background()

    # Category Pill
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(7.5), Inches(0.3))
    tf_c = cat_box.text_frame
    p_c = tf_c.paragraphs[0]
    p_c.text = "B.TECH CAPSTONE PROJECT DEFENSE  |  E-LEARNING ANALYTICS"
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_TEXT_MUTED

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(8.5), Inches(0.75))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(21)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_NAVY_DARK

    # Speaker Badge Pill (Right Corner)
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.3), Inches(0.45), Inches(3.2), Inches(0.65))
    badge.fill.solid()
    badge.fill.fore_color.rgb = speaker_color
    badge.line.fill.background()
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = speaker_tag.upper()
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = RGBColor(255, 255, 255)
    p_b.alignment = PP_ALIGN.CENTER


def add_card(slide, left, top, width, height, bg_color=COLOR_BG_CARD, border_color=COLOR_BORDER):
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
# SLIDE 1: Title Slide (Dark Theme - All Team Members)
# ====================================================================
slide1 = prs.slides.add_slide(blank_layout)
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = COLOR_NAVY_DARK
bg1.line.fill.background()

# Top accent
rib = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.08))
rib.fill.solid()
rib.fill.fore_color.rgb = COLOR_PRIMARY_BLUE
rib.line.fill.background()

# Title
t_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.733), Inches(1.8))
tf1 = t_box.text_frame
tf1.word_wrap = True
p = tf1.paragraphs[0]
p.text = "E-Learning Course Analytics System"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(255, 255, 255)

p_sub = tf1.add_paragraph()
p_sub.text = "A Data-Driven Educational Intelligence & Inactive Student Early-Warning Web Platform"
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = COLOR_ACCENT_BLUE

# Department info
d_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.75), Inches(11.733), Inches(0.5))
tf_d = d_box.text_frame
p_d = tf_d.paragraphs[0]
p_d.text = "Bachelor of Technology (B.Tech) Capstone Defense  |  Sequential 5-Member Team Presentation"
p_d.font.size = Pt(12)
p_d.font.color.rgb = RGBColor(203, 213, 225)

# 5 Team Member Cards
members = [
    ("MEMBER 1 (LEAD)", "Project Leadership, Problem & Gaps", "Roll: [Roll No 1]", COLOR_PRIMARY_BLUE),
    ("MEMBER 2", "Architecture & Flask REST APIs", "Roll: [Roll No 2]", COLOR_NAVY_LIGHT),
    ("MEMBER 3", "Database Engineering & MySQL 8", "Roll: [Roll No 3]", COLOR_EMERALD),
    ("MEMBER 4", "Analytics Engine & Math Models", "Roll: [Roll No 4]", COLOR_AMBER),
    ("MEMBER 5", "UI/UX, Security, QA & Benchmarks", "Roll: [Roll No 5]", COLOR_CRIMSON),
]

card_w = Inches(2.2)
card_gap = Inches(0.18)
start_x = Inches(0.8)

for i, (name, role, roll, col) in enumerate(members):
    x = start_x + i * (card_w + card_gap)
    add_card(slide1, x, Inches(3.6), card_w, Inches(2.4), bg_color=COLOR_NAVY_LIGHT, border_color=col)
    
    # Header strip inside card
    strip = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(3.6), card_w, Inches(0.4))
    strip.fill.solid()
    strip.fill.fore_color.rgb = col
    strip.line.fill.background()
    p_s = strip.text_frame.paragraphs[0]
    p_s.text = f"PART {i+1}"
    p_s.font.bold = True
    p_s.font.size = Pt(9.5)
    p_s.font.color.rgb = RGBColor(255, 255, 255)
    p_s.alignment = PP_ALIGN.CENTER

    tb = slide1.shapes.add_textbox(x + Inches(0.1), Inches(4.05), card_w - Inches(0.2), Inches(1.8))
    tframe = tb.text_frame
    tframe.word_wrap = True
    
    p1 = tframe.paragraphs[0]
    p1.text = name
    p1.font.size = Pt(11)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    
    p2 = tframe.add_paragraph()
    p2.text = role
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = COLOR_ACCENT_BLUE
    p2.space_before = Pt(4)
    
    p3 = tframe.add_paragraph()
    p3.text = roll
    p3.font.size = Pt(9.5)
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.space_before = Pt(4)

# Project Guide Box
g_box = slide1.shapes.add_textbox(Inches(0.8), Inches(6.35), Inches(11.733), Inches(0.5))
tf_g = g_box.text_frame
p_g = tf_g.paragraphs[0]
p_g.text = "Under the Guidance of: [Faculty Guide Name, Designation, Department]"
p_g.font.size = Pt(12)
p_g.font.color.rgb = COLOR_EMERALD
p_g.font.bold = True

slide1.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 (Lead)\n"
    "Good morning esteemed faculty members and evaluators. "
    "Our capstone presentation is organized into 5 continuous sequential sections, "
    "allowing each of our 5 team members to present their specialized technical subsystem in full detail."
)


# ====================================================================
# PART 1: TEAM MEMBER 1 (Slides 2, 3, 4)
# Project Leadership, Problem Statement, Objectives & Gaps
# ====================================================================

# Slide 2: Member 1 - Introduction & Educational Motivation
slide2 = prs.slides.add_slide(blank_layout)
create_slide_header(slide2, "Introduction & E-Learning Growth Paradigm", "SPEAKER: MEMBER 1 (LEAD)", COLOR_PRIMARY_BLUE)

add_card(slide2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb = slide2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "The Paradigm Shift in Higher Education"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

pts = [
    ("Massive Digitization", "Universities and colleges have transitioned heavily toward asynchronous online platforms and LMS portals."),
    ("Student Diversity", "Learners possess varying schedules, baseline skills, and engagement habits across technical disciplines."),
    ("Data Generation Surge", "Every video watched, quiz attempted, and project submitted generates rich behavioral metadata."),
    ("The Visibility Blindspot", "Instructors cannot physically see whether a student is keeping pace until high-stakes examinations.")
]
for title, desc in pts:
    p_t = tf.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb2 = slide2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf2 = tb2.text_frame
tf2.word_wrap = True
p2 = tf2.paragraphs[0]
p2.text = "Educational Intelligence Imperative"
p2.font.size = Pt(16)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

pts2 = [
    ("From Passive Tracking to Active Analytics", "Traditional systems only record 'Enrolled'. We need real-time behavioral progression tracking."),
    ("Quantifying Completion Velocity", "Distinguish between students who actively finish modules versus those stalled in early units."),
    ("Actionable Administrative Metrics", "Empower course administrators to evaluate curriculum difficulty and category effectiveness."),
    ("College Capstone Scope", "Deliver a standalone, production-grade analytics suite built on Python Flask and MySQL 8.")
]
for title, desc in pts2:
    p_t = tf2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide2.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 (Lead)\n"
    "In slide 2, I establish our project background. As online education has expanded, colleges have accumulated massive volumes "
    "of interaction data. However, administrators lack real-time visibility into whether students are genuinely progressing or quietly stalling."
)


# Slide 3: Member 1 - Problem Statement & Dropout Crisis
slide3 = prs.slides.add_slide(blank_layout)
create_slide_header(slide3, "Problem Statement: The Silent Student Dropout Crisis", "SPEAKER: MEMBER 1 (LEAD)", COLOR_PRIMARY_BLUE)

add_card(slide3, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
tb3 = slide3.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf3 = tb3.text_frame
tf3.word_wrap = True

p3 = tf3.paragraphs[0]
p3.text = "Core Academic Problem Defined"
p3.font.size = Pt(16)
p3.font.bold = True
p3.font.color.rgb = COLOR_CRIMSON

bullets3 = [
    ("70%–85% E-Learning Attrition", "Global educational research indicates that the vast majority of students drop out due to loss of engagement and lack of early academic follow-up."),
    ("The 'Post-Mortem' Evaluation Dilemma", "In conventional setups, dropouts are only officially recorded at the semester end during grade submission. By then, corrective academic interventions are impossible."),
    ("Uncalibrated Course Difficulty", "Without continuous analytics, department heads cannot determine whether low completion stems from overly demanding course material, poor content pacing, or lack of practice quizzes."),
    ("Need for Continuous Inactivity Auditing", "College administrators urgently require an algorithmic early-warning indicator that flags students who have been silent for more than 14 consecutive days."),
    ("Project Objective Statement", "To engineer a unified full-stack system providing real-time completion percentages, weekly activity momentum analysis, inactive learner detection, and audit report generation backed by a robust MySQL 8 database.")
]

for title, desc in bullets3:
    p_t = tf3.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf3.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_after = Pt(6)

slide3.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 (Lead)\n"
    "Slide 3 presents our formal problem statement. We address the silent dropout phenomenon. "
    "Traditional LMS reporting is 'post-mortem'—it only tells you someone failed after the course is already over. "
    "Our system focuses on live, actionable early intervention."
)


# Slide 4: Member 1 - Existing vs Proposed Gap Analysis Table
slide4 = prs.slides.add_slide(blank_layout)
create_slide_header(slide4, "Comparative Gap Analysis: Existing Systems vs. Ours", "SPEAKER: MEMBER 1 (LEAD)", COLOR_PRIMARY_BLUE)

add_card(slide4, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
table_shape = slide4.shapes.add_table(6, 3, Inches(1.1), Inches(1.85), Inches(11.133), Inches(4.6))
table = table_shape.table
table.columns[0].width = Inches(2.6)
table.columns[1].width = Inches(4.2)
table.columns[2].width = Inches(4.333)

headers = ["Evaluation Metric", "Existing Academic Approaches", "Our Proposed Analytics Platform"]
for col_idx, h in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY_DARK
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(11.5)
    p.font.color.rgb = RGBColor(255, 255, 255)

gaps = [
    ("Data Architecture", "Static spreadsheets or heavy proprietary LMS", "Relational MySQL 8.0 schema with normalized entities & referential integrity"),
    ("Completion Metric Calculation", "Manual calculations or naive averaging of course percentages", "Rigorous math: (Total Completed / Total Enrolled) * 100 with zero-division safety"),
    ("Inactive Learner Detection", "Manual audit; dropouts discovered only after final grading", "Automated SQL HAVING rule flagging >14 days of silence in real-time"),
    ("Activity Visualizations", "Static offline tables without temporal progression", "Live interactive Chart.js charts & server-side Matplotlib figures"),
    ("Extensibility & Auditing", "Closed vendor ecosystems; hard to export clean data", "REST API architecture with dynamic search & one-click CSV report exports")
]
for row_idx, (feat, exist, prop) in enumerate(gaps, start=1):
    c0 = table.cell(row_idx, 0)
    c0.text = feat
    c0.text_frame.paragraphs[0].font.bold = True
    c0.text_frame.paragraphs[0].font.size = Pt(10.5)
    
    c1 = table.cell(row_idx, 1)
    c1.text = exist
    c1.text_frame.paragraphs[0].font.size = Pt(10)
    c1.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_MUTED
    
    c2 = table.cell(row_idx, 2)
    c2.text = prop
    c2.text_frame.paragraphs[0].font.size = Pt(10)
    c2.text_frame.paragraphs[0].font.color.rgb = COLOR_PRIMARY_BLUE
    c2.text_frame.paragraphs[0].font.bold = True

slide4.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 (Lead)\n"
    "In slide 4, I conclude Part 1 with a comparative matrix. We evaluated conventional spreadsheets and LMS portals. "
    "Our proposed system replaces manual data collation with an automated, mathematical, and secure web application. "
    "I now hand over the presentation to Member 2 for System Architecture and REST API Engineering."
)


# ====================================================================
# PART 2: TEAM MEMBER 2 (Slides 5, 6, 7)
# Architecture, Flask REST APIs, Multi-Threading & Concurrency
# ====================================================================

# Slide 5: Member 2 - 3-Tier Layered Architecture
slide5 = prs.slides.add_slide(blank_layout)
create_slide_header(slide5, "System Architecture: 3-Tier Multi-Layer Design", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_NAVY_LIGHT)

tiers = [
    ("TIER 1: PRESENTATION LAYER", COLOR_PRIMARY_BLUE, [
        "Bootstrap 5.3 SaaS Admin Layout",
        "Responsive Sidebar Navigation",
        "Dual Chart.js 4.4 Canvas Rendering",
        "Vanilla ES6+ Asynchronous Fetch API",
        "Real-Time Database Status Pill",
        "Client-Side Form Validation Modals",
        "Zero-Page-Reload Dynamic Filtering"
    ]),
    ("TIER 2: APPLICATION LAYER", COLOR_NAVY_LIGHT, [
        "Python 3.14 + Flask 3.1 Framework",
        "REST API with JSON Status Codes",
        "Multi-Threaded Server (threaded=True)",
        "Dual-Engine Computation Fallback",
        "Automated Headless Matplotlib (Agg)",
        "Streaming CSV Export Pipeline",
        "Global Error & Exception Handling"
    ]),
    ("TIER 3: DATA PERSISTENCE LAYER", COLOR_EMERALD, [
        "MySQL Server 8.0 Relational DBMS",
        "InnoDB ACID Storage Engine",
        "Normalized 3NF Table Structure",
        "Foreign Key Constraints (RESTRICT/CASCADE)",
        "Composite UNIQUE Constraints",
        "B-Tree Indexes on Dates & Status",
        "Automated Seed Demonstration Data"
    ])
]

col_w = Inches(3.7)
start_x = Inches(0.8)

for i, (title, color, items) in enumerate(tiers):
    x = start_x + i * (col_w + Inches(0.3))
    add_card(slide5, x, Inches(1.6), col_w, Inches(5.2))
    
    hb = slide5.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.6), col_w, Inches(0.65))
    hb.fill.solid()
    hb.fill.fore_color.rgb = color
    hb.line.fill.background()
    p_h = hb.text_frame.paragraphs[0]
    p_h.text = title
    p_h.font.bold = True
    p_h.font.size = Pt(10.5)
    p_h.font.color.rgb = RGBColor(255, 255, 255)
    p_h.alignment = PP_ALIGN.CENTER
    
    tb = slide5.shapes.add_textbox(x + Inches(0.2), Inches(2.35), col_w - Inches(0.4), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, item in enumerate(items):
        p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p.text = f"✔ {item}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_NAVY_DARK
        p.space_after = Pt(7)

slide5.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 2 (Backend Architect)\n"
    "Thank you Member 1. In slide 5, I introduce our system architecture. "
    "We adopted a clean 3-tier separation of concerns. "
    "The presentation layer operates independently of the application layer, communicating exclusively via structured JSON REST APIs. "
    "The persistence layer guarantees ACID transactions in MySQL 8.0."
)


# Slide 6: Member 2 - Flask REST API Endpoints & Routes
slide6 = prs.slides.add_slide(blank_layout)
create_slide_header(slide6, "Flask REST API Routing & HTTP Status Contracts", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_NAVY_LIGHT)

add_card(slide6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb6_1 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf6_1 = tb6_1.text_frame
tf6_1.word_wrap = True
p = tf6_1.paragraphs[0]
p.text = "RESTful Resource Endpoints"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

api_routes = [
    ("GET /api/health", "System diagnostics & database table verification"),
    ("GET /api/dashboard/summary", "Top summary KPI card metrics"),
    ("GET /api/courses", "List courses with dynamic name/category search"),
    ("POST /api/courses", "Create course (validated name & category)"),
    ("DELETE /api/courses/<id>", "Safe course delete (fails if enrolled)"),
    ("GET /api/learners", "List learners with roll number search"),
    ("POST /api/learners", "Register learner (UNIQUE roll check)"),
    ("GET /api/enrollments", "Filter enrollments by course, status & search"),
    ("POST /api/enrollments", "Register student in course (duplicate guarded)")
]
for route, desc in api_routes:
    p_r = tf6_1.add_paragraph()
    p_r.text = f"• {route}"
    p_r.font.bold = True
    p_r.font.size = Pt(11)
    p_r.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf6_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb6_2 = slide6.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf6_2 = tb6_2.text_frame
tf6_2.word_wrap = True
p2 = tf6_2.paragraphs[0]
p2.text = "HTTP Status Code Standardization"
p2.font.size = Pt(16)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

codes = [
    ("200 OK", "Successful data retrieval and metric computation responses."),
    ("201 Created", "Resource successfully inserted into MySQL (new course, learner, enrollment, activity)."),
    ("400 Bad Request", "Missing required form fields or safe deletion rejection when enrollments exist."),
    ("404 Not Found", "Specified resource ID does not exist in the database."),
    ("409 Conflict", "Duplicate roll number or duplicate course enrollment detected."),
    ("503 Service Unavailable", "Clean database connection failure notice without exposing internal passwords or stack traces.")
]
for c_code, c_desc in codes:
    p_c = tf6_2.add_paragraph()
    p_c.text = f"✔ {c_code}:"
    p_c.font.bold = True
    p_c.font.size = Pt(11.5)
    p_c.font.color.rgb = COLOR_PRIMARY_BLUE
    p_cd = tf6_2.add_paragraph()
    p_cd.text = f"   {c_desc}"
    p_cd.font.size = Pt(10)
    p_cd.font.color.rgb = COLOR_TEXT_MUTED

slide6.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 2 (Backend Architect)\n"
    "Slide 6 details our REST API contracts. Every endpoint adheres strictly to HTTP semantic conventions. "
    "Notice the usage of 409 Conflict for duplicate registrations and 400 Bad Request to reject deletion of courses "
    "that currently have enrolled students. This prevents database corruption."
)


# Slide 7: Member 2 - Concurrency & Performance Optimization
slide7 = prs.slides.add_slide(blank_layout)
create_slide_header(slide7, "Backend Concurrency & Loopback Optimization", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_NAVY_LIGHT)

add_card(slide7, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
tb7 = slide7.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf7 = tb7.text_frame
tf7.word_wrap = True

p7 = tf7.paragraphs[0]
p7.text = "High-Performance Server Optimizations"
p7.font.size = Pt(16)
p7.font.bold = True
p7.font.color.rgb = COLOR_PRIMARY_BLUE

opts = [
    ("Parallel Multi-Threading (threaded=True)", "Enabled concurrent request servicing in Flask. When the dashboard opens, all 5 asynchronous API calls (Summary, Course Completion, Weekly Trends, Comparison, and Inactivity) are processed simultaneously in parallel threads rather than waiting in a serial blocking queue."),
    ("Direct IPv4 Loopback (127.0.0.1 vs localhost)", "On Windows platforms, 'localhost' causes the database connector to attempt IPv6 (::1) resolution first, causing a 200–400ms delay per query. By standardizing on direct IPv4 loopback (127.0.0.1), database connection latency dropped from ~200ms to 14ms (over 10x faster)."),
    ("Zombie Process Elimination (use_reloader=False)", "Configured the Flask runner with use_reloader=False to prevent Werkzeug from spawning orphaned background watcher processes that lock port 5000 in Windows CloseWait states."),
    ("Connection Lifecycle Management", "All database cursors and connections are explicitly closed inside try/finally blocks to prevent socket exhaustion and connection pool leaks."),
    ("Measured Latency Benchmark", "Full HTML dashboard render achieved in 94 ms, and the multi-table summary computation finishes in 216 ms.")
]

for title, desc in opts:
    p_t = tf7.add_paragraph()
    p_t.text = f"⚡ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf7.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_after = Pt(4)

slide7.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 2 (Backend Architect)\n"
    "In slide 7, I highlight our server concurrency engineering. "
    "We resolved a critical Windows latency issue by eliminating IPv6 DNS lookup overhead and configuring Flask with threaded multi-processing. "
    "I now hand over the presentation to Member 3 for Database Engineering and Schema Architecture."
)


# ====================================================================
# PART 3: TEAM MEMBER 3 (Slides 8, 9, 10)
# MySQL 8, Relational Schema, Constraints & Integrity
# ====================================================================

# Slide 8: Member 3 - MySQL Database Architecture
slide8 = prs.slides.add_slide(blank_layout)
create_slide_header(slide8, "Database Architecture: MySQL 8.0 & Storage Engine", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_EMERALD)

add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb8_1 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf8_1 = tb8_1.text_frame
tf8_1.word_wrap = True
p = tf8_1.paragraphs[0]
p.text = "Relational Storage Foundation"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = COLOR_EMERALD

db_pts = [
    ("MySQL Server 8.0 Community", "Enterprise-standard relational database management system."),
    ("InnoDB Storage Engine", "Full ACID compliance with row-level locking and transaction support."),
    ("utf8mb4 Character Encoding", "Universal Unicode support for international and multilingual course titles."),
    ("Connection Pool Integration", "Direct integration via mysql.connector with autocommit and timeout configurations.")
]
for title, desc in db_pts:
    p_t = tf8_1.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf8_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb8_2 = slide8.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf8_2 = tb8_2.text_frame
tf8_2.word_wrap = True
p2 = tf8_2.paragraphs[0]
p2.text = "Database Performance Indexing"
p2.font.size = Pt(16)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

idx_pts = [
    ("B-Tree Index on idx_course_category", "Optimizes category-level analytics and group comparisons."),
    ("B-Tree Index on idx_enrollment_status", "Accelerates filtering for Enrolled, In Progress, and Completed counts."),
    ("Index on idx_activity_date", "Essential for high-speed chronological range scans and weekly group-by aggregations."),
    ("Automated Workbench Script (database.sql)", "Single-click DDL script providing idempotent table creation and realistic academic test records.")
]
for title, desc in idx_pts:
    p_t = tf8_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_EMERALD
    p_d = tf8_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide8.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 3 (Database Engineer)\n"
    "Thank you Member 2. In slide 8, I present our database architecture. "
    "We selected MySQL 8 with the InnoDB engine to ensure strict ACID compliance. "
    "We placed strategic B-Tree indexes on activity dates and enrollment statuses to ensure analytics queries execute in milliseconds."
)


# Slide 9: Member 3 - Relational Schema & Tables
slide9 = prs.slides.add_slide(blank_layout)
create_slide_header(slide9, "Relational Schema: 4 Normalized Entities", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_EMERALD)

tables_info = [
    ("courses", "Academic Course Catalog", [
        ("course_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("course_name", "VARCHAR(100) NOT NULL"),
        ("category", "VARCHAR(50) NOT NULL"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_PRIMARY_BLUE),
    ("learners", "Student Profiles", [
        ("learner_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("roll_no", "VARCHAR(30) NOT NULL UNIQUE"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_NAVY_LIGHT),
    ("enrollments", "Registrations & Status Tracking", [
        ("enrollment_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("learner_id", "INT (FK -> learners)"),
        ("course_id", "INT (FK -> courses)"),
        ("status", "ENUM('Enrolled','In Progress','Completed')")
    ], COLOR_EMERALD),
    ("activities", "Timestamped Interaction Logs", [
        ("activity_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("enrollment_id", "INT (FK -> enrollments)"),
        ("activity_type", "VARCHAR(50) [Lesson/Quiz/Project]"),
        ("completed", "BOOLEAN DEFAULT FALSE")
    ], COLOR_AMBER)
]

w9 = Inches(5.6)
h9 = Inches(2.45)
pos9 = [
    (Inches(0.8), Inches(1.6)),
    (Inches(6.8), Inches(1.6)),
    (Inches(0.8), Inches(4.3)),
    (Inches(6.8), Inches(4.3))
]

for (tbl_name, desc, cols, col_tag), (pos_x, pos_y) in zip(tables_info, pos9):
    add_card(slide9, pos_x, pos_y, w9, h9)
    tag_box = slide9.shapes.add_shape(MSO_SHAPE.RECTANGLE, pos_x, pos_y, w9, Inches(0.45))
    tag_box.fill.solid()
    tag_box.fill.fore_color.rgb = col_tag
    tag_box.line.fill.background()
    p = tag_box.text_frame.paragraphs[0]
    p.text = f"{tbl_name.upper()} — {desc}"
    p.font.bold = True
    p.font.size = Pt(10.5)
    p.font.color.rgb = RGBColor(255, 255, 255)
    
    tb = slide9.shapes.add_textbox(pos_x + Inches(0.2), pos_y + Inches(0.5), w9 - Inches(0.4), h9 - Inches(0.55))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, (col, ctype) in enumerate(cols):
        p_c = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p_c.text = f"• {col}: {ctype}"
        p_c.font.size = Pt(9.5)
        p_c.font.color.rgb = COLOR_NAVY_DARK

slide9.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 3 (Database Engineer)\n"
    "Slide 9 displays our 4 normalized entities. "
    "Courses store subject offerings. Learners store students identified by their college roll numbers. "
    "Enrollments link learners to courses with a three-stage progress status. "
    "Activities record granular submissions such as quizzes, assignments, and projects."
)


# Slide 10: Member 3 - Integrity Constraints & Cascade Policies
slide10 = prs.slides.add_slide(blank_layout)
create_slide_header(slide10, "Integrity Constraints & Safe Deletion Enforcement", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_EMERALD)

add_card(slide10, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
tb10 = slide10.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf10 = tb10.text_frame
tf10.word_wrap = True

p10 = tf10.paragraphs[0]
p10.text = "Relational Integrity Rules"
p10.font.size = Pt(16)
p10.font.bold = True
p10.font.color.rgb = COLOR_EMERALD

rules = [
    ("Composite UNIQUE KEY Constraint (learner_id, course_id)", "Enforces at the database schema level that a student can never be enrolled in the same course more than once. Violations immediately raise MySQL Error 1062, caught cleanly by Flask to return HTTP 409 Conflict."),
    ("Foreign Key RESTRICT on Parent Deletion", "Learners and Courses employ ON DELETE RESTRICT on the enrollments table. An administrator cannot accidentally delete a course or student profile if active enrollment records exist, completely preventing orphaned child data."),
    ("Foreign Key CASCADE on Activities", "The activities table uses ON DELETE CASCADE linked to enrollments. If an enrollment is legitimately expunged, all associated sub-activity records are cleanly cleaned up, maintaining referential hygiene."),
    ("Roll Number Uniqueness (UNIQUE KEY on roll_no)", "Prevents student roll number collisions across academic batches."),
    ("Audit Demonstration Data", "The database seed script initializes 6 diverse courses, 8 student profiles, 13 enrollments, and realistic activity timestamps enabling immediate testing of active and inactive conditions.")
]

for title, desc in rules:
    p_t = tf10.add_paragraph()
    p_t.text = f"🔒 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf10.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_after = Pt(4)

slide10.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 3 (Database Engineer)\n"
    "In slide 10, I explain our integrity constraints. "
    "We enforce a composite UNIQUE constraint so duplicate enrollments are mathematically impossible. "
    "We also employ RESTRICT constraints to prevent accidental deletion of courses that have students registered. "
    "I now hand over to Member 4 to present our Computational Analytics and Algorithms."
)


# ====================================================================
# PART 4: TEAM MEMBER 4 (Slides 11, 12, 13)
# Analytics Engine, Mathematical Formulations & Algorithms
# ====================================================================

# Slide 11: Member 4 - Course Completion Rate Formulations
slide11 = prs.slides.add_slide(blank_layout)
create_slide_header(slide11, "Mathematical Formulations: Completion Analytics", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_AMBER)

add_card(slide11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb11_1 = slide11.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf11_1 = tb11_1.text_frame
tf11_1.word_wrap = True
p = tf11_1.paragraphs[0]
p.text = "1. Course Completion Rate Formula"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = COLOR_AMBER

f_pts = [
    ("Mathematical Formula", "Course Completion Rate = (Completed Enrollments / Total Enrollments) * 100"),
    ("Safe Division by Zero Guard", "If Total Enrollments = 0, evaluated via np.where() or conditional logic to return 0.0% instead of crashing with ZeroDivisionError."),
    ("Four Performance Tiers", "• Excellent (>= 75%): Green Badge\n• Good (>= 50%): Blue Badge\n• Average (>= 25%): Amber Badge\n• Needs Attention (< 25%): Red Badge")
]
for title, desc in f_pts:
    p_t = tf11_1.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf11_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide11, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb11_2 = slide11.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf11_2 = tb11_2.text_frame
tf11_2.word_wrap = True
p2 = tf11_2.paragraphs[0]
p2.text = "2. Overall Platform Completion"
p2.font.size = Pt(15)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

pts_overall = [
    ("The Mathematical Fallacy to Avoid", "CRITICAL RULE: Never average individual course percentages! Averaging percentages produces skewed and invalid figures when courses have unequal enrollments (e.g., a course with 100 students vs. a course with 2 students)."),
    ("True Mathematical Definition", "Overall Rate = (Total Completed Enrollments / Total Platform Enrollments) * 100"),
    ("Direct SQL Computation", "Aggregated directly across all enrollment records in MySQL, guaranteeing mathematically rigorous institutional reporting.")
]
for title, desc in pts_overall:
    p_t = tf11_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_PRIMARY_BLUE
    p_d = tf11_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide11.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 4 (Data Analytics Specialist)\n"
    "Thank you Member 3. In slide 11, I present our mathematical foundations. "
    "We enforced mathematical rigor: overall completion rate is computed by dividing total completed students across the entire institution "
    "by total enrollments. We avoid the classic student mistake of averaging course percentages."
)


# Slide 12: Member 4 - Inactive Enrollment Detection Algorithm
slide12 = prs.slides.add_slide(blank_layout)
create_slide_header(slide12, "Algorithm: Inactive Enrollment Detection (14-Day Rule)", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_AMBER)

add_card(slide12, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
tb12 = slide12.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf12 = tb12.text_frame
tf12.word_wrap = True

p12 = tf12.paragraphs[0]
p12.text = "The 14-Day Inactivity Detection Algorithm"
p12.font.size = Pt(16)
p12.font.bold = True
p12.font.color.rgb = COLOR_CRIMSON

algo_pts = [
    ("Formal Inactivity Definition", "An enrollment is classified as Inactive if: (1) status != 'Completed', AND (2) either no activities have been logged OR the most recent activity is older than 14 days (DATEDIFF(NOW(), last_activity) > 14)."),
    ("Parameterized SQL Aggregation with HAVING", "SELECT e.enrollment_id, l.roll_no, c.course_name, MAX(a.activity_date) AS last_activity, DATEDIFF(NOW(), MAX(a.activity_date)) AS days_inactive\nFROM enrollments e JOIN learners l ... LEFT JOIN activities a ...\nWHERE e.status != 'Completed' GROUP BY e.enrollment_id ...\nHAVING last_activity IS NULL OR days_inactive > %s;"),
    ("Eliminating Duplicate Records", "Using GROUP BY on enrollment_id with MAX(activity_date) ensures that even if a student has logged dozens of activities in the past, they appear exactly once in the detection table."),
    ("Dynamic Configurable Threshold", "The 14-day threshold is not hardcoded. Administrators can dynamically filter by 7, 14, 21, or 30 days via the API and dashboard controls.")
]

for title, desc in algo_pts:
    p_t = tf12.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf12.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_after = Pt(4)

slide12.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 4 (Data Analytics Specialist)\n"
    "In slide 12, I detail our early-warning inactivity algorithm. "
    "We evaluate inactivity dynamically using SQL HAVING clauses. "
    "Students who have never logged in, as well as students whose last submission was over 14 days ago, are instantly flagged for intervention."
)


# Slide 13: Member 4 - Weekly Activity Aggregation & Dual-Engine Fallback
slide13 = prs.slides.add_slide(blank_layout)
create_slide_header(slide13, "Weekly Activity Aggregation & Dual-Engine Architecture", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_AMBER)

add_card(slide13, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb13_1 = slide13.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf13_1 = tb13_1.text_frame
tf13_1.word_wrap = True
p = tf13_1.paragraphs[0]
p.text = "Weekly Activity Resampling"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = COLOR_AMBER

pts_wk = [
    ("Calendar Week Resampling", "Groups activities by weekly periods starting on Monday using pd.to_period('W-SUN') and ISO week numbering (e.g. 2026-W41)."),
    ("Chronological Progression", "Aggregates total submissions, completed activities, and pending activities in chronological sequence."),
    ("Date Range Filtering", "Supports optional start_date and end_date query parameters for term-based or monthly activity audits.")
]
for title, desc in pts_wk:
    p_t = tf13_1.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf13_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide13, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb13_2 = slide13.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf13_2 = tb13_2.text_frame
tf13_2.word_wrap = True
p2 = tf13_2.paragraphs[0]
p2.text = "Resilient Dual-Engine Fallback"
p2.font.size = Pt(15)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

pts_dual = [
    ("Primary Engine: Pandas & NumPy", "Utilizes vectorized DataFrame aggregations for large-scale data processing."),
    ("Secondary Engine: Native Python & SQL", "If platform security policies (such as Windows AppLocker or missing C-extensions) restrict Pandas DLLs, the analytics engine automatically falls back to native Python datetime and SQL cursor dictionaries."),
    ("Zero System Downtime", "Guarantees that the web application and analytics dashboard never crash, maintaining 100% server uptime.")
]
for title, desc in pts_dual:
    p_t = tf13_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_PRIMARY_BLUE
    p_d = tf13_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide13.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 4 (Data Analytics Specialist)\n"
    "In slide 13, I conclude Part 4 by explaining our dual-engine architecture. "
    "We built a graceful fallback mechanism: if Pandas is available, it uses vector math; if not, it seamlessly switches to native Python. "
    "I now hand over the presentation to Member 5 for UI/UX, Security, Testing, and Live Demonstration."
)


# ====================================================================
# PART 5: TEAM MEMBER 5 (Slides 14, 15, 16)
# UI/UX, Security Hardening, Testing Suite & Benchmarks
# ====================================================================

# Slide 14: Member 5 - Dashboard Visualizations & Interface
slide14 = prs.slides.add_slide(blank_layout)
create_slide_header(slide14, "User Interface: Dashboard & Visual Analytics", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_CRIMSON)

cards_ui = [
    ("Summary KPI Cards", "6 Live Real-Time Metrics", [
        "Total Courses, Learners",
        "Total & Completed Enrollments",
        "Overall Platform Completion %",
        "Inactive Enrollments (> 14d)"
    ], COLOR_PRIMARY_BLUE),
    ("Course Completion Chart", "Chart.js Bar Visualization", [
        "X-axis: Course Titles",
        "Dual Y-axes: % & Student counts",
        "Color-coded by performance",
        "Dynamic hover tooltips"
    ], COLOR_EMERALD),
    ("Weekly Trends Chart", "Chart.js Line Visualization", [
        "Calendar week timestamps",
        "Tracks total learning volume",
        "Shows completed submissions",
        "Chronological trend curves"
    ], COLOR_NAVY_LIGHT),
    ("Benchmark & Detection", "Interactive Data Grids", [
        "Configurable threshold filter",
        "Direct 'Log Activity' action link",
        "Sub-100ms UI render speed",
        "Zero page reload updates"
    ], COLOR_AMBER)
]

w14 = Inches(2.7)
start_x14 = Inches(0.8)

for i, (title, sub, bullets, col_t) in enumerate(cards_ui):
    x = start_x14 + i * (w14 + Inches(0.3))
    add_card(slide14, x, Inches(1.6), w14, Inches(5.2))
    
    top_t = slide14.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.6), w14, Inches(0.7))
    top_t.fill.solid()
    top_t.fill.fore_color.rgb = col_t
    top_t.line.fill.background()
    p = top_t.text_frame.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER
    
    tb = slide14.shapes.add_textbox(x + Inches(0.15), Inches(2.4), w14 - Inches(0.3), Inches(4.3))
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

slide14.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 5 (UI/UX & QA Lead)\n"
    "Thank you Member 4. In slide 14, I walk through our user interface. "
    "We designed a modern SaaS layout with Bootstrap 5. "
    "All cards, Chart.js bar charts, and weekly trend graphs are populated dynamically via fetch API calls without full-page reloads."
)


# Slide 15: Member 5 - Security Hardening & CSV Exports
slide15 = prs.slides.add_slide(blank_layout)
create_slide_header(slide15, "Security Hardening & Report Generation Pipeline", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_CRIMSON)

add_card(slide15, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb15_1 = slide15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf15_1 = tb15_1.text_frame
tf15_1.word_wrap = True
p = tf15_1.paragraphs[0]
p.text = "Security Architecture"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = COLOR_CRIMSON

sec_pts = [
    ("100% Parameterized SQL", "Zero string concatenation. Every user input is bound to parameterized %s placeholders, eliminating SQL Injection vulnerabilities."),
    ("Environment Isolation (.env)", "Database credentials and secret keys are stored strictly in environment variables and never committed to source control or exposed in browser APIs."),
    ("Referential Protection", "Foreign key constraints prevent deletion of courses with active students, safeguarding data integrity."),
    ("Graceful Error Sanitization", "Database failures return structured JSON error messages without leaking server stack traces.")
]
for title, desc in sec_pts:
    p_t = tf15_1.add_paragraph()
    p_t.text = f"🔒 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf15_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide15, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb15_2 = slide15.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf15_2 = tb15_2.text_frame
tf15_2.word_wrap = True
p2 = tf15_2.paragraphs[0]
p2.text = "Academic Report Generation"
p2.font.size = Pt(15)
p2.font.bold = True
p2.font.color.rgb = COLOR_PRIMARY_BLUE

rep_pts = [
    ("4 Exportable CSV Reports", "One-click streaming of Course Completion, Inactive Enrollments, Weekly Activity, and Course Comparison."),
    ("In-Memory Streaming", "Generated via Python io.StringIO and streamed with Content-Disposition headers for instant browser downloads."),
    ("Headless Matplotlib Charts", "Server-side generation of high-resolution 120 DPI PNG figures saved to static/charts/ for academic archiving."),
    ("Timestamped Filenames", "Exported files use standardized naming (report_YYYYMMDD_HHMMSS.csv) for compliance and auditing.")
]
for title, desc in rep_pts:
    p_t = tf15_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_PRIMARY_BLUE
    p_d = tf15_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide15.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 5 (UI/UX & QA Lead)\n"
    "Slide 15 covers security and data exports. "
    "We secured the application against SQL injection using parameterized queries across all endpoints. "
    "We also implemented streaming CSV report downloads and server-side Matplotlib chart generation."
)


# Slide 16: Member 5 - Testing Suite & Benchmark Results
slide16 = prs.slides.add_slide(blank_layout)
create_slide_header(slide16, "Verification Testing Suite & Latency Benchmarks", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_CRIMSON)

add_card(slide16, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.2))
tb16 = slide16.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.133), Inches(4.8))
tf16 = tb16.text_frame
tf16.word_wrap = True

p16 = tf16.paragraphs[0]
p16.text = "Comprehensive Quality Assurance & Benchmark Results"
p16.font.size = Pt(16)
p16.font.bold = True
p16.font.color.rgb = COLOR_EMERALD

test_pts = [
    ("14/14 Automated Integration Tests Passed", "Verified template rendering, REST endpoints, database connection error recovery, and CSV file streaming."),
    ("Sub-100 Millisecond Page Load (94 ms)", "Measured HTML dashboard load time is just 94 ms due to render-blocking script deferral and direct IPv4 loopback."),
    ("Real MySQL Summary API Execution (216 ms)", "Calculates total courses, total learners, enrollments, completion rates, and inactive students across the entire database in ~200ms."),
    ("Database Loopback Latency (14 ms)", "Standardizing on direct IPv4 (127.0.0.1) reduced database query initialization to a negligible 14 milliseconds."),
    ("Edge Case Validation Verified", "Tested safe handling of 0 enrollments, duplicate roll numbers (409 Conflict), duplicate course enrollment attempts, and invalid activity types.")
]

for title, desc in test_pts:
    p_t = tf16.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(12)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf16.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED
    p_d.space_after = Pt(4)

slide16.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 5 (UI/UX & QA Lead)\n"
    "In slide 16, I present our QA benchmarks. "
    "We verified 14 integration tests. Our benchmark confirms a sub-100 millisecond page render time and a 14ms database loopback speed. "
    "All edge cases, such as 0 enrollments and duplicate submissions, were thoroughly validated. "
    "I now hand back to Member 1 and the whole team for Future Scope and Conclusion."
)


# ====================================================================
# CONCLUSION & DEFENSE: ALL MEMBERS (Slides 17, 18)
# ====================================================================

# Slide 17: All Members - Future Scope & Enhancements
slide17 = prs.slides.add_slide(blank_layout)
create_slide_header(slide17, "Future Enhancements & Research Scope", "SPEAKER: ALL TEAM MEMBERS", COLOR_PRIMARY_BLUE)

add_card(slide17, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
tb17_1 = slide17.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))
tf17_1 = tb17_1.text_frame
tf17_1.word_wrap = True
p = tf17_1.paragraphs[0]
p.text = "Advanced Academic Features"
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = COLOR_PRIMARY_BLUE

f_items1 = [
    ("Predictive ML Dropout Forecasting", "Train a Random Forest or Logistic Regression classifier on student submission velocity to predict dropout risk 3 weeks in advance."),
    ("Automated Nudge Notifications", "Integrate automated email / SMS alerts to gently remind students when they cross the 14-day inactivity mark."),
    ("Digital Certificate Generation", "Automatic generation and verification of PDF certificates upon reaching 100% activity completion.")
]
for title, desc in f_items1:
    p_t = tf17_1.add_paragraph()
    p_t.text = f"🚀 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_d = tf17_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide17, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), bg_color=COLOR_LIGHT_GRAY)
tb17_2 = slide17.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.8))
tf17_2 = tb17_2.text_frame
tf17_2.word_wrap = True
p2 = tf17_2.paragraphs[0]
p2.text = "Platform Expansion"
p2.font.size = Pt(15)
p2.font.bold = True
p2.font.color.rgb = COLOR_EMERALD

f_items2 = [
    ("Role-Based Access Control (RBAC)", "Multi-tenant authentication with dedicated portals for Students (self-paced tracking) and Instructors (grading)."),
    ("Cross-Platform Mobile App", "Complement the web dashboard with a Flutter or React Native mobile application for student push notifications."),
    ("LTI / Canvas / Moodle Integration", "Learning Tools Interoperability (LTI) plugin for plug-and-play adoption across university systems.")
]
for title, desc in f_items2:
    p_t = tf17_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(11.5)
    p_t.font.color.rgb = COLOR_EMERALD
    p_d = tf17_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

slide17.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 & All Members\n"
    "In slide 17, we outline our roadmap. We plan to integrate predictive machine learning models to forecast dropout risk "
    "and add automated email notifications to nudge students back into active learning."
)


# Slide 18: All Members - Conclusion & Q&A
slide18 = prs.slides.add_slide(blank_layout)
bg18 = slide18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg18.fill.solid()
bg18.fill.fore_color.rgb = COLOR_NAVY_DARK
bg18.line.fill.background()

tb_qa = slide18.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.0))
tf_qa = tb_qa.text_frame
tf_qa.word_wrap = True

p_q1 = tf_qa.paragraphs[0]
p_q1.text = "Thank You!"
p_q1.font.size = Pt(44)
p_q1.font.bold = True
p_q1.font.color.rgb = RGBColor(255, 255, 255)
p_q1.alignment = PP_ALIGN.CENTER

p_q2 = tf_qa.add_paragraph()
p_q2.text = "E-Learning Course Analytics System"
p_q2.font.size = Pt(22)
p_q2.font.bold = True
p_q2.font.color.rgb = COLOR_ACCENT_BLUE
p_q2.alignment = PP_ALIGN.CENTER
p_q2.space_before = Pt(12)

p_q3 = tf_qa.add_paragraph()
p_q3.text = "Presented by 5-Member Engineering Team:\nMember 1 (Lead)  •  Member 2 (Backend)  •  Member 3 (Database)  •  Member 4 (Analytics)  •  Member 5 (QA & UI)"
p_q3.font.size = Pt(13)
p_q3.font.color.rgb = RGBColor(203, 213, 225)
p_q3.alignment = PP_ALIGN.CENTER
p_q3.space_before = Pt(15)

p_q4 = tf_qa.add_paragraph()
p_q4.text = "Questions, Faculty Feedback & Technical Discussion Are Welcome"
p_q4.font.size = Pt(14)
p_q4.font.color.rgb = COLOR_EMERALD
p_q4.font.bold = True
p_q4.alignment = PP_ALIGN.CENTER
p_q4.space_before = Pt(20)

slide18.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 & Team\n"
    "Thank you respected professors and evaluators. "
    "We are now ready for your questions and live demonstration."
)

# Save
output_path = os.path.join(os.path.dirname(__file__), "E_Learning_Analytics_5_Members_Continuous.pptx")
prs.save(output_path)
print(f"Continuous PPT saved successfully at: {output_path}")
