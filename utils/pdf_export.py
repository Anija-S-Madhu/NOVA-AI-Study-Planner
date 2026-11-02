from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _plain_pdf(timetable, subjects):
    """Dependency-free, standards-compliant fallback PDF renderer."""
    lines = ["NOVA Study Timetable", f"Subjects tracked: {len(subjects)}", ""]
    lines.extend(f"{x.get('subject', '')} | {x.get('date', '')} | {x.get('hours', 0)} hrs | {x.get('priority', '')}" for x in timetable)
    def escape(value): return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = "BT\n/F1 12 Tf\n72 760 Td\n16 TL\n" + "".join(f"({escape(line)}) Tj\nT*\n" for line in lines) + "ET\n"
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>", "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>", f"<< /Length {len(content.encode('latin-1', 'replace'))} >>\nstream\n{content}endstream", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    output = bytearray(b"%PDF-1.4\n"); offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output)); output.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))
    xref = len(output); output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return BytesIO(output)


def export_timetable_pdf(timetable, subjects):
    """Create a readable timetable PDF; uses ReportLab when installed."""
    if not REPORTLAB_AVAILABLE:
        return _plain_pdf(timetable, subjects)
    buffer = BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet(); story = [Paragraph("NOVA Study Timetable", styles["Title"]), Spacer(1, 10), Paragraph(f"Subjects tracked: {len(subjects)}", styles["Normal"]), Spacer(1, 14)]
    rows = [["Subject", "Date", "Hours", "Priority"]] + [[str(item.get("subject", "")), str(item.get("date", "")), str(item.get("hours", 0)), str(item.get("priority", ""))] for item in timetable]
    table = Table(rows, colWidths=[190, 115, 70, 110], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087e8b")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#cbdde1")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eaf7f6")]), ("PADDING", (0, 0), (-1, -1), 8)]))
    story.append(table); doc.build(story); buffer.seek(0)
    return buffer
