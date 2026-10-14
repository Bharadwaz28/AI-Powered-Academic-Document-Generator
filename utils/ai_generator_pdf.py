
import os
import re
import math
from groq import Groq
from dotenv import load_dotenv

from utils.image_fetcher_pdf import get_image_url


# ============================================================
# CHECKPOINT 1: CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Configure it in .env "
        "or Streamlit Cloud Secrets."
    )

client = Groq(api_key=API_KEY)
MODEL = "openai/gpt-oss-120b"

print("CHECKPOINT 1 PASSED: Groq configured.")


def ask_ai(prompt, max_tokens=1200, temperature=0.3):
    """Call Groq and reject empty responses with a useful error."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_completion_tokens=max_tokens,
        reasoning_effort="low",
        reasoning_format="hidden",
    )

    if not response.choices:
        raise RuntimeError("Groq returned no completion choices.")

    choice = response.choices[0]
    content = choice.message.content

    if not content or not content.strip():
        raise RuntimeError(
            "Groq returned empty content. "
            f"Finish reason: {choice.finish_reason}"
        )

    return content.strip()


# ============================================================
# CHECKPOINT 2: SECTION TITLES
# ============================================================

def generate_section_titles(topic, sections):
    prompt = f"""
Create exactly {sections} unique academic report section titles.

Report topic: {topic}

Rules:
- Every title must be directly relevant to the report topic.
- Number titles consecutively from 1 to {sections}.
- Use a logical academic structure.
- Do not introduce an unrelated subject.
- Do not use generic titles like Additional Analysis.
- Return only numbered titles, one per line.

The report topic is exactly: {topic}
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            raw = ask_ai(
                prompt,
                max_tokens=max(1200, sections * 100),
                temperature=0.2,
            )

            found = {}

            for line in raw.splitlines():
                match = re.match(
                    r"^\s*(\d+)[.)\-:]\s*(.+?)\s*$",
                    line.strip(),
                )

                if not match:
                    continue

                number = int(match.group(1))
                title = match.group(2).strip().strip("*").strip()

                if 1 <= number <= sections and title:
                    found[number] = title

            if len(found) != sections:
                raise ValueError(
                    f"Expected {sections} numbered titles, "
                    f"received {len(found)}. Response: {raw[:500]}"
                )

            titles = [found[n] for n in range(1, sections + 1)]

            if len({t.casefold() for t in titles}) != sections:
                raise ValueError("The model returned duplicate titles.")

            print("CHECKPOINT 2 PASSED:", titles)
            return titles

        except Exception as exc:
            last_error = exc
            print(f"TITLE ATTEMPT {attempt} FAILED: {exc}")

    raise RuntimeError(
        f"Could not generate section titles: {last_error}"
    )


# ============================================================
# CHECKPOINT 3: ACADEMIC CONTENT
# ============================================================

def split_paragraphs(text):
    text = re.sub(
        r"^\s*TEXT\s*:\s*",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    ).strip()

    text = re.sub(
        r"^\s*```(?:text|markdown)?\s*|\s*```\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]

    if len(paragraphs) == 2:
        return paragraphs

    # Handle single-line-break paragraph separation.
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) == 2:
        return lines

    # Handle a single continuous block by splitting at a sentence boundary.
    if len(paragraphs) == 1:
        sentences = re.split(r"(?<=[.!?])\s+", paragraphs[0])

        if len(sentences) >= 4:
            midpoint = len(sentences) // 2
            return [
                " ".join(sentences[:midpoint]).strip(),
                " ".join(sentences[midpoint:]).strip(),
            ]

    return paragraphs


