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
from playwright.async_api import async_playwright

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
        for junk in soup(["script", "style"]):
            junk.decompose()
        return soup.get_text(separator=' ', strip=True)
    except: return ""

def clean_description_with_ai(raw_text):
    # Improved prompt to fix parsing/spacing issues
    prompt = (
        "Reformat the following raw job description text into a professional, "
        "well-structured format. Use clear bold headers for sections like 'Responsibilities' "
        "and 'Requirements'. Use standard bullet points. Ensure there is only a single "
        "empty line between sections and no extra indentation. "
        f"Text:\n\n{raw_text[:5000]}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"Compare this Job and Resume. Return ONLY JSON: {{\"score\": \"X/10\", \"feedback\": [\"point 1\", \"point 2\", \"point 3\"]}}\n\nJOB: {job_desc[:2000]}\nRESUME: {resume_text[:2000]}"
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip('`json \n'))
    except: return {"score": "N/A", "feedback": ["Could not generate feedback"]}

def generate_pdf_snapshot(url, filename):
    async def run():
        async with async_playwright() as p:
            try:
                # Add headless=True and args for better cloud rendering
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.pdf(path=filename, format="A4")
                await browser.close()
                return True
            except Exception as e:
                print(f"Snapshot Error: {e}")
                return False
    return asyncio.run(run())
