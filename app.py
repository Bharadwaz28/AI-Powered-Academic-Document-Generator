import streamlit as st
import pandas as pd
import plotly.express as px

from utils.pdf_generator import generate_pdf
from utils.ppt_generator import generate_ppt
from utils.ai_generator_ppt import generate_ai_content as generate_ppt_content
from utils.ai_generator_pdf import generate_ai_content as generate_pdf_content
from utils.image_fetcher_ppt import get_image_url

st.set_page_config(page_title="AI Academic Generator", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}
.header {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0px 6px 25px rgba(0,0,0,0.5);
}
.card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 15px;
    border: 1px solid rgba(255,255,255,0.05);
}
.stButton>button {
    border-radius: 12px;
    height: 3em;
    font-weight: 600;
    transition: 0.2s;
}
.stButton>button:hover {
    transform: scale(1.03);
}
.stDownloadButton>button {
    width: 100%;
    border-radius: 12px;
    height: 3em;
    font-weight: 600;
}
[data-testid="stSidebar"] {
    background: #020617;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div class="header">
    <h1>🚀 AI Academic Document Generator</h1>
    <p>Create <b>PPTs</b> & <b>PDF Reports</b> instantly using AI</p>
</div>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "slides" not in st.session_state:
    st.session_state.slides = []

if "show_preview" not in st.session_state:
    st.session_state.show_preview = False

if "generated" not in st.session_state:
    st.session_state.generated = False

if "current_slide" not in st.session_state:
    st.session_state.current_slide = 0

if "generated_type" not in st.session_state:
    st.session_state.generated_type = None

if "generated_topic" not in st.session_state:
    st.session_state.generated_topic = ""

if "generated_pages" not in st.session_state:
    st.session_state.generated_pages = None


def reset_preview():
    st.session_state.show_preview = False
    st.session_state.current_slide = 0


# ================= SIDEBAR =================
with st.sidebar:

    st.markdown("## ⚙️ Controls")

    generation_type = st.selectbox(
        "📄 Document Type",
        ["PPT Presentation", "PDF Report"],
        on_change=reset_preview
    )

    topic = st.text_input("" "🧠 Topic", on_change=reset_preview)

    pages = st.slider("📊 Sections", 3, 20, 8, on_change=reset_preview)

    st.markdown("---")

    generate = st.button(
        "🚀 Generate",
        use_container_width=True,
        on_click=reset_preview
    )

    st.markdown("---")

    st.toggle("👀 Preview", key="show_preview")

# ================= GENERATION =================
if generate:

    if topic.strip() == "":
        st.error("Please enter a topic")
        st.stop()

    with st.spinner("Generating content..."):
        try:
            if generation_type == "PPT Presentation":
                slides = generate_ppt_content(topic, pages)

            else:
                slides = generate_pdf_content(
                    topic,
                    pages,
                    "academic",
                    "pdf"
                )

            if not slides:
                st.error("Failed to generate content")
                st.stop()

            st.session_state.slides = slides
            st.session_state.generated = True
            st.session_state.generated_type = generation_type
            st.session_state.generated_topic = topic
            st.session_state.generated_pages = pages

        except Exception as e:
            st.error(f"Generation Error: {str(e)}")
            st.stop()

# ================= LOAD DATA =================
slides = st.session_state.slides

# ================= EMPTY STATE =================
if not slides:
    st.markdown("""
    <div class="card" style="text-align:center;">
        <h3>✨ Welcome</h3>
        <p>Use the sidebar to generate your document.</p>
    </div>
    """, unsafe_allow_html=True)

# ================= PREVIEW =================
if slides and st.session_state.get("show_preview", False):
    if st.session_state.generated_type != generation_type:

        st.warning(
            f"""
            ⚠️ This document was generated as
            '{st.session_state.generated_type}'.

            No {generation_type} preview is available.

            Please click Generate again to create
            a '{generation_type}' document.
            """
        )

    else:

        # ================= PPT MODE =================
        if generation_type == "PPT Presentation":

            st.markdown("## 🎞 PPT Preview")
            total_slides = len(slides)

            nav1, nav2, nav3 = st.columns(
                [1, 6, 1], vertical_alignment="center")

            with nav1:
                if st.button("⬅️", use_container_width=True):
                    if st.session_state.current_slide > 0:
                        st.session_state.current_slide -= 1
                        st.rerun()

            with nav2:
                st.markdown(
                    f"<div style='text-align:center; font-weight:600;'>"
                    f"Slide {st.session_state.current_slide+1} / {total_slides}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            with nav3:
                if st.button("➡️", use_container_width=True):
                    if st.session_state.current_slide < total_slides - 1:
                        st.session_state.current_slide += 1
                        st.rerun()

            i = st.session_state.current_slide + 1
            slide = slides[st.session_state.current_slide]

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <div style="font-size:20px;font-weight:600;">🟦 Slide {i}</div>
            <div style="font-size:22px;font-weight:600;text-align:center;flex:1;">
            {slide.get('title', '')}
            </div>
            <div style="width:60px;"></div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1], gap="medium")

            # LEFT SIDE
            with col1:
                if slide.get("bullets"):
                    for bullet in slide["bullets"]:
                        st.markdown(f"• {bullet}")

            # RIGHT SIDE
            with col2:
                image_url = slide.get("image_url")

                if (
                    image_url
                    and isinstance(image_url, str)
                    and image_url.startswith("http")
                ):

                    st.markdown(f"""
                        <div style="
                            display:flex;
                            justify-content:center;
                            align-items:flex-start;
                            margin-top:0px;
                            padding-top:0px;
                        ">
                        <img src="{image_url}"
                            style="
                            max-height:340px;
                            height:240px;
                            width:auto;
                            border-radius:10px;
                            object-fit:cover;
                        ">
                        </div>
                    """,
                                unsafe_allow_html=True)

                else:
                    st.warning("Image not available")

            st.markdown("<br>", unsafe_allow_html=True)

            chart = slide.get("chart_data")

            table_data = slide.get("table_data")

            if chart and chart.get("labels") and chart.get("values"):

                st.markdown(
                    f"""
                    <h3 style='text-align:center;'>
                    📊 {chart.get('chart_title', slide.get('title'))}
                    </h3>
                    """,
                    unsafe_allow_html=True
                )

                chart_left, chart_center, chart_right = st.columns([1, 3, 1])

                with chart_center:

                    try:

                        df = pd.DataFrame({
                            "X": chart["labels"],
                            "Y": chart["values"]
                        })

                        chart_type = chart.get("type", "bar")
                        if chart_type == "line":

                            st.line_chart(
                                df,
                                x="X",
                                y="Y",
                                height=300
                            )

                        elif chart_type == "pie":
                            pie_df = pd.DataFrame({
                                "Category": chart["labels"],
                                "Value": chart["values"]
                            })

                            fig = px.pie(
                                pie_df,
                                names="Category",
                                values="Value"
                            )

                            fig.update_layout(
                                height=300,
                                margin=dict(
                                    l=10,
                                    r=10,
                                    t=10,
                                    b=10
                                ),
                                showlegend=True
                            )

                            st.plotly_chart(
                                fig,
                                use_container_width=True
                            )

                        else:

                            st.bar_chart(
                                df,
                                x="X",
                                y="Y",
                                height=300
                            )

                    except Exception:
                        st.warning("Chart rendering failed")

            if table_data:
                st.markdown(
                    f"""
                    <h3 style='text-align:center;'>
                    📋 {table_data.get('table_title', slide.get('title'))}
                    </h3>
                    """,
                    unsafe_allow_html=True
                )

                try:

                    headers = table_data.get("headers", [])
                    rows = table_data.get("rows", [])

                    if headers and rows:

                        df = pd.DataFrame(
                            rows,
                            columns=headers
                        )

                        table_left, table_center, table_right = st.columns([
                            1, 3, 1])

                        with table_center:
                            st.table(df)

                except Exception:
                    st.warning("Table rendering failed")

        # ================= PDF MODE ================
        else:

            st.markdown("## 📄 PDF Preview")

            for i, slide in enumerate(slides):

                with st.container():

                    st.markdown(f"## {i+1}. {slide.get('title', '')}")

                    # ---------------- CONTENT ----------------

                    content = slide.get("content", "").strip()

                    st.markdown(
                        f"""
                    <div style="
                    font-size:18px;
                    line-height:1.8;
                    text-align:justify;
                    ">
                    {content}
                    </div>
                    """,
                        unsafe_allow_html=True
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ---------------- VISUAL ----------------

                    chart = slide.get("chart_data")

                    left, center, right = st.columns([1.5, 3, 1.5])

                    with center:

                        if chart and chart.get("labels") and chart.get("values"):

                            try:

                                labels = chart["labels"]
                                values = chart["values"]

                                chart_type = chart.get("type", "bar").lower()

                                df = pd.DataFrame({
                                    "Category": labels,
                                    "Value": values
                                })

                                if chart_type == "line":

                                    fig = px.line(
                                        df,
                                        x="Category",
                                        y="Value"
                                    )

                                    fig.update_layout(
                                        height=350,
                                        margin=dict(l=20, r=20, t=20, b=20)
                                    )

                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True
                                    )

                                elif chart_type == "pie":

                                    fig = px.pie(
                                        df,
                                        names="Category",
                                        values="Value"
                                    )

                                    fig.update_layout(
                                        height=350,
                                        margin=dict(l=20, r=20, t=20, b=20)
                                    )

                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True
                                    )

                                else:

                                    fig = px.bar(
                                        df,
                                        x="Category",
                                        y="Value"
                                    )

                                    fig.update_layout(
                                        height=350,
                                        margin=dict(l=20, r=20, t=20, b=20)
                                    )

                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True
                                    )

                            except Exception:
                                st.warning("Chart rendering failed")

                        else:

                            image_url = slide.get("image_url")

                            if (
                                image_url
                                and isinstance(image_url, str)
                                and image_url.startswith("http")
                            ):

                                st.image(
                                    image_url,
                                    width=550
                                )

                            else:
                                st.info("No image available")

                st.divider()

        st.markdown("<br>", unsafe_allow_html=True)
