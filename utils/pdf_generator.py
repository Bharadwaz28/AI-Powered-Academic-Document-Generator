from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor

import os
import glob
import random
import unicodedata
from html import escape
from io import BytesIO

import requests

from utils.chart_generator_pdf import generate_chart


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    alignment=1,
    fontSize=30,
    textColor=HexColor("#2E86C1"),
    spaceAfter=25,
)

heading_style = ParagraphStyle(
    "Heading",
    parent=styles["Heading1"],
    fontSize=18,
    textColor=HexColor("#1F618D"),
    spaceAfter=12,
)

text_style = ParagraphStyle(
    "BodyText",
    parent=styles["Normal"],
    fontSize=11,
    leading=20,
    alignment=4,
    spaceAfter=10,
)


def clean_pdf_text(text):
    """Normalize punctuation unsupported by ReportLab's standard fonts."""
    if not isinstance(text, str):
        text = str(text)

    replacements = {
        "\u2010": "-",  # Hyphen
        "\u2011": "-",  # Non-breaking hyphen
        "\u2012": "-",  # Figure dash
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2212": "-",  # Minus sign
        "\u00a0": " ",  # Non-breaking space
        "\u200b": "",   # Zero-width space
        "\ufeff": "",   # BOM
        "\u25a0": "-",  # Black square sometimes used as a replacement glyph
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKC", text)

    # Keep characters supported by the standard Helvetica encoding.
    text = text.encode("cp1252", errors="replace").decode("cp1252")

    # Escape user/AI text so characters like < and & cannot break Paragraph.
    return escape(text)


def add_page_number(canvas, doc):
    canvas.getPageNumber()
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(200 * mm, 15, str(canvas.getPageNumber()))


def generate_pdf(slides, topic):
    os.makedirs("outputs", exist_ok=True)

    file_path = "outputs/report.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elements = []
    image_streams = []

    try:
        # ---------------- TITLE PAGE ----------------
        elements.append(Spacer(1, 220))
        elements.append(Paragraph(clean_pdf_text(topic.upper()), title_style))
        elements.append(
            Paragraph("AI Generated Academic Report", styles["Heading2"])
        )
        elements.append(PageBreak())

        # ---------------- TABLE OF CONTENTS ----------------
        elements.append(Paragraph("Table of Contents", styles["Heading1"]))
        elements.append(Spacer(1, 20))

        for i, slide in enumerate(slides):
            elements.append(
                Paragraph(
                    f"{i + 1}. {clean_pdf_text(slide.get('title', ''))}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 5))

        elements.append(PageBreak())

        # ---------------- REPORT SECTIONS ----------------
        for i, slide in enumerate(slides):
            section = []

            section.append(
                Paragraph(
                    f"{i + 1}. {clean_pdf_text(slide.get('title', ''))}",
                    heading_style,
                )
            )
            section.append(Spacer(1, 10))

            content = slide.get("content", "")

            if len(content) > 1800:
                content = content[:1800] + "..."

            for para in content.split("\n\n"):
                para = para.strip()

                if para:
                    section.append(
                        Paragraph(clean_pdf_text(para), text_style)
                    )
                    section.append(Spacer(1, 10))

            chart_data = slide.get("chart_data")
            image_url = slide.get("image_url")

            # Use the visual already chosen in app.py (same as the preview).
            saved_visual = slide.get("visual_type")

            if saved_visual in ("chart", "image"):
                preferred_visual = saved_visual
            elif saved_visual == "none":
                preferred_visual = None
            else:
                # Only used if visual_type is missing
                preferred_visual = random.choice(["chart", "image"])

            visual_added = False

            def add_chart():
                if not chart_data:
                    return False

                chart_path = generate_chart(chart_data, i)

                if not chart_path or not os.path.isfile(chart_path):
                    return False

                with open(chart_path, "rb") as chart_file:
                    chart_bytes = chart_file.read()

                if not chart_bytes:
                    return False

                stream = BytesIO(chart_bytes)
                image_streams.append(stream)

                section.append(
                    Image(
                        stream,
                        width=6.2 * inch,
                        height=4.0 * inch,
                    )
                )
                return True

            def add_image():
                if not image_url:
                    return False

                response = requests.get(image_url, timeout=15)
                response.raise_for_status()

                if not response.content:
                    return False

                stream = BytesIO(response.content)
                image_streams.append(stream)

                section.append(
                    Image(
                        stream,
                        width=6.0 * inch,
                        height=3.8 * inch,
                    )
                )
                return True

            # Try the selected visual first.
            if preferred_visual:
                try:
                    if preferred_visual == "chart":
                        visual_added = add_chart()
                    else:
                        visual_added = add_image()

                except Exception as exc:
                    print(
                        f"{preferred_visual.title()} error in section "
                        f"{i + 1}: {exc}"
                    )

                # If the chosen visual fails, try the other type.
                if not visual_added:
                    try:
                        if preferred_visual == "chart":
                            visual_added = add_image()
                        else:
                            visual_added = add_chart()

                    except Exception as exc:
                        print(
                            f"Fallback visual error in section "
                            f"{i + 1}: {exc}"
                        )

                if not visual_added:
                    print(
                        f"WARNING: No visual available for section {i + 1}."
                    )

            section.append(Spacer(1, 15))
            elements.append(KeepTogether(section))

            if i < len(slides) - 1:
                elements.append(PageBreak())

        # Build before closing streams or deleting chart files.
        doc.build(
            elements,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number,
        )

        print(f"PDF generated successfully: {file_path}")
        return file_path

    finally:
        for stream in image_streams:
            stream.close()

        for pattern in ("outputs/img_*.jpg", "outputs/chart_*.png"):
            for temporary_file in glob.glob(pattern):
                try:
                    os.remove(temporary_file)
                except OSError as exc:
                    print(f"Cleanup warning: {temporary_file}: {exc}")
