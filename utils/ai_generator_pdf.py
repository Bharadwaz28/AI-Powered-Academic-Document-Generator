import os
import re
import random
from groq import Groq
from dotenv import load_dotenv
from utils.image_fetcher_pdf import get_image_url

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_ai_content(topic, sections, category, format_type):

    slides = []

    # ---------- GENERATE SECTION TITLES ----------

    title_prompt = f"""
    Generate EXACTLY {sections} unique section titles for an academic report on:

    {topic}

    IMPORTANT RULES:
    - Return EXACTLY {sections} titles.
    - Number them from 1 to {sections}.
    - Each title must be unique.
    - Do NOT skip any number.
    - Do NOT add explanations.
    - Do NOT add bullet points.

    Example:

    1. Introduction
    2. Applications
    3. Challenges
    """

    title_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": title_prompt}],
        temperature=0.6,
        max_tokens=300
    )

    title_text = title_response.choices[0].message.content.strip()

    aspects = []

    for line in title_text.split("\n"):

        line = line.strip()

        if not line:
            continue

        match = re.match(
            r'^\s*\d+[\.\)\-:]\s*(.+)$',
            line
        )

        if match:

            title = match.group(1).strip()

            title = re.sub(
                r'^(ai|artificial intelligence)\s*[-:|]\s*',
                '',
                title,
                flags=re.IGNORECASE
            )

            title = re.sub(
                r'^(artificial intelligence)\s*',
                '',
                title,
                flags=re.IGNORECASE
            )

            aspects.append(title)

    # ---------- FALLBACK TITLES ----------
    while len(aspects) < sections:
        aspects.append(
            f"Additional Analysis {len(aspects)+1}"
        )

    aspects = aspects[:sections]

    print(
        f"Requested={sections}, Generated={len(aspects)}"
    )

    # ---------- CHART DETECTION KEYWORDS ----------

    analysis_keywords = [
        "analysis",
        "comparison",
        "trend",
        "performance",
        "growth",
        "forecast",
        "statistics",
        "market",
        "industry",
        "applications",
        "impact",
        "role",
        "effects",
        "study",
        "evaluation",
        "research",
        "development",
        "future"
    ]

    # ---------- GENERATE CONTENT ----------
    pages_since_chart = 0

    for idx, aspect in enumerate(aspects):

        prompt = f"""
        Write an academic report section.

        Topic: {topic}
        Section: {aspect}

        Requirements:
        - Write exactly 2 academic paragraphs.
        - Separate the paragraphs with one blank line.
        - Total length MUST NOT exceed 250 words.
        - Each paragraph must be 80-100 words only.
        - Maximum 2 paragraphs.
        - Do NOT repeat the section title.
        - Start directly with the paragraph.
        - Do NOT write a heading.
        - Do not repeat ideas.

        FORMAT:

        TEXT:
        paragraph paragraph
    """

        try:

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=220
            )

            text = response.choices[0].message.content.strip()

            # ---------- CONTENT EXTRACTION ----------

            if "TEXT:" in text.upper():

                idx = text.upper().find("TEXT:")

                content = text[idx + 5:].strip()

            else:

                content = text.strip()

            content = content.replace("TEXT:", "").strip()

            print("CONTENT LENGTH:", len(content))
            print(content[:200])

            # ---------- FALLBACK CONTENT ----------

            if len(content.split()) < 50:

                content = f"""
                    {aspect} is an important dimension of {topic}. Understanding this aspect helps researchers and policymakers analyse how environmental, technological, and socio-economic systems interact. Studies highlight that examining this area provides valuable insight into long-term sustainability and global development challenges.

                    Furthermore, analysing {aspect.lower()} allows decision-makers to develop more effective strategies and policies. Through research, data analysis, and global cooperation, societies can address emerging risks and design solutions that improve resilience and promote sustainable development.
                """
            # ---------- PRESERVE PARAGRAPHS ----------

            paragraphs = []

            for para in content.split("\n\n"):

                para = para.strip()

                if para:
                    paragraphs.append(para)

            content = "\n\n".join(paragraphs)

            # ---------- CHART ----------
            chart_data = None

            forced_chart = None

            generate_chart = False

            pages_since_chart += 1

            if pages_since_chart >= 2:

                probability = min(
                    0.15 * pages_since_chart,
                    0.60
                )

                if random.random() < probability:

                    generate_chart = True
                    pages_since_chart = 0

                    forced_chart = random.choice([
                        "bar",
                        "line",
                        "pie"
                    ])

            if generate_chart:

                chart_prompt = f"""
                    Generate chart data from this section.

                    SECTION TITLE:
                    {aspect}

                    SECTION CONTENT:
                    {content[:400]}

                    Rules:
                    - Labels must come from the content.
                    - Do not invent unrelated categories.
                    - Use exactly 4 labels.
                    - Values must be realistic.

                    FORMAT:

                    LABELS:item1,item2,item3,item4
                    VALUES:number,number,number,number
                """

                chart_response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": chart_prompt}],
                    temperature=0.4,
                    max_tokens=150
                )

                chart_text = chart_response.choices[0].message.content.strip()

                labels = []
                values = []
                chart_type = forced_chart if forced_chart else "bar"

                for line in chart_text.split("\n"):

                    line_upper = line.upper()

                    if line_upper.startswith("LABELS"):
                        labels = line.split(":")[1].split(",")

                    elif line_upper.startswith("VALUES"):

                        raw_vals = line.split(":")[1].split(",")

                        values = [
                            abs(float(v.replace("%", "").strip()))
                            for v in raw_vals if v.strip()
                        ]

                if len(labels) == len(values) and len(labels) >= 3:

                    chart_data = {
                        "labels": labels,
                        "values": values,
                        "type": chart_type,
                        "title": aspect + " Analysis"
                    }

                else:

                    chart_data = {
                        "labels": ["Category A", "Category B", "Category C", "Category D"],
                        "values": [25, 35, 20, 20],
                        "type": chart_type,
                        "title": aspect + " Analysis"
                    }

            # ---------- IMAGE ONLY IF NO CHART ----------

            image_url = None

            if chart_data is None:

                image_query = f"{aspect} {topic}"

                image_url = get_image_url(image_query)

            slides.append({
                "title": f"{aspect}",
                "content": content.strip(),
                "image_url": image_url,
                "chart_data": chart_data
            })

        except Exception as e:
            print("AI Error:", e)

    while len(slides) < sections:

        idx = len(slides) + 1

        slides.append({
            "title": f"Additional Analysis {idx}",
            "content": f"""
This section provides additional discussion related to {topic}. The topic is examined from multiple perspectives to ensure comprehensive academic coverage.
""",
            "image_url": get_image_url(topic),
            "chart_data": None
        })

    slides = slides[:sections]

    print(
        f"Final Slides Generated: {len(slides)}"
    )

    return slides
