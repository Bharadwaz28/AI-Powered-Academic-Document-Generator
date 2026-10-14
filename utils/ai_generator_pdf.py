
import os
import re
import math

from groq import Groq
from dotenv import load_dotenv
from utils.image_fetcher_pdf import get_image_url
from utils.chart_generator_pdf import generate_chart


# ============================================================
# CHECKPOINT 1: CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "").strip()

if not API_KEY:
    raise RuntimeError(
        "CHECKPOINT 1 FAILED: GROQ_API_KEY is missing. "
        "Configure it in .env or Streamlit Cloud Secrets."
    )

client = Groq(api_key=API_KEY)

MODEL = "openai/gpt-oss-120b"

print("CHECKPOINT 1 PASSED: Groq client configured.")


# ============================================================
# SHARED MODEL CALL WITH EMPTY-RESPONSE DIAGNOSTICS
# ============================================================

def ask_ai(prompt, max_tokens=1200, temperature=0.3):
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
            "Groq returned empty text. "
            f"Model={MODEL}, "
            f"finish_reason={choice.finish_reason}, "
            f"usage={response.usage}"
        )

    return content.strip()


# ============================================================
# CHECKPOINT 2: SECTION TITLES
# ============================================================

def generate_section_titles(topic, sections):
    prompt = f"""
You are writing an academic report.

The user's exact report topic is:
{topic}

Generate exactly {sections} distinct section titles about THIS topic.

Requirements:
- Number them 1 through {sections}.
- Use a logical academic structure.
- Make every title specific to the requested topic.
- Do not switch to a different topic.
- Do not use generic titles such as Additional Analysis.
- Do not include explanations or Markdown fences.
- Return one numbered title per line.

The report topic must remain: {topic}
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"CHECKPOINT 2: Title generation attempt {attempt}/3. "
                f"Topic={topic!r}"
            )

            raw = ask_ai(
                prompt,
                max_tokens=max(1200, sections * 100),
                temperature=0.2,
            )

            titles = []

            for line in raw.splitlines():
                line = line.strip()

                match = re.match(
                    r"^\s*(\d+)[.)\-:]\s*(.+?)\s*$",
                    line,
                )

                if not match:
                    continue

                number = int(match.group(1))
                title = match.group(2).strip().strip("*").strip()

                if number < 1 or number > sections:
                    continue

                if not title:
                    continue

                if any(
                    existing.lower() == title.lower()
                    for existing in titles
                ):
                    continue

                titles.append(title)

            if len(titles) != sections:
                raise ValueError(
                    f"Expected {sections} titles, parsed {len(titles)}. "
                    f"Raw response: {raw[:700]}"
                )

            # A clear diagnostic: this helps detect a wrong topic
            # being passed from app.py.
            print("CHECKPOINT 2 PASSED:", titles)

            return titles

        except Exception as exc:
            last_error = exc
            print(f"TITLE ERROR: {exc}")

    raise RuntimeError(
        f"CHECKPOINT 2 FAILED for topic {topic!r}: {last_error}"
    )


# ============================================================
# CHECKPOINT 3: ACADEMIC CONTENT
# ============================================================

def split_into_two_paragraphs(content):
    content = re.sub(
        r"^\s*TEXT\s*:\s*",
        "",
        content,
        count=1,
        flags=re.IGNORECASE,
    ).strip()

    content = re.sub(
        r"^\s*```(?:text|markdown)?\s*|\s*```\s*$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", content)
        if p.strip()
    ]

    if len(paragraphs) == 2:
        return paragraphs

    # Some model responses use single newlines rather than blank lines.
    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if len(lines) == 2:
        return lines

    # If the model returns one continuous block, split at a sentence
    # boundary near the middle rather than rejecting good prose.
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

OVERALL REPORT TOPIC: {topic}
SECTION TITLE: {section_title}

Write exactly two substantive paragraphs, approximately
80-100 words per paragraph.

Rules:
- Discuss the specified section within the overall topic.
- Do not change the subject to an unrelated topic.
- Explain concepts, applications, implications, or limitations.
- Use accurate information.
- Do not invent statistics, citations, or research findings.
- Do not include the section heading.
- Do not include a preamble, numbered list, or Markdown heading.
- Separate the two paragraphs with a blank line.
- Return the paragraphs only.
"""

    last_error = None

    for attempt in range(1, 4):
        try:
            print(
                f"CHECKPOINT 3: Writing section {section_title!r}; "
                f"attempt {attempt}/3."
            )

            content = ask_ai(
                prompt,
                max_tokens=1600,
                temperature=0.2,
            )

            paragraphs = split_into_two_paragraphs(content)
            word_count = len(content.split())

            if len(paragraphs) != 2 or word_count < 100:
                raise ValueError(
                    f"Expected two paragraphs and at least 100 words; "
                    f"got {len(paragraphs)} paragraphs and "
                    f"{word_count} words. Response={content[:400]!r}"
                )

            result = "\n\n".join(paragraphs)

            print(
                f"CHECKPOINT 3 PASSED: {section_title!r}, "
                f"{len(result.split())} words."
            )

            return result

        except Exception as exc:
            last_error = exc
            print(f"CONTENT ERROR: {exc}")

    raise RuntimeError(
        f"CHECKPOINT 3 FAILED for {section_title!r}: {last_error}"
    )


