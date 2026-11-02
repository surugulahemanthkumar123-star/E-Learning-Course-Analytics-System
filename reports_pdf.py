"""
====================================================================
E-Learning Course Analytics System - PDF Report Generator
File: reports_pdf.py
Generates professional, publication-ready PDF analytical summaries
using ReportLab with custom NumberedCanvas headers/footers, KPI tiles,
data tables with alternating row shading, and embedded chart figures.
====================================================================
"""

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count and draw
    consistent professional headers and 'Page X of Y' footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_w, page_h = self._pagesize

        # Running Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1e293b"))
        self.drawString(36, page_h - 28, "E-LEARNING COURSE ANALYTICS SYSTEM")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(page_w - 36, page_h - 28, "ACADEMIC AUDIT & PERFORMANCE TELEMETRY")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(36, page_h - 34, page_w - 36, page_h - 34)

        # Running Footer
        self.line(36, 36, page_w - 36, 36)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 24, "CONFIDENTIAL & PROPRIETARY — FOR INSTITUTIONAL USE ONLY")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_w - 36, 24, page_str)

        self.restoreState()


def build_pdf_report(report_title, field_labels, rows, kpi_items=None, filter_text=None, chart_filename=None):
    """
    Builds a styled PDF document in memory and returns bytes.
    - report_title: str
    - field_labels: list of (key, label, col_width_or_ratio)
    - rows: list of dicts
    - kpi_items: list of (label, value)
    - filter_text: str describing active filters applied
    - chart_filename: optional filename inside static/charts/ to embed
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )

    kpi_val_style = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        alignment=1,
        textColor=colors.HexColor("#1e40af")
    )

    kpi_lbl_style = ParagraphStyle(
        "KPILbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.HexColor("#64748b")
    )

    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b")
    )

    cell_bold_style = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a")
    )

    cell_center_style = ParagraphStyle(
        "TableCellCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Title & Metadata Header Block
    now_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    header_data = [
        [
            Paragraph(report_title, title_style),
            Paragraph(f"<b>Generated:</b> {now_str}<br/><b>Filters:</b> {filter_text or 'All Catalog Records'}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[480, 240])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # KPI Summary Cards Block (if provided)
    if kpi_items:
        kpi_cols = len(kpi_items)
        col_w = 720 / kpi_cols
        row_vals = [Paragraph(str(item[1]), kpi_val_style) for item in kpi_items]
        row_lbls = [Paragraph(str(item[0]).upper(), kpi_lbl_style) for item in kpi_items]
        kpi_outer = Table([row_vals, row_lbls], colWidths=[col_w] * kpi_cols)
        kpi_outer.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(kpi_outer)
        story.append(Spacer(1, 12))

    # Optional Embedded Chart Image (if exists and genuinely generated)
    if chart_filename:
        chart_path = os.path.join(os.path.dirname(__file__), "static", "charts", chart_filename)
        if os.path.exists(chart_path) and os.path.getsize(chart_path) > 5000:
            try:
                chart_img = Image(chart_path, width=5.5 * inch, height=2.2 * inch)
                chart_wrapper = Table([[chart_img]], colWidths=[720])
                chart_wrapper.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(chart_wrapper)
            except Exception as _img_err:
                pass

    # Main Data Table
    norm_labels = []
    for item in field_labels:
        if len(item) == 2:
            norm_labels.append((item[0], item[1], 100))
        elif len(item) >= 3:
            norm_labels.append((item[0], item[1], item[2]))
    field_labels = norm_labels

    th_row = [Paragraph(label, th_style) for _, label, _ in field_labels]
    table_data = [th_row]

    for idx, row in enumerate(rows):
        row_cells = []
        for col_idx, (key, _, _) in enumerate(field_labels):
            val = row.get(key)
            if val is None:
                display_str = "—"
            elif isinstance(val, float):
                display_str = f"{val:.1f}" if "%" not in key else f"{val:.1f}%"
            else:
                display_str = str(val)

            # Center numbers/short codes, left align text
            if col_idx in (0, 3, 4, 5, 6, 7):
                p = Paragraph(display_str, cell_center_style)
            elif col_idx == 1:
                p = Paragraph(display_str, cell_bold_style)
            else:
                p = Paragraph(display_str, cell_style)
            row_cells.append(p)
        table_data.append(row_cells)

    total_specified_w = sum(float(w or 100) for _, _, w in field_labels) if field_labels else 720.0
    scale = (720.0 / total_specified_w) if total_specified_w > 0 else 1.0
    col_widths = [float(w or 100) * scale for _, _, w in field_labels] if field_labels else None

    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table_style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]

    for i in range(1, len(table_data)):
        bg = colors.HexColor("#ffffff") if i % 2 == 1 else colors.HexColor("#f8fafc")
        table_style_commands.append(("BACKGROUND", (0, i), (-1, i), bg))
        table_style_commands.append(("TOPPADDING", (0, i), (-1, i), 4))
        table_style_commands.append(("BOTTOMPADDING", (0, i), (-1, i), 4))

    main_table.setStyle(TableStyle(table_style_commands))
    story.append(main_table)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
