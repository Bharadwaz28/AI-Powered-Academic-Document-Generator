
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
import requests

from io import BytesIO
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


def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(200 * mm, 15, str(page_num))


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
        elements.append(Paragraph(topic.upper(), title_style))
        elements.append(
            Paragraph(
                "AI Generated Academic Report",
                styles["Heading2"],
            )
        )
        elements.append(PageBreak())

        # ---------------- TABLE OF CONTENTS ----------------
        elements.append(
            Paragraph("Table of Contents", styles["Heading1"])
        )
        elements.append(Spacer(1, 20))

        for i, slide in enumerate(slides):
            elements.append(
                Paragraph(
                    f"{i + 1}. {slide.get('title', '')}",
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
                    f"{i + 1}. {slide.get('title', '')}",
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
                    section.append(Paragraph(para, text_style))
                    section.append(Spacer(1, 10))

            chart_data = slide.get("chart_data")
            image_url = slide.get("image_url")

            # =================================================
            # VISUAL SELECTION
            # Even section index: chart
            # Odd section index: image
            # Each section attempts to add only ONE visual.
            # =================================================
            prefer_chart = (i % 2 == 0)

            visual_added = False

            # ---------------- CHART SECTION ----------------
            if prefer_chart and chart_data:
                try:
                    chart_path = generate_chart(chart_data, i)

                    if chart_path and os.path.isfile(chart_path):
                        with open(chart_path, "rb") as chart_file:
                            chart_bytes = chart_file.read()

                        if chart_bytes:
                            chart_stream = BytesIO(chart_bytes)
                            image_streams.append(chart_stream)

                            section.append(
                                Image(
                                    chart_stream,
                                    width=6.2 * inch,
                                    height=4.0 * inch,
                                )
                            )

                            visual_added = True

                except Exception as e:
                    print(
                        f"Chart Error in section {i + 1}: {e}"
                    )

            # ---------------- IMAGE SECTION ----------------
            # Image-designated sections never fall back to charts.
            if not prefer_chart and image_url:
                try:
                    response = requests.get(
                        image_url,
                        timeout=15,
                    )
                    response.raise_for_status()

                    if not response.content:
                        raise ValueError("Downloaded image is empty.")

                    image_stream = BytesIO(response.content)
                    image_streams.append(image_stream)

                    section.append(
                        Image(
                            image_stream,
                            width=6.0 * inch,
                            height=3.8 * inch,
                        )
                    )

                    visual_added = True

                except Exception as e:
                    print(
                        f"Image Error in section {i + 1}: {e}"
                    )

            # ---------------- IMAGE FALLBACK ----------------
            # If a chart fails, try an image.
            # Never show a chart on an image-designated section.
            if prefer_chart and not visual_added and image_url:
                try:
                    response = requests.get(
                        image_url,
                        timeout=15,
                    )
                    response.raise_for_status()

                    if not response.content:
                        raise ValueError("Downloaded image is empty.")

                    image_stream = BytesIO(response.content)
                    image_streams.append(image_stream)

                    section.append(
                        Image(
                            image_stream,
                            width=6.0 * inch,
                            height=3.8 * inch,
                        )
                    )

                    visual_added = True

                except Exception as e:
                    print(
                        f"Fallback Image Error in section {i + 1}: {e}"
                    )

            if not visual_added:
                print(
                    f"WARNING: No visual available for section "
                    f"{i + 1}: {slide.get('title', '')}"
                )

            section.append(Spacer(1, 15))
            elements.append(KeepTogether(section))

            if i < len(slides) - 1:
                elements.append(PageBreak())

        # Build the PDF before closing streams or deleting chart files.
        doc.build(
            elements,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number,
        )

        print(f"PDF generated successfully: {file_path}")
        return file_path

    finally:
        # Release image streams after ReportLab has finished building.
        for stream in image_streams:
            stream.close()

        # Remove temporary assets only after the build attempt.
        for pattern in (
            "outputs/img_*.jpg",
            "outputs/chart_*.png",
        ):
            for temporary_file in glob.glob(pattern):
                try:
                    os.remove(temporary_file)
                except OSError as e:
                    print(
                        f"Cleanup warning for {temporary_file}: {e}"
                    )
