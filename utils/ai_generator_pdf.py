
from utils.image_fetcher_pdf import get_image_url
from utils.chart_generator_pdf import generate_chart
from dotenv import load_dotenv
from groq import Groq
import math
import os
import re


# ============================================================
# CHECKPOINT 1: CONFIGURATION AND API VALIDATION
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key or not api_key.strip():
    raise ValueError(
        "CHECKPOINT 1 FAILED: GROQ_API_KEY is missing. "
        "Configure it in .env or Streamlit Cloud Secrets."
    )

client = Groq(api_key=api_key.strip())

MODEL = "openai/gpt-oss-120b"

print("CHECKPOINT 1 PASSED: Groq client configured.")


# ============================================================
# CHECKPOINT 2: SECTION TITLE GENERATION
# ============================================================

def parse_section_titles(text, expected_count):
    """Extract numbered titles and validate count and uniqueness."""

    titles = []

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("```"):
            continue

        match = re.match(
            r"^\s*(?:\*\*)?\s*(\d+)[.)\-:]\s*(.+?)\s*(?:\*\*)?\s*$",
            line
        )

        if not match:
            continue

        title = match.group(2).strip().strip("*").strip()

        # Remove only unwanted introductory prefixes.
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
            f"Expected {expected_count} unique titles, "
            f"but parsed {len(titles)}. "
            f"Response: {text[:800]}"
        )

    return titles


def generate_section_titles(topic, sections):

    prompt = f"""
Generate exactly {sections} unique academic report section titles.

Report topic: {topic}

Rules:
- Number titles consecutively from 1 to {sections}.
- Make every title specific to the topic.
- Use a logical academic report structure.
- Avoid generic titles such as Additional Analysis.
- Do not add introductions, explanations, or Markdown.
- Do not repeat titles.

Return only the numbered titles.
"""

    last_error = None

    for attempt in range(1, 3):
        try:
            print(
                f"CHECKPOINT 2: Generating titles, attempt {attempt}/2."
            )

            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=max(300, sections * 80)
            )

            text = response.choices[0].message.content or ""

            titles = parse_section_titles(text, sections)

            print(
                f"CHECKPOINT 2 PASSED: {len(titles)} valid titles."
            )

            return titles

        except Exception as exc:
            last_error = exc
            print(f"TITLE GENERATION ERROR: {exc}")

    raise RuntimeError(
        f"CHECKPOINT 2 FAILED: Could not generate valid titles. "
        f"Last error: {last_error}"
    )


# ============================================================
# CHECKPOINT 3: ACADEMIC CONTENT GENERATION
# ============================================================


def generate_section_content(topic, section_title):

    prompt = f"""
Write an academic report section about the following.

Overall topic: {topic}
Section title: {section_title}

Write exactly TWO paragraphs, each containing approximately
80-100 words.

Discuss the specified topic directly. Do not introduce an
unrelated topic. Do not add a heading, numbering, preamble,
or the label TEXT:.

Separate the paragraphs with a blank line.
Return only the paragraphs.
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"Generating '{section_title}', attempt {attempt}/3"
            )

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=650
            )

            content = (
                response.choices[0].message.content or ""
            ).strip()

            # Remove optional Markdown fences.
            content = re.sub(
                r"^\s*```(?:text|markdown)?\s*",
                "",
                content,
                flags=re.IGNORECASE
            )
            content = re.sub(r"\s*```\s*$", "", content)

            # Remove an optional TEXT: prefix.
            content = re.sub(
                r"^\s*TEXT\s*:\s*",
                "",
                content,
                count=1,
                flags=re.IGNORECASE
            ).strip()

            # Split on blank lines first.
            paragraphs = [
                p.strip()
                for p in re.split(r"\n\s*\n", content)
                if p.strip()
            ]

            # If the model used single line breaks, split lines.
            if len(paragraphs) == 1:
                lines = [
                    line.strip()
                    for line in content.splitlines()
                    if line.strip()
                ]

                if len(lines) == 2:
                    paragraphs = lines

            word_count = len(content.split())

            if len(paragraphs) != 2 or word_count < 100:
                last_error = ValueError(
                    f"Expected two paragraphs and at least 100 words; "
                    f"got {len(paragraphs)} paragraphs and "
                    f"{word_count} words. Response: {content[:300]!r}"
                )

                print(f"CONTENT VALIDATION: {last_error}")
                continue

            print(
                f"CONTENT CHECKPOINT PASSED: {word_count} words"
            )

            return "\n\n".join(paragraphs)

        except Exception as exc:
            last_error = exc
            print(f"CONTENT GENERATION ATTEMPT FAILED: {exc}")

    raise RuntimeError(
        f"Could not generate valid content for '{section_title}'. "
        f"Last error: {last_error}"
    )



# ============================================================
# CHECKPOINT 4: CHART DATA GENERATION
# ============================================================

def generate_chart(topic, section_title, content):
    """
    Generate explicitly illustrative chart data.

    These values are NOT real-world statistics. They must be
    labelled illustrative in the resulting chart title.
    """

    prompt = f"""
