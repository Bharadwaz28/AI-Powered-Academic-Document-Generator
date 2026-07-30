# 🚀 AI Academic Document Generator

An AI-powered academic content generation platform that automatically creates professional PowerPoint presentations and PDF reports from a user-provided topic.

## 🌐 Live Demo

🔗 **Launch the App:** https://ai-powered-academic-document-generator.streamlit.app/

## Features

* AI-generated academic content using Groq LLaMA models
* Interactive Streamlit web interface
* Live PPT slide preview
* Live PDF report preview
* Automatic chart generation
* Dynamic image retrieval using Unsplash API
* Automatic table generation
* Professional PDF report generation
* Professional PowerPoint generation
* One-click download functionality
* Document validation before download

## Tech Stack

* Python
* Streamlit
* Groq API
* LLaMA Models
* ReportLab
* python-pptx
* Matplotlib
* Plotly
* Pandas
* Requests
* Unsplash API

## Installation

```bash
git clone <repository-url>

cd AI-Academic-Document-Generator

pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

## Run Application

```bash
streamlit run app.py
```

## Project Structure

```text
app.py

utils/
│
├── ai_generator_pdf.py
├── ai_generator_ppt.py
├── pdf_generator.py
├── ppt_generator.py
├── chart_generator_pdf.py
├── image_fetcher_pdf.py
├── image_fetcher_ppt.py

outputs/
```

## Supported Outputs

### PDF Reports

* Title Page
* Table of Contents
* Academic Sections
* Charts
* Images
* Page Numbers

### PowerPoint Presentations

* Multiple Slide Layouts
* Bullet Points
* Images
* Tables
* Charts

## Future Improvements

* DOCX Support
* Citation Generator
* Multi-language Generation
* Custom Themes
* Offline AI Models

## Authors

* G. Bharadwaz
