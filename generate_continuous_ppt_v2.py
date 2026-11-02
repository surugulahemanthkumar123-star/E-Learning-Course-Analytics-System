"""
====================================================================
E-Learning Course Analytics System - PPT Generator (Enhanced Theme & Typography)
File: generate_continuous_ppt_v2.py
Features:
- Larger, high-contrast, projector-optimized font sizes (Titles: 26pt, Body: 13-14pt)
- Modern Executive Theme (Crisp Slate canvas, accent color cards, high contrast)
- Slide 1 Spacious Design with dedicated areas for College Logo, Names, Rolls, Guide
- Continuous 3-slide sequential blocks for each of the 5 team members
====================================================================
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Modern Executive Color Theme
COLOR_BG_PAGE = RGBColor(248, 250, 252)     # #f8fafc (Crisp Canvas)
COLOR_CARD_BG = RGBColor(255, 255, 255)     # #ffffff (Pure White Card)
COLOR_CARD_ALT = RGBColor(241, 245, 249)    # #f1f5f9 (Soft Light Slate)
COLOR_NAVY_DARK = RGBColor(15, 23, 42)      # #0f172a (Primary Deep Slate Text)
COLOR_TEXT_BODY = RGBColor(30, 41, 59)      # #1e293b (High-Contrast Body)
COLOR_TEXT_MUTED = RGBColor(71, 85, 105)    # #475569 (Secondary Text)
COLOR_BORDER = RGBColor(203, 213, 225)      # #cbd5e1 (Clean Card Border)
COLOR_ACCENT_BLUE = RGBColor(56, 189, 248)  # #38bdf8 (Light Blue Accent)

# Team Member Distinct Accents
COLOR_M1 = RGBColor(37, 99, 235)   # Royal Blue (Member 1 - Lead & Problem)
COLOR_M2 = RGBColor(79, 70, 229)   # Indigo (Member 2 - Architecture & APIs)
COLOR_M3 = RGBColor(5, 150, 105)   # Emerald Green (Member 3 - Database & SQL)
COLOR_M4 = RGBColor(217, 119, 6)   # Amber Bronze (Member 4 - Analytics & Math)
COLOR_M5 = RGBColor(225, 29, 72)   # Rose Crimson (Member 5 - UI/UX, Security & QA)
COLOR_EMERALD = RGBColor(16, 185, 129)  # Emerald Green

blank_layout = prs.slide_layouts[6]


def apply_page_background(slide, color=COLOR_BG_PAGE):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg


def create_slide_header(slide, title_text, speaker_tag, speaker_color=COLOR_M1):
    """Creates a modern header with larger fonts and prominent speaker badge."""
    apply_page_background(slide)

    # Top accent line
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = speaker_color
    bar.line.fill.background()

    # Supertitle / Breadcrumb
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(7.5), Inches(0.3))
    tf_c = cat_box.text_frame
    p_c = tf_c.paragraphs[0]
    p_c.text = "B.TECH CAPSTONE PROJECT DEFENSE  |  E-LEARNING ANALYTICS SYSTEM"
    p_c.font.size = Pt(11)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_TEXT_MUTED

    # Slide Title (Enlarged 25pt)
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(8.5), Inches(0.8))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.size = Pt(25)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_NAVY_DARK

    # Speaker Badge (Top Right)
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.1), Inches(0.42), Inches(3.4), Inches(0.72))
    badge.fill.solid()
    badge.fill.fore_color.rgb = speaker_color
    badge.line.fill.background()
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = speaker_tag.upper()
    p_b.font.size = Pt(12)
    p_b.font.bold = True
    p_b.font.color.rgb = RGBColor(255, 255, 255)
    p_b.alignment = PP_ALIGN.CENTER


def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    return shape


# ====================================================================
# SLIDE 1: Title Slide (Redesigned with Spacious Layout & Clear Placeholders)
# ====================================================================
slide1 = prs.slides.add_slide(blank_layout)
apply_page_background(slide1, RGBColor(248, 250, 252))

# Top Accent Strip
strip1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
strip1.fill.solid()
strip1.fill.fore_color.rgb = COLOR_M1
strip1.line.fill.background()

# Space 1: Dedicated College / Institution Header Box (Spacious)
college_box = add_card(slide1, Inches(0.8), Inches(0.45), Inches(11.733), Inches(0.9), bg_color=RGBColor(255, 255, 255), border_color=COLOR_BORDER)
tb_col = slide1.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(11.333), Inches(0.8))
tf_col = tb_col.text_frame
tf_col.word_wrap = True
p_col1 = tf_col.paragraphs[0]
p_col1.text = "[ YOUR COLLEGE / UNIVERSITY NAME HERE ]"
p_col1.font.size = Pt(15)
p_col1.font.bold = True
p_col1.font.color.rgb = COLOR_M1
p_col1.alignment = PP_ALIGN.CENTER

p_col2 = tf_col.add_paragraph()
p_col2.text = "Department of Computer Science & Engineering  |  Bachelor of Technology (B.Tech) Final Year Defense"
p_col2.font.size = Pt(11.5)
p_col2.font.color.rgb = COLOR_TEXT_MUTED
p_col2.alignment = PP_ALIGN.CENTER

# Space 2: Major Project Title Box (Spacious Center)
title_card = add_card(slide1, Inches(0.8), Inches(1.5), Inches(11.733), Inches(1.7), bg_color=RGBColor(15, 23, 42), border_color=None)
tb_t1 = slide1.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.333), Inches(1.5))
tf_t1 = tb_t1.text_frame
tf_t1.word_wrap = True

p1 = tf_t1.paragraphs[0]
p1.text = "E-Learning Course Analytics System"
p1.font.size = Pt(32)
p1.font.bold = True
p1.font.color.rgb = RGBColor(255, 255, 255)
p1.alignment = PP_ALIGN.CENTER

p1_sub = tf_t1.add_paragraph()
p1_sub.text = "A Full-Stack Educational Intelligence, Engagement Monitoring & Inactivity Detection Platform"
p1_sub.font.size = Pt(15)
p1_sub.font.color.rgb = COLOR_ACCENT_BLUE
p1_sub.alignment = PP_ALIGN.CENTER
p1_sub.space_before = Pt(8)

# Space 3: 5 Team Member Placeholders (Generous Width & Blank Space for Editing)
member_box = add_card(slide1, Inches(0.8), Inches(3.35), Inches(11.733), Inches(2.6), bg_color=RGBColor(255, 255, 255), border_color=COLOR_BORDER)

# Member Header Strip
m_hdr = slide1.shapes.add_textbox(Inches(1.0), Inches(3.45), Inches(11.333), Inches(0.4))
tf_mh = m_hdr.text_frame
p_mh = tf_mh.paragraphs[0]
p_mh.text = "PROJECT PRESENTATION TEAM ROSTER (5 MEMBERS):"
p_mh.font.size = Pt(12)
p_mh.font.bold = True
p_mh.font.color.rgb = COLOR_NAVY_DARK

# 5 Spacious Column Cards for Members
m_w = Inches(2.18)
m_gap = Inches(0.18)
m_x0 = Inches(1.0)

team_spaces = [
    ("MEMBER 1 (LEAD)", "Name: _______________", "Roll No: _____________", "Role: UI & Problem Scope", COLOR_M1),
    ("MEMBER 2", "Name: _______________", "Roll No: _____________", "Role: Architecture & APIs", COLOR_M2),
    ("MEMBER 3", "Name: _______________", "Roll No: _____________", "Role: MySQL Database", COLOR_M3),
    ("MEMBER 4", "Name: _______________", "Roll No: _____________", "Role: Analytics Engine", COLOR_M4),
    ("MEMBER 5", "Name: _______________", "Roll No: _____________", "Role: QA, Security & Demo", COLOR_M5)
]

for idx, (m_tag, m_name, m_roll, m_role, m_col) in enumerate(team_spaces):
    x_pos = m_x0 + idx * (m_w + m_gap)
    # Mini card
    mc = add_card(slide1, x_pos, Inches(3.9), m_w, Inches(1.9), bg_color=COLOR_CARD_ALT, border_color=m_col)
    
    tb_m = slide1.shapes.add_textbox(x_pos + Inches(0.08), Inches(3.95), m_w - Inches(0.16), Inches(1.8))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    
    pm1 = tf_m.paragraphs[0]
    pm1.text = m_tag
    pm1.font.bold = True
    pm1.font.size = Pt(11)
    pm1.font.color.rgb = m_col
    
    pm2 = tf_m.add_paragraph()
    pm2.text = m_name
    pm2.font.size = Pt(10.5)
    pm2.font.color.rgb = COLOR_NAVY_DARK
    pm2.space_before = Pt(6)
    
    pm3 = tf_m.add_paragraph()
    pm3.text = m_roll
    pm3.font.size = Pt(10)
    pm3.font.color.rgb = COLOR_TEXT_MUTED
    pm3.space_before = Pt(4)

    pm4 = tf_m.add_paragraph()
    pm4.text = m_role
    pm4.font.size = Pt(9.5)
    pm4.font.bold = True
    pm4.font.color.rgb = COLOR_NAVY_DARK
    pm4.space_before = Pt(4)

# Space 4: Faculty Guide & Academic Details Box (Bottom)
guide_card = add_card(slide1, Inches(0.8), Inches(6.1), Inches(11.733), Inches(0.9), bg_color=RGBColor(241, 245, 249), border_color=COLOR_BORDER)
tb_g = slide1.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.333), Inches(0.8))
tf_g = tb_g.text_frame
tf_g.word_wrap = True

pg1 = tf_g.paragraphs[0]
pg1.text = "PROJECT GUIDE:  Prof. / Dr. ___________________________, Designation: ___________________________"
pg1.font.size = Pt(12)
pg1.font.bold = True
pg1.font.color.rgb = COLOR_NAVY_DARK

pg2 = tf_g.add_paragraph()
pg2.text = "ACADEMIC YEAR:  2025 – 2026   |   BATCH:  [ Your Batch Here ]   |   SEMESTER:  VIII"
pg2.font.size = Pt(11)
pg2.font.color.rgb = COLOR_TEXT_MUTED
pg2.space_before = Pt(3)

slide1.notes_slide.notes_text_frame.text = (
    "SPEAKER: Member 1 (Lead)\n"
    "Good morning respected professors and evaluators. "
    "Welcome to our B.Tech capstone project presentation on the 'E-Learning Course Analytics System'. "
    "Our presentation is structured into 5 continuous sequential sections, with each team member presenting their core subsystem."
)


# ====================================================================
# PART 1: TEAM MEMBER 1 (Slides 2, 3, 4) - Enlarged Fonts (13-14pt)
# ====================================================================

# Slide 2: Member 1 - Introduction & Educational Motivation
slide2 = prs.slides.add_slide(blank_layout)
create_slide_header(slide2, "1.1 Introduction & E-Learning Expansion", "SPEAKER: MEMBER 1 (LEAD)", COLOR_M1)

add_card(slide2, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb = slide2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "The Growth of Modern E-Learning"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = COLOR_M1

pts = [
    ("Widespread Academic Adoption", "Universities worldwide have adopted asynchronous online learning modules, hybrid classrooms, and LMS portals."),
    ("Student Learning Trajectories", "Students learn at distinct paces, with varying study habits, submission velocity, and technical proficiencies."),
    ("Data Abundance", "Every video watched, quiz completed, and project submitted generates rich academic interaction metadata."),
    ("The Visibility Blindspot", "Instructors cannot observe whether students are actively progressing or quietly disengaging.")
]
for title, desc in pts:
    p_t = tf.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(8)
    p_d = tf.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb2 = slide2.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf2 = tb2.text_frame
tf2.word_wrap = True
p2 = tf2.paragraphs[0]
p2.text = "The Analytics Imperative"
p2.font.size = Pt(18)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

pts2 = [
    ("Moving Beyond Static Rosters", "Recording 'Enrolled' is not enough. We require continuous behavioral tracking across learning stages."),
    ("Quantifying Real Completion", "Measure true course completion percentage to identify which modules cause student bottlenecks."),
    ("Proactive Early Intervention", "Empower course administrators to rescue struggling students weeks before semester examinations."),
    ("Project Purpose", "Deliver a full-stack, data-driven web system using Python Flask, MySQL 8, and Chart.js.")
]
for title, desc in pts2:
    p_t = tf2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(8)
    p_d = tf2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 3: Member 1 - Problem Statement & Attrition Crisis
slide3 = prs.slides.add_slide(blank_layout)
create_slide_header(slide3, "1.2 Problem Statement: Silent Student Attrition", "SPEAKER: MEMBER 1 (LEAD)", COLOR_M1)

add_card(slide3, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
tb3 = slide3.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(5.0))
tf3 = tb3.text_frame
tf3.word_wrap = True

p3 = tf3.paragraphs[0]
p3.text = "Key Academic Problem Identified"
p3.font.size = Pt(19)
p3.font.bold = True
p3.font.color.rgb = COLOR_M5

bullets3 = [
    ("70%–85% E-Learning Dropout Rate", "Educational research shows that 70% to 85% of registered online learners fail to finish courses due to isolation and disengagement."),
    ("The 'Post-Mortem' Evaluation Dilemma", "Traditional learning systems only record failures at semester-end during final grading. By then, corrective academic interventions are impossible."),
    ("Uncalibrated Course Difficulty", "Without continuous analytics, department heads cannot determine whether low completion stems from overly demanding material or poor pacing."),
    ("Need for Continuous Inactivity Auditing", "Administrators urgently need an early-warning engine that flags students inactive for > 14 consecutive days."),
    ("Core Engineering Objective", "To engineer a unified full-stack platform with real-time completion rates, weekly activity trends, inactive student detection, and audit report generation backed by a robust MySQL 8 database.")
]

for title, desc in bullets3:
    p_t = tf3.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(14)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(8)
    p_d = tf3.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 4: Member 1 - Comparative Gap Analysis Table
slide4 = prs.slides.add_slide(blank_layout)
create_slide_header(slide4, "1.3 Gap Analysis: Conventional vs. Proposed", "SPEAKER: MEMBER 1 (LEAD)", COLOR_M1)

add_card(slide4, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
table_shape = slide4.shapes.add_table(6, 3, Inches(1.0), Inches(1.7), Inches(11.333), Inches(5.0))
table = table_shape.table
table.columns[0].width = Inches(2.7)
table.columns[1].width = Inches(4.3)
table.columns[2].width = Inches(4.333)

headers = ["Capability / Feature", "Conventional LMS / Spreadsheets", "Our Proposed Analytics System"]
for col_idx, h in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = COLOR_NAVY_DARK
    p = cell.text_frame.paragraphs[0]
    p.text = h
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(255, 255, 255)

gaps = [
    ("Data Architecture", "Static spreadsheets or heavy proprietary LMS", "Normalized MySQL 8.0 schema with ACID referential integrity"),
    ("Completion Metric Calculation", "Manual calculations or naive averaging of percentages", "Rigorous math: (Total Completed / Total Enrolled) * 100 with safe division"),
    ("Inactive Learner Detection", "Manual audit; dropouts discovered only after final grading", "Automated SQL HAVING rule flagging >14 days of silence in real-time"),
    ("Activity Visualizations", "Static offline tables without temporal progression", "Live interactive Chart.js charts & server-side Matplotlib figures"),
    ("Extensibility & Auditing", "Closed vendor ecosystems; hard to export clean data", "REST API architecture with dynamic search & one-click CSV report exports")
]
for row_idx, (feat, exist, prop) in enumerate(gaps, start=1):
    c0 = table.cell(row_idx, 0)
    c0.text = feat
    c0.text_frame.paragraphs[0].font.bold = True
    c0.text_frame.paragraphs[0].font.size = Pt(12)
    
    c1 = table.cell(row_idx, 1)
    c1.text = exist
    c1.text_frame.paragraphs[0].font.size = Pt(11.5)
    c1.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_MUTED
    
    c2 = table.cell(row_idx, 2)
    c2.text = prop
    c2.text_frame.paragraphs[0].font.size = Pt(11.5)
    c2.text_frame.paragraphs[0].font.color.rgb = COLOR_M1
    c2.text_frame.paragraphs[0].font.bold = True


# ====================================================================
# PART 2: TEAM MEMBER 2 (Slides 5, 6, 7) - Enlarged Fonts (13-14pt)
# ====================================================================

# Slide 5: Member 2 - 3-Tier Layered Architecture
slide5 = prs.slides.add_slide(blank_layout)
create_slide_header(slide5, "2.1 System Architecture: 3-Tier Multi-Layer Design", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_M2)

tiers = [
    ("1. PRESENTATION LAYER", COLOR_M1, [
        "Bootstrap 5.3 Responsive SaaS UI",
        "Dual Chart.js 4.4 Canvas Visuals",
        "Vanilla ES6+ Asynchronous Fetch API",
        "Real-Time Database Health Status",
        "Accessible Modal Dialogs & Toasts",
        "Zero-Page-Reload Dynamic Updates"
    ]),
    ("2. APPLICATION LAYER", COLOR_M2, [
        "Python 3.14 + Flask 3.1 Framework",
        "Multi-Threaded Server (threaded=True)",
        "REST API with Standard Status Codes",
        "Dual-Engine Fallback (Pandas + Native)",
        "Automated Headless Matplotlib (Agg)",
        "Streaming CSV Report Generator"
    ]),
    ("3. DATA LAYER", COLOR_M3, [
        "MySQL Server 8.0 Relational DBMS",
        "InnoDB Storage Engine (ACID-Compliant)",
        "Normalized 3NF Relational Structure",
        "Referential Integrity & Foreign Keys",
        "Unique Constraints on (Learner, Course)",
        "B-Tree Indexes on Dates & Status"
    ])
]

col_w = Inches(3.7)
start_x = Inches(0.8)

for i, (title, color, items) in enumerate(tiers):
    x = start_x + i * (col_w + Inches(0.3))
    add_card(slide5, x, Inches(1.5), col_w, Inches(5.4))
    
    hb = slide5.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.5), col_w, Inches(0.7))
    hb.fill.solid()
    hb.fill.fore_color.rgb = color
    hb.line.fill.background()
    p_h = hb.text_frame.paragraphs[0]
    p_h.text = title
    p_h.font.bold = True
    p_h.font.size = Pt(12)
    p_h.font.color.rgb = RGBColor(255, 255, 255)
    p_h.alignment = PP_ALIGN.CENTER
    
    tb = slide5.shapes.add_textbox(x + Inches(0.18), Inches(2.35), col_w - Inches(0.36), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, item in enumerate(items):
        p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p.text = f"✔ {item}"
        p.font.size = Pt(12.5)
        p.font.color.rgb = COLOR_NAVY_DARK
        p.space_after = Pt(10)


# Slide 6: Member 2 - Flask REST API Endpoints & Contracts
slide6 = prs.slides.add_slide(blank_layout)
create_slide_header(slide6, "2.2 Flask REST API Routing & HTTP Contracts", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_M2)

add_card(slide6, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb6_1 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf6_1 = tb6_1.text_frame
tf6_1.word_wrap = True
p = tf6_1.paragraphs[0]
p.text = "Key REST API Endpoints"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = COLOR_M2

api_routes = [
    ("GET /api/health", "System diagnostics & table verification"),
    ("GET /api/dashboard/summary", "Top summary card KPI figures"),
    ("GET /api/courses", "List courses with dynamic name/category search"),
    ("POST /api/courses", "Create course (validates required fields)"),
    ("DELETE /api/courses/<id>", "Safe course delete (fails if enrolled)"),
    ("POST /api/learners", "Register learner (unique roll number check)"),
    ("GET /api/enrollments", "Filter enrollments by course, status & roll"),
    ("POST /api/enrollments", "Register student in course (duplicate guarded)")
]
for route, desc in api_routes:
    p_r = tf6_1.add_paragraph()
    p_r.text = f"• {route}"
    p_r.font.bold = True
    p_r.font.size = Pt(12)
    p_r.font.color.rgb = COLOR_NAVY_DARK
    p_r.space_before = Pt(4)
    p_d = tf6_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb6_2 = slide6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf6_2 = tb6_2.text_frame
tf6_2.word_wrap = True
p2 = tf6_2.paragraphs[0]
p2.text = "HTTP Status Code Standardization"
p2.font.size = Pt(18)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

codes = [
    ("200 OK", "Successful data retrieval and analytical computation."),
    ("201 Created", "Resource successfully created in MySQL."),
    ("400 Bad Request", "Missing form parameters or rejection of unsafe deletion."),
    ("404 Not Found", "Specified resource ID does not exist in database."),
    ("409 Conflict", "Duplicate roll number or duplicate course enrollment."),
    ("503 Service Unavailable", "Clean database connection failure notice without exposing internal passwords.")
]
for c_code, c_desc in codes:
    p_c = tf6_2.add_paragraph()
    p_c.text = f"✔ {c_code}:"
    p_c.font.bold = True
    p_c.font.size = Pt(13)
    p_c.font.color.rgb = COLOR_M2
    p_c.space_before = Pt(6)
    p_cd = tf6_2.add_paragraph()
    p_cd.text = f"   {c_desc}"
    p_cd.font.size = Pt(11.5)
    p_cd.font.color.rgb = COLOR_TEXT_MUTED


# Slide 7: Member 2 - Concurrency & Performance Optimization
slide7 = prs.slides.add_slide(blank_layout)
create_slide_header(slide7, "2.3 Server Concurrency & Performance Engineering", "SPEAKER: MEMBER 2 (BACKEND ARCHITECT)", COLOR_M2)

add_card(slide7, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
tb7 = slide7.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(5.0))
tf7 = tb7.text_frame
tf7.word_wrap = True

p7 = tf7.paragraphs[0]
p7.text = "High-Performance Server Engineering"
p7.font.size = Pt(19)
p7.font.bold = True
p7.font.color.rgb = COLOR_M2

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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf7.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# ====================================================================
# PART 3: TEAM MEMBER 3 (Slides 8, 9, 10) - Enlarged Fonts (13-14pt)
# ====================================================================

# Slide 8: Member 3 - MySQL Database Architecture
slide8 = prs.slides.add_slide(blank_layout)
create_slide_header(slide8, "3.1 Database Architecture: MySQL 8.0 & Storage", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_M3)

add_card(slide8, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb8_1 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf8_1 = tb8_1.text_frame
tf8_1.word_wrap = True
p = tf8_1.paragraphs[0]
p.text = "Relational Storage Foundation"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = COLOR_M3

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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(8)
    p_d = tf8_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb8_2 = slide8.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf8_2 = tb8_2.text_frame
tf8_2.word_wrap = True
p2 = tf8_2.paragraphs[0]
p2.text = "Database Performance Indexing"
p2.font.size = Pt(18)
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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_M3
    p_t.space_before = Pt(8)
    p_d = tf8_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 9: Member 3 - Relational Schema & Tables
slide9 = prs.slides.add_slide(blank_layout)
create_slide_header(slide9, "3.2 Relational Schema: 4 Normalized Entities", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_M3)

tables_info = [
    ("courses", "Academic Course Catalog", [
        ("course_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("course_name", "VARCHAR(100) NOT NULL"),
        ("category", "VARCHAR(50) NOT NULL"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_M1),
    ("learners", "Student Profiles", [
        ("learner_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("roll_no", "VARCHAR(30) NOT NULL UNIQUE"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ], COLOR_M2),
    ("enrollments", "Registrations & Status", [
        ("enrollment_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("learner_id", "INT (FK -> learners)"),
        ("course_id", "INT (FK -> courses)"),
        ("status", "ENUM('Enrolled','In Progress','Completed')")
    ], COLOR_M3),
    ("activities", "Timestamped Interaction Logs", [
        ("activity_id", "INT AUTO_INCREMENT PRIMARY KEY"),
        ("enrollment_id", "INT (FK -> enrollments)"),
        ("activity_type", "VARCHAR(50) [Lesson/Quiz/Project]"),
        ("completed", "BOOLEAN DEFAULT FALSE")
    ], COLOR_M4)
]

w9 = Inches(5.6)
h9 = Inches(2.55)
pos9 = [
    (Inches(0.8), Inches(1.5)),
    (Inches(6.8), Inches(1.5)),
    (Inches(0.8), Inches(4.35)),
    (Inches(6.8), Inches(4.35))
]

for (tbl_name, desc, cols, col_tag), (pos_x, pos_y) in zip(tables_info, pos9):
    add_card(slide9, pos_x, pos_y, w9, h9)
    tag_box = slide9.shapes.add_shape(MSO_SHAPE.RECTANGLE, pos_x, pos_y, w9, Inches(0.48))
    tag_box.fill.solid()
    tag_box.fill.fore_color.rgb = col_tag
    tag_box.line.fill.background()
    p = tag_box.text_frame.paragraphs[0]
    p.text = f"{tbl_name.upper()} — {desc}"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(255, 255, 255)
    
    tb = slide9.shapes.add_textbox(pos_x + Inches(0.2), pos_y + Inches(0.55), w9 - Inches(0.4), h9 - Inches(0.6))
    tf = tb.text_frame
    tf.word_wrap = True
    for idx, (col, ctype) in enumerate(cols):
        p_c = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p_c.text = f"• {col}: {ctype}"
        p_c.font.size = Pt(11)
        p_c.font.color.rgb = COLOR_NAVY_DARK
        p_c.space_after = Pt(2)


# Slide 10: Member 3 - Integrity Constraints & Safe Deletion
slide10 = prs.slides.add_slide(blank_layout)
create_slide_header(slide10, "3.3 Integrity Constraints & Deletion Policies", "SPEAKER: MEMBER 3 (DATABASE ENGINEER)", COLOR_M3)

add_card(slide10, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
tb10 = slide10.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(5.0))
tf10 = tb10.text_frame
tf10.word_wrap = True

p10 = tf10.paragraphs[0]
p10.text = "Relational Integrity Enforcement"
p10.font.size = Pt(19)
p10.font.bold = True
p10.font.color.rgb = COLOR_M3

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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf10.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# ====================================================================
# PART 4: TEAM MEMBER 4 (Slides 11, 12, 13) - Enlarged Fonts (13-14pt)
# ====================================================================

# Slide 11: Member 4 - Course Completion Formulations
slide11 = prs.slides.add_slide(blank_layout)
create_slide_header(slide11, "4.1 Mathematical Models: Completion Analytics", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_M4)

add_card(slide11, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb11_1 = slide11.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf11_1 = tb11_1.text_frame
tf11_1.word_wrap = True
p = tf11_1.paragraphs[0]
p.text = "1. Course Completion Rate Formula"
p.font.size = Pt(17)
p.font.bold = True
p.font.color.rgb = COLOR_M4

f_pts = [
    ("Mathematical Definition", "Course Completion Rate = (Completed Enrollments / Total Enrollments) * 100"),
    ("Safe Division by Zero Guard", "If Total Enrollments = 0, evaluated via np.where() or conditional logic to return 0.0% instead of crashing with ZeroDivisionError."),
    ("Four Performance Tiers", "• Excellent (>= 75%): Green Badge\n• Good (>= 50%): Blue Badge\n• Average (>= 25%): Amber Badge\n• Needs Attention (< 25%): Red Badge")
]
for title, desc in f_pts:
    p_t = tf11_1.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf11_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb11_2 = slide11.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf11_2 = tb11_2.text_frame
tf11_2.word_wrap = True
p2 = tf11_2.paragraphs[0]
p2.text = "2. Overall Platform Completion"
p2.font.size = Pt(17)
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
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_M1
    p_t.space_before = Pt(6)
    p_d = tf11_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 12: Member 4 - Inactive Enrollment Detection Algorithm
slide12 = prs.slides.add_slide(blank_layout)
create_slide_header(slide12, "4.2 Algorithm: Inactive Detection (14-Day Rule)", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_M4)

add_card(slide12, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
tb12 = slide12.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(5.0))
tf12 = tb12.text_frame
tf12.word_wrap = True

p12 = tf12.paragraphs[0]
p12.text = "The 14-Day Inactivity Detection Algorithm"
p12.font.size = Pt(19)
p12.font.bold = True
p12.font.color.rgb = COLOR_M5

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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf12.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 13: Member 4 - Weekly Activity Aggregation & Dual-Engine
slide13 = prs.slides.add_slide(blank_layout)
create_slide_header(slide13, "4.3 Weekly Aggregation & Dual-Engine Fallback", "SPEAKER: MEMBER 4 (DATA ANALYTICS)", COLOR_M4)

add_card(slide13, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb13_1 = slide13.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf13_1 = tb13_1.text_frame
tf13_1.word_wrap = True
p = tf13_1.paragraphs[0]
p.text = "Weekly Activity Resampling"
p.font.size = Pt(17)
p.font.bold = True
p.font.color.rgb = COLOR_M4

pts_wk = [
    ("Calendar Week Resampling", "Groups activities by weekly periods starting on Monday using pd.to_period('W-SUN') and ISO week numbering (e.g. 2026-W41)."),
    ("Chronological Progression", "Aggregates total submissions, completed activities, and pending activities in chronological sequence."),
    ("Date Range Filtering", "Supports optional start_date and end_date query parameters for term-based or monthly activity audits.")
]
for title, desc in pts_wk:
    p_t = tf13_1.add_paragraph()
    p_t.text = f"• {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf13_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide13, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb13_2 = slide13.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf13_2 = tb13_2.text_frame
tf13_2.word_wrap = True
p2 = tf13_2.paragraphs[0]
p2.text = "Resilient Dual-Engine Fallback"
p2.font.size = Pt(17)
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
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_M1
    p_t.space_before = Pt(6)
    p_d = tf13_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# ====================================================================
# PART 5: TEAM MEMBER 5 (Slides 14, 15, 16) - Enlarged Fonts (13-14pt)
# ====================================================================

# Slide 14: Member 5 - Dashboard & Visual Analytics
slide14 = prs.slides.add_slide(blank_layout)
create_slide_header(slide14, "5.1 User Interface: Dashboard & Visual Analytics", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_M5)

cards_ui = [
    ("Summary KPI Cards", "6 Live Real-Time Metrics", [
        "Total Courses, Learners",
        "Total & Completed Enrollments",
        "Overall Platform Completion %",
        "Inactive Enrollments (> 14d)"
    ], COLOR_M1),
    ("Course Completion Chart", "Chart.js Bar Visualization", [
        "X-axis: Course Titles",
        "Dual Y-axes: % & Student counts",
        "Color-coded by performance",
        "Dynamic hover tooltips"
    ], COLOR_M3),
    ("Weekly Trends Chart", "Chart.js Line Visualization", [
        "Calendar week timestamps",
        "Tracks total learning volume",
        "Shows completed submissions",
        "Chronological trend curves"
    ], COLOR_M2),
    ("Benchmark & Detection", "Interactive Data Grids", [
        "Configurable threshold filter",
        "Direct 'Log Activity' action link",
        "Sub-100ms UI render speed",
        "Zero page reload updates"
    ], COLOR_M4)
]

w14 = Inches(2.7)
start_x14 = Inches(0.8)

for i, (title, sub, bullets, col_t) in enumerate(cards_ui):
    x = start_x14 + i * (w14 + Inches(0.3))
    add_card(slide14, x, Inches(1.5), w14, Inches(5.4))
    
    top_t = slide14.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.5), w14, Inches(0.72))
    top_t.fill.solid()
    top_t.fill.fore_color.rgb = col_t
    top_t.line.fill.background()
    p = top_t.text_frame.paragraphs[0]
    p.text = title
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER
    
    tb = slide14.shapes.add_textbox(x + Inches(0.15), Inches(2.35), w14 - Inches(0.3), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p_s = tf.paragraphs[0]
    p_s.text = sub
    p_s.font.size = Pt(11)
    p_s.font.bold = True
    p_s.font.color.rgb = COLOR_TEXT_MUTED
    p_s.space_after = Pt(8)
    
    for b in bullets:
        p_b = tf.add_paragraph()
        p_b.text = f"✔ {b}"
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = COLOR_NAVY_DARK
        p_b.space_after = Pt(8)


# Slide 15: Member 5 - Security Hardening & CSV Exports
slide15 = prs.slides.add_slide(blank_layout)
create_slide_header(slide15, "5.2 Security Hardening & Academic CSV Exports", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_M5)

add_card(slide15, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb15_1 = slide15.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf15_1 = tb15_1.text_frame
tf15_1.word_wrap = True
p = tf15_1.paragraphs[0]
p.text = "Security Architecture"
p.font.size = Pt(17)
p.font.bold = True
p.font.color.rgb = COLOR_M5

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
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf15_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide15, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb15_2 = slide15.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf15_2 = tb15_2.text_frame
tf15_2.word_wrap = True
p2 = tf15_2.paragraphs[0]
p2.text = "Academic Report Generation"
p2.font.size = Pt(17)
p2.font.bold = True
p2.font.color.rgb = COLOR_NAVY_DARK

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
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_M1
    p_t.space_before = Pt(6)
    p_d = tf15_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 16: Member 5 - Verification Testing & Benchmarks
slide16 = prs.slides.add_slide(blank_layout)
create_slide_header(slide16, "5.3 Verification Testing & Latency Benchmarks", "SPEAKER: MEMBER 5 (UI/UX & QA)", COLOR_M5)

add_card(slide16, Inches(0.8), Inches(1.5), Inches(11.733), Inches(5.4))
tb16 = slide16.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(11.133), Inches(5.0))
tf16 = tb16.text_frame
tf16.word_wrap = True

p16 = tf16.paragraphs[0]
p16.text = "Comprehensive QA & Verified Benchmarks"
p16.font.size = Pt(19)
p16.font.bold = True
p16.font.color.rgb = COLOR_M3

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
    p_t.font.size = Pt(13.5)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf16.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# ====================================================================
# CONCLUSION & DEFENSE: ALL MEMBERS (Slides 17, 18) - Enlarged Fonts
# ====================================================================

# Slide 17: All Members - Future Scope
slide17 = prs.slides.add_slide(blank_layout)
create_slide_header(slide17, "6.1 Future Enhancements & Research Horizons", "SPEAKER: ALL TEAM MEMBERS", COLOR_M1)

add_card(slide17, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
tb17_1 = slide17.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf17_1 = tb17_1.text_frame
tf17_1.word_wrap = True
p = tf17_1.paragraphs[0]
p.text = "Advanced Academic Features"
p.font.size = Pt(17)
p.font.bold = True
p.font.color.rgb = COLOR_M1

f_items1 = [
    ("Predictive ML Dropout Forecasting", "Train a Random Forest or Logistic Regression classifier on student submission velocity to predict dropout risk 3 weeks in advance."),
    ("Automated Nudge Notifications", "Integrate automated email / SMS alerts to gently remind students when they cross the 14-day inactivity mark."),
    ("Digital Certificate Generation", "Automatic generation and verification of PDF certificates upon reaching 100% activity completion.")
]
for title, desc in f_items1:
    p_t = tf17_1.add_paragraph()
    p_t.text = f"🚀 {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_NAVY_DARK
    p_t.space_before = Pt(6)
    p_d = tf17_1.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED

add_card(slide17, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=COLOR_CARD_ALT)
tb17_2 = slide17.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf17_2 = tb17_2.text_frame
tf17_2.word_wrap = True
p2 = tf17_2.paragraphs[0]
p2.text = "Platform Expansion"
p2.font.size = Pt(17)
p2.font.bold = True
p2.font.color.rgb = COLOR_M3

f_items2 = [
    ("Role-Based Access Control (RBAC)", "Multi-tenant authentication with dedicated portals for Students (self-paced tracking) and Instructors (grading)."),
    ("Cross-Platform Mobile App", "Complement the web dashboard with a Flutter or React Native mobile application for student push notifications."),
    ("LTI / Canvas / Moodle Integration", "Learning Tools Interoperability (LTI) plugin for plug-and-play adoption across university systems.")
]
for title, desc in f_items2:
    p_t = tf17_2.add_paragraph()
    p_t.text = f"✔ {title}:"
    p_t.font.bold = True
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = COLOR_M3
    p_t.space_before = Pt(6)
    p_d = tf17_2.add_paragraph()
    p_d.text = f"   {desc}"
    p_d.font.size = Pt(11.5)
    p_d.font.color.rgb = COLOR_TEXT_MUTED


# Slide 18: All Members - Conclusion & Q&A
slide18 = prs.slides.add_slide(blank_layout)
apply_page_background(slide18, COLOR_NAVY_DARK)

tb_qa = slide18.shapes.add_textbox(Inches(1.5), Inches(1.6), Inches(10.333), Inches(4.5))
tf_qa = tb_qa.text_frame
tf_qa.word_wrap = True

p_q1 = tf_qa.paragraphs[0]
p_q1.text = "Thank You!"
p_q1.font.size = Pt(46)
p_q1.font.bold = True
p_q1.font.color.rgb = RGBColor(255, 255, 255)
p_q1.alignment = PP_ALIGN.CENTER

p_q2 = tf_qa.add_paragraph()
p_q2.text = "E-Learning Course Analytics System"
p_q2.font.size = Pt(24)
p_q2.font.bold = True
p_q2.font.color.rgb = COLOR_ACCENT_BLUE
p_q2.alignment = PP_ALIGN.CENTER
p_q2.space_before = Pt(14)

p_q3 = tf_qa.add_paragraph()
p_q3.text = "Presented by 5-Member Engineering Team:\nMember 1 (Lead)  •  Member 2 (Backend)  •  Member 3 (Database)  •  Member 4 (Analytics)  •  Member 5 (QA & UI)"
p_q3.font.size = Pt(14)
p_q3.font.color.rgb = RGBColor(203, 213, 225)
p_q3.alignment = PP_ALIGN.CENTER
p_q3.space_before = Pt(16)

p_q4 = tf_qa.add_paragraph()
p_q4.text = "Questions, Faculty Feedback & Technical Discussion Are Welcome"
p_q4.font.size = Pt(16)
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
print(f"Enhanced Continuous PPT saved successfully at: {output_path}")
