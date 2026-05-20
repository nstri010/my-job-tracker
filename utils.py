import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json
import asyncio
import subprocess
import sys
import os
from playwright.async_api import async_playwright

# --- OPTIMIZED STARTUP SCRIPT ---
@st.cache_resource
def try_install_playwright():
    """Runs once per session to ensure browser exists without crashing."""
    try:
        # Check if already installed
        subprocess.run(["playwright", "--version"], capture_output=True, check=True)
    except:
        # Install only if missing
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        subprocess.run([sys.executable, "-m", "playwright", "install-deps"])

try_install_playwright()

# AI Setup
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_upload(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['docx', 'doc']:
            return docx2txt.process(io.BytesIO(uploaded_file.getvalue()))
    except: return ""
    return ""

def scrape_job_link(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for junk in soup(["script", "style", "nav", "footer", "header"]):
            junk.decompose()
        return soup.get_text(separator='\n\n', strip=True)
    except Exception as e:
        return f"Scraper Error: {e}"

def clean_description_with_ai(raw_text):
    prompt = f"Format this into a clean job listing with bold headers and bullets. Keep all details:\n\n{raw_text[:5000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"Compare this Job and Resume. Return ONLY JSON: {{\"score\": \"X/10\", \"feedback\": [\"point 1\", \"point 2\", \"point 3\"]}}\n\nJOB: {job_desc[:2000]}\nRESUME: {resume_text[:2000]}"
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip('`json \n'))
    except: return {"score": "N/A", "feedback": ["Could not generate feedback"]}

async def run_snapshot(url, filename):
    async with async_playwright() as p:
        # Launch with additional flags for low-memory environments
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        try:
            # Increase timeout to 60s for slow sites
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(2) # Give it a moment to settle
            await page.pdf(path=filename, format="A4")
            return True
        except Exception as e:
            st.error(f"Snapshot Failed: {e}")
            return False
        finally:
            await browser.close()

def generate_pdf_snapshot(url, filename):
    """Wrapper to run the async function correctly."""
    return asyncio.run(run_snapshot(url, filename))
