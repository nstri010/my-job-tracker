import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
from bs4 import BeautifulSoup
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

# GEMINI CONFIG
genai.configure(
    api_key=st.secrets["GOOGLE_API_KEY"]
)


# PDF SNAPSHOT GENERATOR
def generate_pdf_snapshot(
    company,
    position,
    description
):

    filename = (
        f"{company}_{position}.pdf"
        .replace(
            " ",
            "_"
        )
    )

    doc = SimpleDocTemplate(
        filename
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            f"<b>Company:</b> {company}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(
            1,
            12
        )
    )

    story.append(
        Paragraph(
            f"<b>Position:</b> {position}",
            styles["Normal"]
        )
    )

    story.append(
        Spacer(
            1,
            12
        )
    )

    story.append(
        Paragraph(
            description,
            styles["BodyText"]
        )
    )

    doc.build(
        story
    )

    return filename


# SCRAPE JOB PAGE
def scrape_job_link(
    url
):

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        return soup.get_text(
            separator="\n"
        )

    except Exception as e:

        return (
            f"Scrape error: {e}"
        )


# RESUME EXTRACT
def extract_text_from_upload(
    uploaded_file
):

    text = ""

    if uploaded_file.name.endswith(
        ".pdf"
    ):

        pdf = fitz.open(
            stream=uploaded_file.read(),
            filetype="pdf"
        )

        for page in pdf:

            text += page.get_text()

    elif uploaded_file.name.endswith(
        ".docx"
    ):

        document = docx.Document(
            uploaded_file
        )

        for para in document.paragraphs:

            text += (
                para.text
                + "\n"
            )

    return text


# DESCRIPTION CLEANER
def clean_description_with_ai(
    raw_text
):

    try:

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        prompt = f"""
Organize this job description.

Sections:

Responsibilities
Requirements
Preferred Skills
Benefits

{raw_text}
"""

        response = model.generate_content(
            prompt
        )

        return response.text

    except Exception as e:

        return str(e)


# MATCH SCORING
def get_ai_match_feedback(
    job_desc,
    resume_text
):

    try:

        prompt = f"""
Compare resume to job.

Return:

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

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = model.generate_content(
            prompt
        )

        result = response.text

        score = "N/A"

        match = re.search(
            r'(\d+)/10',
            result
        )

        if match:

            score = (
                match.group(1)
                + "/10"
            )

        feedback = []

        for line in result.split(
            "\n"
        ):

            line = line.strip()

            if line:

                feedback.append(
                    line
                )

        return {
            "score":
            score,

            "feedback":
            feedback
        }

    except Exception as e:

        return {
            "score":
            "Error",

            "feedback":
            [
                str(e)
            ]
        }
