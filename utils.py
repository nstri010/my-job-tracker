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
# This ensures the browser is installed only once when the app boots up
@st.cache_resource
def try_install_playwright():
    try:
        # Check if playwright is already functional
        subprocess.run(["playwright", "--version"], capture_output=True, check=True)
    except:
        # Install chromium and required linux system dependencies
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
        # Handle cases where AI might wrap JSON in markdown blocks
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {"score": "N/A", "feedback": ["Could not generate feedback"]}

async def run_snapshot(url, filename):
    """Internal async function to handle the browser logic."""
    async with async_playwright() as p:
        # Critical flags for running inside a container (Streamlit Cloud)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu"
