import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re

# Configure Gemini API
genai.configure(
    api_key=st.secrets["GOOGLE_API_KEY"]
)


# PDF / DOCX TEXT EXTRACTION
def extract_text_from_upload(uploaded_file):

    text = ""

    if uploaded_file.name.endswith(".pdf"):

        pdf = fitz.open(
            stream=uploaded_file.read(),
            filetype="pdf"
        )

        for page in pdf:
            text += page.get_text()

    elif uploaded_file.name.endswith(".docx"):

        document = docx.Document(
            uploaded_file
        )

        for para in document.paragraphs:
            text += para.text + "\n"

    return text


# AI JOB DESCRIPTION CLEANER
def clean_description_with_ai(raw_text):

    try:

        prompt = f"""
Clean and organize this job description.

Make sections:

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

        response = model.generate_content(
            prompt
        )

        return response.text

    except Exception as e:

        return f"AI formatting error: {e}"


# RESUME MATCH ANALYZER
def get_ai_match_feedback(
    job_desc,
    resume_text
):

    try:

        prompt = f"""
Compare this resume against the job description.

Return EXACTLY in this format:

Score: XX%

Strengths:
- item
- item
- item

Missing Skills:
- item
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

        response = model.generate_content(
            prompt
        )

        result = response.text

        score = "N/A"

        match = re.search(
            r'(\d+)%',
            result
        )

        if match:

            score = (
                match.group(1)
                + "%"
            )

        feedback = []

        lines = result.split(
            "\n"
        )

        for line in lines:

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
                f"Technical error: {str(e)}"
            ]
        }