# ================= DOWNLOAD =================

if slides and st.session_state.generated:

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⬇️ Download")

    # ----------------------------------------
    # Wrong document type selected
    # ----------------------------------------

    if st.session_state.generated_type != generation_type:

        st.warning(
            f"""
            ⚠️ This document was generated as
            '{st.session_state.generated_type}'.

            Please click Generate again to create
            a '{generation_type}' document.
            """
        )

    # ----------------------------------------
    # Topic changed after generation
    # ----------------------------------------

    elif (
        st.session_state.generated_topic != topic
        or st.session_state.generated_pages != pages
    ):

        st.warning(
            """
            ⚠️ Topic or section count has been modified.

            Please regenerate the document before downloading.
            """
        )

    # ----------------------------------------
    # Correct download
    # ----------------------------------------

    else:

        st.success(
            "Document generated successfully. Enable Preview to view it."
        )

        try:

            if st.session_state.generated_type == "PPT Presentation":

                file_path = generate_ppt(slides)

                with open(file_path, "rb") as f:

                    st.download_button(
                        "📊 Download PPT",
                        f,
                        file_name=f"{topic}.pptx"
                    )

            else:

                file_path = generate_pdf(
                    slides,
                    topic
                )

                with open(file_path, "rb") as f:

                    st.download_button(
                        "📄 Download PDF",
                        f,
                        file_name=f"{topic} report.pdf"
                    )

        except Exception as e:

            st.error(
                f"Download Error: {str(e)}"
            )
