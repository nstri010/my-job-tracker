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
genai.configure(
    api_key=st.secrets["GOOGLE_API_KEY"]
)

# PDF SNAPSHOT
# Creates REAL webpage screenshot then converts to PDF
def generate_pdf_snapshot(job_url, output_file):
    try:
        screenshot_file = "job_snapshot.png"
        
        with sync_playwright() as p:
            # Added no-sandbox for container compatibility
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            
            # Use a standard Desktop User Agent to ensure the full site renders, not a mobile version
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 2500}
            )
            
            page = context.new_page()
            
            # Wait until the network is idle so all images and styles load
            page.goto(job_url, wait_until="networkidle", timeout=60000)
            
            # Extra time for any lazy-loaded elements or animations
            time.sleep(5)

            # Advanced cleanup: Remove popups, cookie banners, and overlays that block the screenshot
            page.evaluate("""
                () => {
                    const selectors = [
                        '[role="dialog"]', '.popup', '.modal', '.cookie-banner', 
                        '#onetrust-banner-sdk', '.privacy-policy', '.sign-up-modal'
                    ];
                    selectors.forEach(s => {
                        document.querySelectorAll(s).forEach(el => el.remove());
                    });
                    // Re-enable scrolling if a modal disabled it
                    document.body.style.overflow = 'visible';
                }
            """)

            # Take the full-page screenshot
            page.screenshot(path=screenshot_file, full_page=True)
            browser.close()

        # Convert the high-res image to a PDF
        img = Image.open(screenshot_file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        img.save(output_file, "PDF", resolution=100.0)
        
        # Clean up temporary image file
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            
        return True

    except Exception as e:
        st.error(f"Snapshot capture failed: {e}")
        return False

# SCRAPE JOB PAGE
def scrape_job_link(url):
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text
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
        prompt = f"Organize this job posting. Create sections: Responsibilities, Requirements, Preferred Skills, Benefits.\n\nJob Text:\n{raw_text}"
        model = genai.GenerativeModel("gemini-1.5-flash") # Updated to existing model name
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Formatting error: {e}"

# RESUME MATCH
def get_ai_match_feedback(job_desc, resume_text):
    try:
        prompt = f"""Compare resume against job. Return EXACTLY:
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
{job_desc}"""
        model = genai.GenerativeModel("gemini-1.5-flash")
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
