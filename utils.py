import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib import colors

# GEMINI CONFIG
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


# PDF SNAPSHOT
# Fetches job page text and renders it as a clean PDF
def generate_pdf_snapshot(job_url, output_file):
    try:
        # Fetch the page
        response = requests.get(
            job_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=20
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Pull page title
        title = soup.title.string.strip() if soup.title else job_url

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        # Get clean text
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        clean_text = "\n".join(lines)

        # Build PDF with reportlab
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=6
        )

        url_style = ParagraphStyle(
            "URL",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#0066cc"),
            spaceAfter=12
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#222222")
        )

        story = []
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(job_url, url_style))
        story.append(Spacer(1, 4*mm))

        # Split into chunks to avoid overflow
        chunk_size = 1500
        for i in range(0, min(len(clean_text), 15000), chunk_size):
            chunk = clean_text[i:i+chunk_size]
            chunk = chunk.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(chunk, body_style))
            story.append(Spacer(1, 3*mm))

        doc.build(story)
        return True

    except Exception as e:
        st.warning(f"⚠️ Snapshot error: {e}")
        return False


# SCRAPE JOB PAGE
def scrape_job_link(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n")
    except Exception as e:
        return f"Scrape error: {e}"


# EXTRACT RESUME TEXT
def extract_text_from_upload(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text()
    elif uploaded_file.name.endswith(".docx"):
        document = docx.Document(uploaded_file)
        for para in document.paragraphs:
            text += para.text + "\n"
    return text


# CLEAN DESCRIPTION
def clean_description_with_ai(raw_text):
    try:
        prompt = f"""
Organize this job posting.

Create sections:

Responsibilities

Requirements

Preferred Skills

Benefits

Job Text:

{raw_text}
"""
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Formatting error: {e}"


# RESUME MATCH
def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"""
Compare resume against job.

Return EXACTLY:

Rating: X/10

Strengths:
- item

Missing Skills:
- item

Suggestions:
- item

Resume:

{resume_text}

Job:

{job_desc}
"""
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        result = response.text

        rating = "N/A"
        match = re.search(r"(\d+)\s*/\s*10", result)
        if match:
            rating = match.group(1) + "/10"

        feedback = [line.strip() for line in result.split("\n") if line.strip()]

        return {"score": rating, "feedback": feedback}

    except Exception as e:
        return {"score": "Error", "feedback": [f"Technical error: {e}"]}
