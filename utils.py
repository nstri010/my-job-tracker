import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from PIL import Image

# GEMINI CONFIG
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def generate_pdf_snapshot(job_url, output_file):
    try:
        # 1. Capture the visual screenshot
        screenshot_file = "temp_render.png"
        
        with sync_playwright() as p:
            # Launch with specific flags for container stability
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            
            # Use a standard Desktop context so it doesn't look like a mobile site
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 3000}
            )
            
            page = context.new_page()
            
            # Wait for 'networkidle' ensures images and CSS are fully loaded
            page.goto(job_url, wait_until="networkidle", timeout=60000)
            
            # Give an extra 3 seconds for any JavaScript pop-ins
            time.sleep(3)

            # SCRIPT: Remove common banners/modals that might block the text
            page.evaluate("""
                () => {
                    const selectors = [
                        '[role="dialog"]', '.popup', '.modal', '.cookie-banner', 
                        '#onetrust-banner-sdk', '.privacy-policy', '.sign-up-modal'
                    ];
                    selectors.forEach(s => {
                        document.querySelectorAll(s).forEach(el => el.remove());
                    });
                    document.body.style.overflow = 'visible';
                }
            """)

            # Capture the FULL visual page as a PNG
            page.screenshot(path=screenshot_file, full_page=True)
            browser.close()

        # 2. Convert that PNG image into a PDF
        img = Image.open(screenshot_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # This saves the IMAGE as the PDF page, preserving exactly how it looks
        img.save(output_file, "PDF", resolution=100.0)
        
        # Clean up temp image
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            
        return True

    except Exception as e:
        st.error(f"Snapshot failed: {e}")
        return False

# Rest of your existing utils functions (scrape_job_link, extract_text_from_upload, etc.)
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
        prompt = f"Organize this job posting. Sections: Responsibilities, Requirements, Benefits.\n\nJob Text:\n{raw_text}"
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"Compare resume against job. Rating: X/10, Strengths, Missing Skills, Suggestions.\n\nResume:\n{resume_text}\n\nJob:\n{job_desc}"
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        result = response.text
        rating = "N/A"
        match = re.search(r"(\d+)\s*/\s*10", result)
        if match: rating = match.group(1) + "/10"
        return {"score": rating, "feedback": [line.strip() for line in result.split("\n") if line.strip()]}
    except Exception as e:
        return {"score": "Error", "feedback": [str(e)]}
