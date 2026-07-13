"""Generate INSTALLER_GUIDE.pdf from INSTALLER_GUIDE.md

Usage:
    python tools/generate_guide_pdf.py

Output: INSTALLER_GUIDE.pdf
"""
import os
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT, "INSTALLER_GUIDE.pdf")
GUIDE_MD = os.path.join(PROJECT, "INSTALLER_GUIDE.md")

# Colors matching the app theme
GOLD = colors.HexColor("#f0c060")
TEAL = colors.HexColor("#00d4aa")
DARK_BG = colors.HexColor("#0a0a0f")
TEXT_COLOR = colors.HexColor("#333333")


def parse_markdown(md_text):
    """Simple markdown to reportlab flowables converter."""
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )

    heading1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor("#2a1040"),
    )

    heading2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#4a1a30"),
    )

    heading3_style = ParagraphStyle(
        "CustomH3",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#6a2a40"),
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceBefore=4,
        spaceAfter=4,
    )

    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontSize=8,
        leading=10,
        fontName="Courier",
        backColor=colors.HexColor("#f5f5f5"),
        borderWidth=1,
        borderColor=colors.HexColor("#dddddd"),
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6,
    )

    story = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                code_text = "\n".join(code_lines)
                story.append(Paragraph(code_text.replace("\n", "<br/>"), code_style))
                code_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Tables
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if all(set(c) <= set("- :") for c in cells):
                # Separator row, skip
                i += 1
                continue
            table_rows.append(cells)
            # Check if next line is also a table row
            if i + 1 < len(lines) and "|" in lines[i + 1] and lines[i + 1].strip().startswith("|"):
                i += 1
                continue
            else:
                # End of table, render it
                if table_rows:
                    tbl = Table(table_rows, hAlign="LEFT")
                    tbl.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2a1040")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                            [colors.HexColor("#f9f9f9"), colors.white]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(tbl)
                    story.append(Spacer(1, 6))
                table_rows = []
                i += 1
                continue

        # Headings
        if line.startswith("# ") and not line.startswith("## "):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            i += 1
            continue

        if line.startswith("## "):
            text = line[3:].strip()
            story.append(Paragraph(text, heading1_style))
            i += 1
            continue

        if line.startswith("### "):
            text = line[4:].strip()
            story.append(Paragraph(text, heading2_style))
            i += 1
            continue

        if line.startswith("#### "):
            text = line[5:].strip()
            story.append(Paragraph(text, heading3_style))
            i += 1
            continue

        # Horizontal rule
        if line.strip() in ("---", "***", "___"):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # Empty lines
        if not line.strip():
            story.append(Spacer(1, 6))
            i += 1
            continue

        # Blockquotes
        if line.startswith("> "):
            text = line[2:].strip()
            # Simple italic for blockquotes
            text = f"<i>{text}</i>"
            story.append(Paragraph(text, body_style))
            i += 1
            continue

        # List items
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            text = f"• {text}"
            story.append(Paragraph(text, body_style))
            i += 1
            continue

        # Numbered lists
        match = re.match(r"^(\d+)\.\s+(.+)", line)
        if match:
            num, text = match.groups()
            text = f"<b>{num}.</b> {text}"
            story.append(Paragraph(text, body_style))
            i += 1
            continue

        # Regular paragraph
        text = line.strip()
        # Convert markdown bold/italic
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        text = re.sub(r"`(.+?)`", r"<font face='Courier' size='9'>\1</font>", text)
        story.append(Paragraph(text, body_style))
        i += 1

    return story


def build_pdf():
    """Build the PDF from INSTALLER_GUIDE.md."""
    print(f"Reading {GUIDE_MD}...")
    with open(GUIDE_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    print("Generating PDF...")
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=1.0 * inch,
        title="GTA San Andreas Stories 1987 — Installer Guide & Credits",
        author="GTA SAS 1987 Team",
    )

    story = parse_markdown(md_text)
    doc.build(story)

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"Done! Output: {OUTPUT} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    build_pdf()
