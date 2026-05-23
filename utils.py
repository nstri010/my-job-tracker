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
    st.error("Check your Google API Key in Streamlit Secrets.")

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
        for element in soup(["script", "style"]):
            element.decompose()
        # Using separator='\n' helps preserve structure during initial scrape
        return soup.get_text(separator='\n', strip=True)
    except Exception:
        return ""

def clean_description_with_ai(raw_text):
    # Added explicit instruction to keep newlines/spacing
    prompt = f"""
    Extract the job title, company name, and the core job description from the text below. 
    IMPORTANT: Maintain the original formatting, bullet points, and paragraph spacing of the job description. 
    Remove only the website navigation, headers, footers, and legal disclaimers.

    TEXT:
    {raw_text[:4000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return raw_text[:2000]

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"""
    Analyze the following Job and Resume. Provide a score out of 10 and 3 actionable suggestions.
    Return ONLY a raw JSON object. Do not include markdown code blocks like ```json.
    
    Format: {{"score": "X/10", "feedback": ["suggestion 1", "suggestion 2", "suggestion 3"]}}

    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        raw_content = response.text.strip()
        
        # Robust JSON extraction: finds the first { and the last }
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        return {"score": "N/A", "feedback": ["AI failed to format response correctly."]}
    except Exception as e:
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
                if 'browser' in locals():
                    await browser.close()
                return False
    try:
        return asyncio.run(run())
    except Exception:
        return False
