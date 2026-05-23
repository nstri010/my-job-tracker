import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
from bs4 import BeautifulSoup

# GEMINI CONFIG
genai.configure(
    api_key=st.secrets["GOOGLE_API_KEY"]
)


# SCRAPE JOB PAGE
def scrape_job_link(url):

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

        text = soup.get_text(
            separator="\n"
        )

        return text

    except Exception as e:

        return (
            f"Scrape error: {e}"
        )


# PDF / DOCX EXTRACTION
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


# CLEAN DESCRIPTION
def clean_description_with_ai(
    raw_text
):

    try:

        prompt = f"""
Clean and organize this job description.

Create:

Responsibilities
Requirements
Preferred Skills
Benefits

Text:

{raw_text}
"""

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = (
            model.generate_content(
                prompt
            )
        )

        return response.text

    except Exception as e:

        return (
            f"AI formatting error: {e}"
        )


# RESUME SCORING
def get_ai_match_feedback(
    job_desc,
    resume_text
):

    try:

        prompt = f"""
Compare resume vs job.

Return:

Score: XX%

Strengths:
- item
- item

Missing Skills:
- item
- item

Resume:

{resume_text}

Job Description:

{job_desc}
"""

        model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

        response = (
            model.generate_content(
                prompt
            )
        )

        result = response.text

        score = "N/A"

        match = re.search(
            r"(\\d+)%",
            result
        )

        if match:

            score = (
                match.group(1)
                + "%"
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
                f"Technical error: {e}"
            ]
        }
