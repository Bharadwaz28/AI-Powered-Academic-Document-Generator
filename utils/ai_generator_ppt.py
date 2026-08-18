import os
import json
import requests
from groq import Groq
from dotenv import load_dotenv
from utils.image_fetcher_ppt import get_guaranteed_image


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_ai_content(topic, number):

    prompt = f"""
        You are a JSON generator.

        Generate {number} slides for a presentation on "{topic}".

        Return ONLY valid JSON.

        Format:
        [
        {{
            "title": "Slide title",

            "bullets": [
                "Point 1",
                "Point 2",
                "Point 3"
            ],

            "image_query": "1-3 keyword search phrase",

            
            "table_data": {{
                "table_title": "",
                "headers": ["Column1", "Column2"],
                "rows": [
                    ["Value1", "Value2"],
                    ["Value3", "Value4"]
                ]
            }}

            "chart_data": {{
                "chart_title": "",
                "metric": "",
                "type": "bar/line/pie",
                "labels": ["A", "B", "C"],
                "values": [10, 20, 30],
                "x_label": "X axis name",
                "y_label": "Y axis name"
            }}
        }}
        ]

        STRICT RULES:

        - Output must be valid JSON.
        - All keys must always exist.
        - Use double quotes only.
        - Add commas correctly.
        - Each bullet should be concise but meaningful.
        - bullets must be a list of plain strings (no numbering, no symbols).
        - Each slide must contain 4 to 6 bullets.
        - Each bullet should start with a key concept, feature, process, tool, technology, or subtopic.
        - After introducing the concept, provide a brief explanation in the same bullet.
        - Each bullet should be 12 to 25 words long.
        - Bullets should be informative enough that a reader can understand the slide without additional explanation.
        - Avoid single-word bullets.
        - Avoid short phrases that only act as headings.
        GOOD EXAMPLE:
        - Network Scanning identifies active hosts, open ports, and services running across a target network.
        - Vulnerability Assessment helps discover security weaknesses before attackers can exploit them.
        BAD EXAMPLE:
        - Network Scanning
        - Vulnerability Assessment
        - image_query must be relevant to the title of that slide and match the slide content.
        - Do NOT repeat the same image_query for all slides.
        - table_data must be structured properly.
        - labels and values must have EXACT same length.
        - Do NOT include anything outside JSON.
        - If a table is not useful, return null for table_data.
        - If a chart is not useful, return null for chart_data.
        - image_query should be a natural image search phrase containing 3-6 keywords describing the visual content of the slide.
        Examples:
        "ethical hacking tools dashboard"
        "network penetration testing lab"
        "cybersecurity operations center"
        "machine learning workflow diagram"
        - Every generated table must contain table_title.
        GOOD table_title examples:
        "Comparison of Ethical Hacking Tools"
        "Ethical Hacking Career Roles and Salaries"
        "Machine Learning Algorithm Comparison"
        "Cloud Service Provider Features"
        BAD table_title examples:
        "Table"
        "Data Table"
        "Comparison"
        "Information"

        CHART GENERATION RULES:

        - Generate chart_data ONLY when the slide naturally contains:
            - comparisons
            - rankings
            - trends
            - percentages
            - statistics
            - growth
            - distributions

        - If the slide is introductory, conceptual, descriptive, explanatory, historical, or informational without measurable comparison, return null for chart_data.

        - chart_data must be derived directly from the slide bullets.

        - Labels must come from:
            - tools
            - technologies
            - methods
            - categories
            - years
            - roles
            - stages
            - concepts
            - entities

        explicitly mentioned in the slide bullets.

        - Do NOT invent unrelated categories.

        - Do NOT use generic labels:
            A, B, C, D
            Item 1, Item 2
            Category 1, Category 2

        - Labels should be short and presentation friendly (1-4 words).

        METRIC RULES:

        - Every chart must contain a metric field.
        - metric describes what the chart values represent.

        GOOD metric examples:

        - Popularity Score
        - Adoption Rate (%)
        - Market Share (%)
        - Average Salary (USD)
        - Incident Frequency
        - Accuracy (%)
        - Revenue
        - Growth Rate (%)
        - Usage Score

        BAD metric examples:

        - Data
        - Value
        - Number
        - Metric

        - metric must be directly related to the slide content.

        VALUES RULES:

        - Values must represent realistic:
            - popularity
            - adoption
            - usage
            - impact
            - importance
            - effectiveness
            - contribution
            - frequency
            - percentage
            - growth

        - Values should logically match the slide content.

        CHART TITLE RULES:

        - Every chart must contain chart_title.

        GOOD chart_title examples:

        - Popularity of Ethical Hacking Tools
        - Salary Growth Across Job Levels
        - Distribution of Security Threat Types
        - Cyberattack Trends by Year
        - Comparison of Machine Learning Algorithms
        - Cloud Service Adoption Rates

        BAD chart_title examples:

        - Chart
        - Graph
        - Data
        - Visualization
        - Slide Chart

        CHART TYPE SELECTION:

        BAR CHART:

        Use for:
        - tool comparison
        - technology comparison
        - framework comparison
        - feature comparison
        - category ranking
        - importance ranking

        Examples:
        - Tool Popularity
        - Algorithm Accuracy
        - Technology Adoption
        - Feature Importance

        LINE CHART:

        Use for:
        - growth
        - progression
        - timeline
        - evolution
        - yearly trends
        - career progression
        - historical developments

        Examples:
        - Revenue Growth
        - Salary Progression
        - User Growth
        - Cyberattacks by Year

        PIE CHART:

        Use ONLY for:
        - percentage distributions
        - market share
        - resource allocation
        - contribution percentages
        - composition breakdowns

        Examples:
        - Market Share
        - Threat Distribution
        - Budget Allocation
        - Resource Allocation

        PIE CHART RULES:

        - Values MUST sum exactly to 100.
        - At least 3 categories must exist.
        - Do NOT generate equal percentages unless the content clearly implies equal distribution.

        BAR CHART RULES:

        - Values must be between 10 and 100.
        - Values should represent relative comparison.
        - Avoid identical values.

        LINE CHART RULES:

        - Values should show a logical trend.
        - Use ordered labels whenever possible.
        - Avoid random fluctuations.

        AXIS RULES:

        - x_label and y_label must always be meaningful.
        - y_label should normally match metric.
        - x_label and y_label must match the meaning of labels and values.

        GOOD EXAMPLES:

        {{
            "chart_title": "Popularity of Ethical Hacking Tools",
            "metric": "Popularity Score",
            "type": "bar",
            "labels": ["Nmap", "Metasploit", "Burp Suite"],
            "values": [82, 74, 91],
            "x_label": "Tool",
            "y_label": "Popularity Score"
        }}

        {{
            "chart_title": "Salary Growth Across Career Levels",
            "metric": "Average Salary (USD)",
            "type": "line",
            "labels": ["Junior", "Mid-Level", "Senior", "Lead"],
            "values": [45000, 65000, 90000, 120000],
            "x_label": "Career Level",
            "y_label": "Average Salary (USD)"
        }}

        {{
            "chart_title": "Distribution of Security Threat Types",
            "metric": "Percentage",
            "type": "pie",
            "labels": ["Phishing", "Malware", "DDoS", "Ransomware"],
            "values": [35, 30, 20, 15],
            "x_label": "Threat Type",
            "y_label": "Percentage"
        }}

        QUALITY RULES:

        - Avoid random numbers.
        - Avoid identical values.
        - Avoid perfectly uniform pie charts.
        - Ensure the chart communicates a meaningful insight.
        - Ensure the chart adds value to the slide.
        - If a meaningful chart cannot be created, return null for chart_data.
        - Generate chart_data for at most 30-40% of slides.
        - Only generate charts when they genuinely improve understanding.

        TABLE RULES:

        - Generate table_data only when tabular comparison improves understanding.
        - Tables should contain factual comparisons, metrics, timelines, features, specifications, classifications, or rankings.
        - Headers must be meaningful.
        - Every row must contain the same number of columns as the headers.
        - Avoid unnecessary tables.
        GOOD TABLE EXAMPLE:

        "table_title": "Comparison of Ethical Hacking Tools",
            "headers": ["Tool", "Purpose"],
            "rows": [
                ["Nmap", "Network Scanning"],
                ["Metasploit", "Penetration Testing"],
                ["Burp Suite", "Web Security Testing"]
            ]
        

        CONTENT QUALITY RULES:

        - Each slide should cover a unique aspect of the topic.
        - Avoid repeating the same information across slides.
        - Generate presentation-quality content suitable for academic, technical, or professional audiences.
        - Ensure bullets, images, charts, and tables align with the slide title.
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.9,
            max_tokens=5000
        )

        content = response.choices[0].message.content

        content = content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        slides = json.loads(content)

        for slide in slides:

            chart = slide.get("chart_data")

            if chart:
                labels = chart.get("labels", [])
                values = chart.get("values", [])

                if (
                    len(labels) != len(values)
                    or len(labels) == 0
                    or len(values) == 0
                    or not chart.get("chart_title")
                    or not chart.get("metric")
                ):
                    slide["chart_data"] = None

            table = slide.get("table_data")

            if table:

                headers = table.get("headers", [])
                rows = table.get("rows", [])

                valid = (
                    table.get("table_title")
                    and len(headers) > 0
                    and len(rows) > 0
                )

                if not valid:
                    slide["table_data"] = None

    except Exception as e:
        print("AI Error:", e)
        raise

    for idx, slide in enumerate(slides):

        query = slide.get("image_query", "")

        if query:
            query = f"{topic} {query}"
        else:
            query = topic

        layout_type = idx % 3

        if layout_type == 0:
            slide["image_url"] = get_guaranteed_image(
                query,
                topic,
                orientation="portrait"
            )

        else:
            slide["image_url"] = get_guaranteed_image(
                query,
                topic,
                orientation="landscape"
            )

    return slides