# ============================================================
# CHECKPOINT 4: CHART DATA
# ============================================================

def generate_chart(topic, section_title, content):
    """
    Produce clearly labelled illustrative data for chart rendering.

    These are not observed stock prices or real research statistics.
    The existing pdf_generator.py renders this dictionary into an image.
    """

    prompt = f"""
Create an ILLUSTRATIVE example chart for an academic report.

Topic: {topic}
Section: {section_title}
Section content:
{content}

These values are hypothetical examples, NOT real-world observations.

Return exactly two lines:
LABELS: four short, distinct category names
VALUES: four numeric values between 1 and 100

Rules:
- Use four categories relevant to the section.
- Do not claim that the values are real statistics.
- Do not include explanations, Markdown, or other lines.
"""

    try:
        raw = ask_ai(
            prompt,
            max_tokens=300,
            temperature=0.1,
        )

        labels = []
        values = []

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
            or len({label.lower() for label in labels}) != 4
            or any(not math.isfinite(v) or not 1 <= v <= 100
                   for v in values)
        ):
            print(
                f"CHECKPOINT 4: Invalid chart data for {section_title!r}; "
                "using an image instead."
            )
            return None

        chart_data = {
            "labels": labels,
            "values": values,
            "type": "bar",
            "title": f"{section_title} (Illustrative Example)",
        }

        print(f"CHECKPOINT 4 PASSED: {section_title!r}")
        return chart_data

    except Exception as exc:
        # Chart failure must not discard successfully generated content.
        print(f"CHART WARNING for {section_title!r}: {exc}")
        return None


# ============================================================
# CHECKPOINT 5: MAIN FUNCTION
# ============================================================

def generate_ai_content(topic, sections, category, format_type):
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("CHECKPOINT 5 FAILED: Topic is empty.")

    if (
        not isinstance(sections, int)
        or isinstance(sections, bool)
        or not 1 <= sections <= 20
    ):
        raise ValueError(
            "CHECKPOINT 5 FAILED: Sections must be between 1 and 20."
        )

    topic = topic.strip()

    print("=" * 60)
    print("REPORT GENERATION STARTED")
    print(f"ACTUAL TOPIC RECEIVED: {topic!r}")
    print(f"SECTIONS REQUESTED: {sections}")
    print(f"CATEGORY: {category!r}")
    print(f"FORMAT: {format_type!r}")
    print("=" * 60)

    titles = generate_section_titles(topic, sections)
    slides = []

    for index, title in enumerate(titles, start=1):
        print(f"\nSECTION {index}/{sections}: {title}")

        content = generate_section_content(topic, title)


        # ---------- CHART OR IMAGE: EXACTLY ONE ----------
        
        chart_data = generate_chart(
            topic,
            title,
            content
        )
        
        image_url = None
        image_url = get_image_url(f"{title} {topic}")
        
        slides.append({
            "title": title,
            "content": content,
            "image_url": image_url,
            "chart_data": chart_data
        })

    print(f"CHECKPOINT 5 PASSED: Section {index} validated.")

    if len(slides) != sections:
        raise RuntimeError(
            f"Expected {sections} slides, generated {len(slides)}."
        )

    print("=" * 60)
    print(f"ALL CHECKPOINTS PASSED: {len(slides)} sections generated.")
    print("=" * 60)

    return slides