def generate_section_content(topic, section_title):
    prompt = f"""
Write an academic report section.

Overall report topic: {topic}
Section title: {section_title}

Requirements:
- Write exactly two substantive paragraphs.
- Aim for 80-100 words per paragraph.
- Discuss this section within the overall report topic.
- Explain relevant concepts, applications, implications, or limitations.
- Use accurate information and academic language.
- Do not invent statistics, citations, or research findings.
- Do not repeat the heading.
- Return only the paragraphs, separated by a blank line.
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            content = ask_ai(
                prompt,
                max_tokens=1600,
                temperature=0.2,
            )

            paragraphs = split_paragraphs(content)
            word_count = len(content.split())

            if len(paragraphs) != 2 or word_count < 100:
                raise ValueError(
                    f"Expected two paragraphs and at least 100 words; "
                    f"received {len(paragraphs)} paragraphs and "
                    f"{word_count} words."
                )

            result = "\n\n".join(paragraphs)
            print(
                f"CHECKPOINT 3 PASSED: {section_title} "
                f"({len(result.split())} words)"
            )
            return result

        except Exception as exc:
            last_error = exc
            print(
                f"CONTENT ATTEMPT {attempt} FAILED "
                f"for {section_title}: {exc}"
            )

    raise RuntimeError(
        f"Could not generate valid content for "
        f"'{section_title}': {last_error}"
    )


# ============================================================
# CHECKPOINT 4: ILLUSTRATIVE CHART DATA
# ============================================================

def generate_chart_data(topic, section_title, content):
    """
    Create clearly labelled illustrative data.
    These values are not real stock-market observations.
    """

    prompt = f"""
Create an illustrative example chart for an academic report.

Topic: {topic}
Section: {section_title}
Content:
{content}

The values are hypothetical examples, NOT real-world measurements.
Choose four relevant, distinct categories and four numeric values
between 1 and 100.

Return exactly:
LABELS: Category A, Category B, Category C, Category D
VALUES: 20, 40, 60, 80

Replace the examples with relevant labels and illustrative values.
Return no other text.
"""

    try:
        raw = ask_ai(
            prompt,
            max_tokens=300,
            temperature=0.1,
        )

        labels, values = [], []

        for line in raw.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            if key.strip().upper() == "LABELS":
                labels = [x.strip() for x in value.split(",")]

            elif key.strip().upper() == "VALUES":
                try:
                    values = [
                        float(x.strip().replace("%", ""))
                        for x in value.split(",")
                    ]
                except ValueError:
                    return None

        if (
            len(labels) != 4
            or len(values) != 4
            or any(not label for label in labels)
            or len({label.casefold() for label in labels}) != 4
            or any(
                not math.isfinite(v) or not 1 <= v <= 100
                for v in values
            )
        ):
            print(f"Invalid chart data for {section_title}; using image.")
            return None

        return {
            "labels": labels,
            "values": values,
            "type": "bar",
            "title": f"{section_title} (Illustrative Example)",
        }

    except Exception as exc:
        print(f"CHART DATA WARNING for {section_title}: {exc}")
        return None


# ============================================================
# CHECKPOINT 5: MAIN GENERATOR
# ============================================================

def generate_ai_content(topic, sections, category, format_type):
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic cannot be empty.")

    if (
        not isinstance(sections, int)
        or isinstance(sections, bool)
        or not 1 <= sections <= 20
    ):
        raise ValueError("Sections must be between 1 and 20.")

    topic = topic.strip()

    print("=" * 60)
    print(f"REPORT TOPIC RECEIVED: {topic!r}")
    print(f"SECTIONS REQUESTED: {sections}")
    print(f"CATEGORY: {category!r}")
    print(f"FORMAT: {format_type!r}")
    print("=" * 60)

    titles = generate_section_titles(topic, sections)
    slides = []

    for index, title in enumerate(titles, start=1):
        print(f"Generating section {index}/{sections}: {title}")

        content = generate_section_content(topic, title)
        chart_data = generate_chart_data(topic, title, content)

        # Always fetch an image independently of chart availability.
        # pdf_generator.py will randomly choose one visual.
        image_url = get_image_url(f"{title} {topic}")

        slides.append({
            "title": title,
            "content": content,
            "image_url": image_url,
            "chart_data": chart_data,
        })

    if len(slides) != sections:
        raise RuntimeError(
            f"Expected {sections} sections; generated {len(slides)}."
        )

    if any(
        slide["title"].casefold().startswith("additional analysis")
        for slide in slides
    ):
        raise RuntimeError("A generic placeholder title was detected.")

    print(f"CHECKPOINT 5 PASSED: {len(slides)} sections generated.")
    return slides
