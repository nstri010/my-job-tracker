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
    """Generates a high-quality PDF of the job posting using Playwright's native PDF engine."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Set a standard desktop viewport
            context = browser.new_context(viewport={"width": 1280, "height": 1000})
            page = context.new_page()
            
            # Navigate and wait for the page to finish loading styles/images
            page.goto(job_url, wait_until="networkidle", timeout=60000)
            
            # Brief pause for any lazy-loaded elements
            time.sleep(2)

            # Optional: Remove common popups that might block the job details
            page.evaluate("""
                () => {
                    const selectors = ['[role="dialog"]', '.popup', '.modal', '#cookie-banner'];
                    selectors.forEach(s => {
                        document.querySelectorAll(s).forEach(el => el.remove());
                    });
                }
            """)

            # Generate the PDF directly from the page
            page.pdf(
                path=output_file,
                format="A4",
                print_background=True,
                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
            )
            browser.close()
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
        prompt = f"Organize this job posting into sections (Responsibilities, Requirements, Skills, Benefits):\n\n{raw_text}"
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Formatting error: {e}"

def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"Compare resume against job. Return Rating: X/10, Strengths, Missing Skills, and Suggestions.\n\nResume:\n{resume_text}\n\nJob:\n{job_desc}"
        model = genai.GenerativeModel("gemini-2.0-flash")
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
