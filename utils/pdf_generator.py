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

    # Keep references to in-memory image streams until doc.build ends.
    image_streams = []
    temporary_files = []

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

            # Choose ONE visual per section.
            # Alternate chart/image when both resources are available.
            chart_data = slide.get("chart_data")
            img_url = slide.get("image_url")

            prefer_chart = bool(chart_data) and (
                not img_url or i % 2 == 0
            )

            visual_added = False

            # ---------------- CHART ----------------
            if prefer_chart:
                try:
                    chart_path = generate_chart(chart_data, i)

                    if chart_path and os.path.isfile(chart_path):
                        # Read chart bytes immediately. This avoids
                        # ReportLab later trying to reopen a deleted file.
                        with open(chart_path, "rb") as chart_file:
                            chart_bytes = chart_file.read()

                        if chart_bytes:
                            stream = BytesIO(chart_bytes)
                            image_streams.append(stream)

                            section.append(
                                Image(
                                    stream,
                                    width=6.2 * inch,
                                    height=4.0 * inch,
                                )
                            )

                            visual_added = True

                except Exception as e:
                    print(f"Chart Error for section {i + 1}: {e}")

            # ---------------- IMAGE ----------------
            # Use the image if selected, or if chart generation failed.
            if not visual_added and img_url:
                try:
                    response = requests.get(
                        img_url,
                        timeout=15,
                    )
                    response.raise_for_status()

                    image_bytes = response.content

                    if image_bytes:
                        stream = BytesIO(image_bytes)
                        image_streams.append(stream)

                        section.append(
                            Image(
                                stream,
                                width=6.0 * inch,
                                height=3.8 * inch,
                            )
                        )

                        visual_added = True

                except Exception as e:
                    print(f"Image Error for section {i + 1}: {e}")

            # If chart was not preferred and no image could be loaded,
            # try the chart as a final fallback.
            if (
                not visual_added
                and chart_data
                and not prefer_chart
            ):
                try:
                    chart_path = generate_chart(chart_data, i)

                    if chart_path and os.path.isfile(chart_path):
                        with open(chart_path, "rb") as chart_file:
                            chart_bytes = chart_file.read()

                        if chart_bytes:
                            stream = BytesIO(chart_bytes)
                            image_streams.append(stream)

                            section.append(
                                Image(
                                    stream,
                                    width=6.2 * inch,
                                    height=4.0 * inch,
                                )
                            )

                            visual_added = True

                except Exception as e:
                    print(f"Fallback Chart Error for section {i + 1}: {e}")

            section.append(Spacer(1, 15))
            elements.append(KeepTogether(section))

            if i < len(slides) - 1:
                elements.append(PageBreak())

        # Build before removing any generated chart files.
        doc.build(
            elements,
            onFirstPage=add_page_number,
            onLaterPages=add_page_number,
        )

        print(f"PDF generated successfully: {file_path}")
        return file_path

    finally:
        # Clean up only after ReportLab has finished building the PDF.
        for stream in image_streams:
            stream.close()

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
