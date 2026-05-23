import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from PIL import Image

# GEMINI CONFIG
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def generate_pdf_snapshot(job_url, output_file):
    try:
        screenshot_file = "job_snapshot.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 2200})
            page.goto(job_url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            # remove popups/modals
            page.evaluate("""() => {
                document.querySelectorAll('[role="dialog"], .popup, .modal').forEach(x => x.remove());
            }""")
            page.screenshot(path=screenshot_file, full_page=True)
            browser.close()

        img = Image.open(screenshot_file)
        img.convert("RGB").save(output_file)
        return True
    except Exception as e:
        print(f"Snapshot error: {e}")
        return False

def scrape_job_link(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n")
    except Exception as e:
        return f"Scrape error: {e}"

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

def clean_description_with_ai(raw_text):
    try:
        prompt = f"Organize this job posting.\n\nCreate sections:\nResponsibilities\nRequirements\nPreferred Skills\nBenefits\n\nJob Text:\n{raw_text}"
        model = genai.GenerativeModel("gemini-2.0-flash") # Updated to stable version
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Formatting error: {e}"

def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"""
        Compare resume against job.
        Return EXACTLY this format at the start:
        Rating: X/10
        
        Then provide:
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
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        result = response.text

        # IMPROVED REGEX: Matches "Rating: 6/10", "6 / 10", or just "6/10"
        rating = "N/A"
        match = re.search(r"(\d+)\s*/\s*10", result)
        if match:
            rating = f"{match.group(1)}/10"

        feedback_lines = [line.strip() for line in result.split("\n") if line.strip()]

        return {
            "score": rating,
            "feedback": feedback_lines
        }
    except Exception as e:
        return {
            "score": "Error",
            "feedback": [f"Technical error: {e}"]
        }