Create a small ILLUSTRATIVE chart for an academic report.

Topic: {topic}
Section: {section_title}
Section content:
{content}

Important:
- These are illustrative example values, NOT real statistics.
- Do not claim the values are observed, measured, or researched.
- Choose four meaningful categories related to the section.
- Use simple positive numeric values between 1 and 100.
- Choose a bar chart.
- Do not use the same labels for every section.
- Return exactly these two lines and nothing else:

LABELS: Category A, Category B, Category C, Category D
VALUES: 20, 40, 60, 80

Replace the example categories and values with suitable
illustrative data for this section.
"""

    try:
        print(
            f"CHECKPOINT 4: Creating illustrative chart "
            f"for '{section_title}'."
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=180
        )

        result = (response.choices[0].message.content or "").strip()

        labels = []
        values = []

        for line in result.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().upper()

            if key == "LABELS":
                labels = [
                    item.strip()
                    for item in value.split(",")
                ]

            elif key == "VALUES":
                try:
                    values = [
                        float(item.strip().replace("%", ""))
                        for item in value.split(",")
                    ]
                except ValueError:
                    return None

        if (
            len(labels) != 4
            or len(values) != 4
            or any(not label for label in labels)
            or len({label.lower() for label in labels}) != 4
            or any(not math.isfinite(value) for value in values)
            or any(value < 0 or value > 100 for value in values)
        ):
            print(
                f"CHECKPOINT 4: Invalid chart data for "
                f"'{section_title}'. Using an image instead."
            )
            return None

        chart_data = {
            "labels": labels,
            "values": values,
            "type": "bar",
            "title": f"{section_title} (Illustrative Data)"
        }

        print(
            f"CHECKPOINT 4 PASSED: Valid illustrative chart data "
            f"for '{section_title}'."
        )

        return chart_data

    except Exception as exc:
        # Chart generation is optional. A chart failure must not
        # discard otherwise valid academic section content.
        print(
            f"CHART DATA WARNING for '{section_title}': {exc}"
        )
        return None


# ============================================================
# CHECKPOINT 5: MAIN REPORT GENERATION
# ============================================================

def generate_ai_content(topic, sections, category, format_type):

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("CHECKPOINT 5 FAILED: Topic cannot be empty.")

    if (
        not isinstance(sections, int)
        or isinstance(sections, bool)
        or sections < 1
        or sections > 20
    ):
        raise ValueError(
            "CHECKPOINT 5 FAILED: Sections must be between 1 and 20."
        )

    topic = topic.strip()

    print("=" * 60)
    print("STARTING REPORT GENERATION")
    print(f"Topic: {topic}")
    print(f"Requested sections: {sections}")
    print(f"Category: {category}")
    print(f"Format: {format_type}")
    print("=" * 60)

    # Generate all titles before creating any section.
    titles = generate_section_titles(topic, sections)

    slides = []

    for index, section_title in enumerate(titles):

        print(
            f"\nSECTION {index + 1}/{sections}: {section_title}"
        )

        # A content failure is fatal: never silently replace
        # a failed section with generic text.
        content = generate_section_content(
            topic,
            section_title
        )

        chart_data = generate_chart(
            topic,
            section_title,
            content
        )

        # Preserve the existing image fetcher.
        image_url = None

        if chart_data is None:
            image_url = get_image_url(
                f"{section_title} {topic}"
            )

        slide = {
            "title": section_title,
            "content": content,
            "image_url": image_url,
            "chart_data": chart_data
        }

        slides.append(slide)

        # CHECKPOINT 5: Validate the section before proceeding.
        assert slide["title"].strip()
        assert len(slide["content"].split()) >= 100
        assert "\n\n" in slide["content"]

        print(
            f"CHECKPOINT 5 PASSED: Section {index + 1} validated."
        )

    if len(slides) != sections:
        raise RuntimeError(
            f"CHECKPOINT 5 FAILED: Expected {sections} sections, "
            f"generated {len(slides)}."
        )

    if any(
        slide["title"].lower().startswith("additional analysis")
        for slide in slides
    ):
        raise RuntimeError(
            "CHECKPOINT 5 FAILED: Generic placeholder title detected."
        )

    print("=" * 60)
    print(f"CHECKPOINT 5 PASSED: {len(slides)} sections validated.")
    print("REPORT CONTENT GENERATION COMPLETED.")
    print("=" * 60)

    # Keep the original interface expected by the PDF/PPT workflow.
    return slides
