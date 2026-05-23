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
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.units import mm

# GEMINI CONFIG
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


# PDF SNAPSHOT
# Uses ApiFlash to take a real visual screenshot then saves as PDF
def generate_pdf_snapshot(job_url, output_file):
    try:
        api_key = st.secrets["APIFLASH_KEY"]
        st.info(f"🔑 Key loaded: {api_key[:6]}...")

        params = {
            "access_key": api_key,
            "url": job_url,
            "format": "jpeg",
            "quality": 85,
            "width": 1440,
            "height": 900,
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
            st.warning(f"⚠️ Screenshot API error: {response.status_code} — {response.text[:200]}")
            return False

        # Convert screenshot to PDF
        img = Image.open(BytesIO(response.content)).convert("RGB")

        a4_width_mm = 210
        a4_height_mm = 297
        a4_width_px = int(a4_width_mm * 3.7795)
        page_height_px = int(a4_height_mm * 3.7795)

        ratio = a4_width_px / img.width
        new_height = int(img.height * ratio)
        img = img.resize((a4_width_px, new_height), Image.LANCZOS)

        tmp_img = output_file.replace(".pdf", "_tmp.jpg")
        img.save(tmp_img, "JPEG", quality=85)

        num_pages = max(1, -(-new_height // page_height_px))

        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            leftMargin=0, rightMargin=0,
            topMargin=0, bottomMargin=0
        )

        story = []
        for i in range(num_pages):
            y_start = i * page_height_px
            y_end = min(y_start + page_height_px, new_height)
            crop = img.crop((0, y_start, a4_width_px, y_end))
            tmp_crop = output_file.replace(".pdf", f"_crop_{i}.jpg")
            crop.save(tmp_crop, "JPEG", quality=85)
            rl_img = RLImage(
                tmp_crop,
                width=a4_width_mm * mm,
                height=(y_end - y_start) * (a4_width_mm * mm / a4_width_px)
            )
            story.append(rl_img)

        doc.build(story)

        import os
        if os.path.exists(tmp_img):
            os.remove(tmp_img)
        for i in range(num_pages):
            tmp_crop = output_file.replace(".pdf", f"_crop_{i}.jpg")
            if os.path.exists(tmp_crop):
                os.remove(tmp_crop)

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
