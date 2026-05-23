import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json
import asyncio
import re
from playwright.async_api import async_playwright

# AI Setup
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.error("Missing Google API Key in Secrets.")

def extract_text_from_upload(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['docx', 'doc']:
            return docx2txt.process(io.BytesIO(uploaded_file.getvalue()))
    except Exception:
        return ""
    return ""

def scrape_job_link(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Clean up script and style elements
        for element in soup(["script", "style"]):
            element.decompose()
            
        return soup.get_text(separator=' ', strip=True)
    except Exception:
        return ""

def clean_description_with_ai(raw_text):
    prompt = f"Extract only the job title, company name, and core description. Remove legal jargon:\n\n{raw_text[:4000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return raw_text[:2000]

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"""
    Analyze the following Job and Resume. Provide a score out of 10 and 3 suggestions.
    Return ONLY JSON: {{"score": "X/10", "feedback": ["1", "2", "3"]}}
    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        raw_content = response.text.strip()
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {"score": "N/A", "feedback": ["AI formatting error"]}
    except Exception as e:
        # Fixed: Indented to match the 'try' block above
        return {"score": "Error", "feedback": [f"Connection error: {str(e)}"]}

def generate_pdf_snapshot(url, filename):
    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.pdf(path=filename, format="A4")
                await browser.close()
                return True
            except Exception:
                await browser.close()
                return False
    try:
        return asyncio.run(run())
    except Exception:
        return False
