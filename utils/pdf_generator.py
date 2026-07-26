from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor

import os
import requests
import glob
from io import BytesIO

from utils.chart_generator_pdf import generate_chart

styles = getSampleStyleSheet()

# ==================================================
# STYLES
# ==================================================

title_style = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    alignment=1,
    fontSize=30,
    textColor=HexColor("#2E86C1"),
    spaceAfter=25
)

heading_style = ParagraphStyle(
    "Heading",
    parent=styles["Heading1"],
    fontSize=18,
    textColor=HexColor("#1F618D"),
    spaceAfter=12
)

text_style = ParagraphStyle(
    "BodyText",
    parent=styles["Normal"],
    fontSize=11,
    leading=20,
    alignment=4,  # justified
    spaceAfter=10
)

# ==================================================
# PAGE NUMBER
# ==================================================


def add_page_number(canvas, doc):

    page_num = canvas.getPageNumber()

    canvas.setFont("Helvetica", 10)

    canvas.drawRightString(
        200 * mm,
        15,
        str(page_num)
    )


# ==================================================
# PDF GENERATOR
# ==================================================

def generate_pdf(slides, topic):

    os.makedirs("outputs", exist_ok=True)

    file_path = "outputs/report.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []

    # ==================================================
    # TITLE PAGE
    # ==================================================

    elements.append(Spacer(1, 220))

    elements.append(
        Paragraph(
            topic.upper(),
            title_style
        )
    )

    elements.append(
        Paragraph(
            "AI Generated Academic Report",
            styles["Heading2"]
        )
    )

    elements.append(PageBreak())

    # ==================================================
    # TABLE OF CONTENTS
    # ==================================================

    elements.append(
        Paragraph(
            "Table of Contents",
            styles["Heading1"]
        )
    )

    elements.append(Spacer(1, 20))

    for i, slide in enumerate(slides):

        elements.append(
            Paragraph(
                f"{i+1}. {slide.get('title', '')}",
                styles["Normal"]
            )
        )

        elements.append(Spacer(1, 5))

    elements.append(PageBreak())

    # ==================================================
    # CONTENT PAGES
    # ==================================================

    for i, slide in enumerate(slides):

        section = []

        # ----------------------------------------------
        # TITLE
        # ----------------------------------------------

        section.append(
            Paragraph(
                f"{i+1}. {slide.get('title', '')}",
                heading_style
            )
        )

        section.append(Spacer(1, 10))

        # ----------------------------------------------
        # CONTENT
        # ----------------------------------------------

        content = slide.get("content", "")

        # Prevent huge paragraphs
        if len(content) > 1800:
            content = content[:1800] + "..."

        paragraphs = content.split("\n\n")

        for para in paragraphs:

            para = para.strip()

            if para:

                section.append(
                    Paragraph(
                        para,
                        text_style
                    )
                )

                section.append(
                    Spacer(1, 10)
                )

        # ==================================================
        # GRAPH HAS PRIORITY
        # ==================================================

        chart_path = generate_chart(
            slide.get("chart_data"),
            i
        )

        if chart_path:

            try:

                chart_img = Image(
                    chart_path,
                    width=6.2 * inch,
                    height=4.0 * inch
                )

                section.append(chart_img)

            except Exception as e:
                print("Chart Error:", e)

        else:

            img_url = slide.get("image_url")

            if img_url:

                try:

                    img_data = requests.get(
                        img_url,
                        timeout=10
                    ).content

                    img_path = f"outputs/img_{i}.jpg"

                    with open(img_path, "wb") as f:
                        f.write(img_data)

                    report_img = Image(
                        img_path,
                        width=6.0 * inch,
                        height=3.8 * inch
                    )

                    section.append(report_img)

                except Exception as e:
                    print("Image Error:", e)

        section.append(Spacer(1, 15))

        # ----------------------------------------------
        # KEEP SECTION TOGETHER
        # ----------------------------------------------

        elements.append(
            KeepTogether(section)
        )

        # ----------------------------------------------
        # NEW PAGE
        # ----------------------------------------------

        if i < len(slides) - 1:
            elements.append(PageBreak())

    # ==================================================
    # BUILD PDF
    # ==================================================

    doc.build(
        elements,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    for file in glob.glob("outputs/img_*.jpg"):
        os.remove(file)

    for file in glob.glob("outputs/chart_*.png"):
        os.remove(file)

    return file_path
