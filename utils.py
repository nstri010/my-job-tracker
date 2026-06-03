import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
from bs4 import BeautifulSoup
import img2pdf
import os

# ── Gemini setup ──────────────────────────────────────────────────
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


def _call_gemini(prompt, temperature=None, max_retries=4):
    """Call Gemini with automatic retry on rate-limit (429) errors."""
    model = genai.GenerativeModel("gemini-2.0-flash-001")
    for attempt in range(max_retries):
        try:
            kwargs = {}
            if temperature is not None:
                kwargs["generation_config"] = genai.GenerationConfig(temperature=temperature)
            return model.generate_content(prompt, **kwargs).text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                wait = 30 * (attempt + 1)
                try:
                    m = re.search(r'retry in (\d+)', msg, re.IGNORECASE)
                    if m:
                        wait = int(m.group(1)) + 2
                except Exception:
                    pass
                if attempt < max_retries - 1:
                    time.sleep(wait)
                else:
                    raise
            else:
                raise
    return ""


# ── PDF Snapshot ──────────────────────────────────────────────────
def generate_pdf_snapshot(job_url, output_file):
    try:
        api_key = st.secrets["APIFLASH_KEY"]
        params = {
            "access_key": api_key,
            "url": job_url,
            "format": "jpeg",
            "quality": 85,
            "width": 1440,
            "full_page": "true",
            "no_cookie_banners": "true",
            "no_ads": "true",
            "delay": 2,
        }
        response = requests.get(
            "https://api.apiflash.com/v1/urltoimage",
            params=params,
            timeout=60
        )
        if response.status_code != 200:
            st.warning(f"Screenshot API error: {response.status_code} — {response.text[:200]}")
            return False
        tmp_jpg = output_file.replace(".pdf", "_tmp.jpg")
        with open(tmp_jpg, "wb") as f:
            f.write(response.content)
        with open(output_file, "wb") as f:
            f.write(img2pdf.convert(tmp_jpg))
        os.remove(tmp_jpg)
        return True
    except Exception as e:
        st.warning(f"Snapshot error: {e}")
        return False


# ── Scrape Job Page ───────────────────────────────────────────────
def scrape_job_link(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n")
    except Exception as e:
        return f"Scrape error: {e}"


# ── Extract Resume Text ───────────────────────────────────────────
def extract_text_from_upload(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith(".pdf"):
            pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in pdf:
                text += page.get_text()
        elif uploaded_file.name.endswith(".docx"):
            document = docx.Document(uploaded_file)
            for para in document.paragraphs:
                text += para.text + "\n"
        else:
            text = uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.warning(f"Could not read file: {e}")
    return text


# ── Clean Job Description ─────────────────────────────────────────
def clean_description_with_ai(raw_text):
    try:
        prompt = f"""Organize this job posting into these sections:

Responsibilities
Requirements
Preferred Skills
Benefits

Job Text:
{raw_text}"""
        return _call_gemini(prompt)
    except Exception as e:
        return f"Formatting error: {e}"


# ── Resume Match Feedback ─────────────────────────────────────────
def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"""You are a resume evaluator. Compare the resume against the job description.

Your response MUST start with this exact line:
SCORE: X/10

Where X is a whole number from 1 to 10. Then provide:

Strengths:
- item

Missing Skills:
- item

Suggestions:
- item

Resume:
{resume_text}

Job Description:
{job_desc}"""
        result = _call_gemini(prompt, temperature=0)

        rating = "N/A"
        match = re.search(r"SCORE:\s*(\d+)\s*/\s*10", result, re.IGNORECASE)
        if match:
            rating = match.group(1) + "/10"
        else:
            match = re.search(r"(\d+)\s*/\s*10", result)
            if match:
                rating = match.group(1) + "/10"

        feedback = [line.strip() for line in result.split("\n") if line.strip()]
        return {"score": rating, "feedback": feedback}

    except Exception as e:
        return {"score": "Error", "feedback": [f"Technical error: {e}"]}
