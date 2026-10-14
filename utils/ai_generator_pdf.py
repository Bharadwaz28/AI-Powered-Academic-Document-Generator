
import os
import re

from groq import Groq
from dotenv import load_dotenv

from utils.image_fetcher_pdf import get_image_url


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is missing. Configure it in .env "
        "locally or Streamlit Cloud Secrets when deployed."
    )

client = Groq(api_key=api_key)

TITLE_MODEL = "openai/gpt-oss-120b"
CONTENT_MODEL = "llama-3.1-8b-instant"


def parse_section_titles(title_text, expected_count):
    """Extract numbered titles and reject incomplete model responses."""

    titles = []

    for line in title_text.splitlines():
        line = line.strip()

        # Ignore Markdown code fences and empty lines.
        if not line or line.startswith("```"):
            continue

        match = re.match(
            r"^\s*(?:\*\*)?\s*(\d+)[.)\-:]\s*(.+?)\s*(?:\*\*)?\s*$",
            line
        )

        if not match:
            continue

        title = match.group(2).strip().strip("*").strip()

        # Remove unwanted generic prefixes without damaging
        # legitimate topic-specific section titles.
        title = re.sub(
            r"^(?:AI|Artificial Intelligence)\s*[-:|]\s*",
            "",
            title,
            flags=re.IGNORECASE
        ).strip()

        if title and title.lower() not in {
            existing.lower() for existing in titles
        }:
            titles.append(title)

    if len(titles) != expected_count:
        raise ValueError(
            f"Expected {expected_count} unique section titles, "
            f"but parsed {len(titles)}. "
            f"Model response: {title_text[:1000]}"
        )

    return titles


def generate_section_titles(topic, sections):
    prompt = f"""
Generate exactly {sections} unique, informative academic report
section titles about the topic: {topic}

Requirements:
- Return exactly {sections} numbered titles.
- Number consecutively from 1 to {sections}.
- Make every title specific to the topic.
- Use an appropriate academic report structure.
- Do not include explanations or introductory text.
- Do not use generic titles such as "Additional Analysis".
- Avoid repeating the topic as the entire title.

Example format:
1. Introduction to the Topic
2. Key Concepts and Principles
3. Applications and Implications
"""

    response = client.chat.completions.create(
        model=TITLE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=max(300, sections * 80)
    )

    title_text = response.choices[0].message.content or ""

    if not title_text.strip():
        raise ValueError("The AI returned an empty section-title response.")

    titles = parse_section_titles(title_text, sections)

    print(f"Successfully generated {len(titles)} section titles.")

    return titles


def generate_section_content(topic, aspect):
    """Generate topic-specific academic content."""

    prompt = f"""
Write an informative academic report section.

Overall topic: {topic}
Section title: {aspect}

Requirements:
- Write two substantive academic paragraphs.
- Aim for 80-100 words per paragraph.
- Discuss the actual topic and section, not unrelated subjects.
- Explain relevant concepts, mechanisms, applications, and limitations.
- Use specific, accurate details where possible.
- Never invent statistics, studies, citations, or numerical findings.
- Do not repeat the section heading.
- Do not include Markdown headings, numbered lists, or a preamble.
- Separate the two paragraphs with a blank line.
- Return only the section text.
"""

    response = client.chat.completions.create(
        model=CONTENT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=650
    )

    content = (response.choices[0].message.content or "").strip()

    # Remove a response label if the model adds one.
    content = re.sub(
        r"^\s*TEXT\s*:\s*",
        "",
        content,
        count=1,
        flags=re.IGNORECASE
    ).strip()

    if not content:
        raise ValueError(f"Empty content returned for section: {aspect}")

    # Preserve paragraph separation while removing empty paragraphs.
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", content)
        if paragraph.strip()
    ]

    # Don't silently replace incomplete AI output with generic filler.
    if len(paragraphs) < 2:
        raise ValueError(
            f"Incomplete content for '{aspect}': "
            f"expected two paragraphs, got {len(paragraphs)}. "
            f"Response: {content[:500]}"
        )

    if len(content.split()) < 80:
        raise ValueError(
            f"Content for '{aspect}' is too short "
            f"({len(content.split())} words)."
        )

    return "\n\n".join(paragraphs[:2])


def generate_chart(topic, aspect, content):
    """
    Extract chart data only when the section contains explicit,
    meaningful quantitative information.

    Returns chart data for pdf_generator.py to render, or None.
    """

    prompt = f"""
Determine whether the following academic section contains enough
explicit quantitative information to create a meaningful chart.

Topic: {topic}
Section: {aspect}
Content:
{content}

Rules:
- Use only numerical facts explicitly stated in the content.
- Never invent values, statistics, percentages, or measurements.
- Do not turn qualitative claims into numerical scores.
- Use at least 3 distinct, explicitly supported categories or data points.
- If there is insufficient quantitative information, return exactly:
NO_CHART

Otherwise return exactly these two lines:
LABELS: label1, label2, label3
VALUES: value1, value2, value3

Use numeric values. Do not add explanations or Markdown.
"""

    response = client.chat.completions.create(
        model=CONTENT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=180
    )

    result = (response.choices[0].message.content or "").strip()

    if not result or "NO_CHART" in result.upper():
        return None

    labels = []
    values = []

    for line in result.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().upper()

        if key == "LABELS":
            labels = [item.strip() for item in value.split(",")]

        elif key == "VALUES":
            try:
                values = [
                    float(item.strip().replace("%", ""))
                    for item in value.split(",")
                ]
            except ValueError:
                return None

    if (
        len(labels) < 3
        or len(labels) != len(values)
        or any(not label for label in labels)
        or any(not __import__("math").isfinite(v) for v in values)
    ):
        return None

    # Keep the data structure expected by chart_generator_pdf.py.
    return {
        "labels": labels,
        "values": values,
        "type": "bar",
        "title": f"{aspect} — Reported Data"
    }


def generate_ai_content(topic, sections, category, format_type):
    """
    Generate report sections.

    The returned structure remains compatible with the existing
    PDF and PPT generation workflow.
    """

    if not isinstance(sections, int) or sections < 1:
        raise ValueError("sections must be a positive integer.")

    slides = []
    aspects = generate_section_titles(topic, sections)

    for section_number, aspect in enumerate(aspects, start=1):
        print(
            f"Generating section {section_number}/{sections}: {aspect}"
        )

        try:
            content = generate_section_content(topic, aspect)

            chart_data = generate_chart_data(
                topic=topic,
                aspect=aspect,
                content=content
            )

            # Preserve the existing image fetcher functionality.
            image_url = None

            if chart_data is None:
                image_url = get_image_url(f"{aspect} {topic}")

            slides.append({
                "title": aspect,
                "content": content,
                "image_url": image_url,
                "chart_data": chart_data
            })

        except Exception as exc:
            # Fail visibly rather than generating a misleading report.
            raise RuntimeError(
                f"Failed to generate section "
                f"{section_number} ('{aspect}'): {exc}"
            ) from exc

    if len(slides) != sections:
        raise RuntimeError(
            f"Expected {sections} sections, but generated {len(slides)}."
        )

    print(f"Successfully generated all {len(slides)} sections.")

    return slides
