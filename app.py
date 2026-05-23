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

# AI Setup - Using the stable model identifier
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest') # Changed to flash-latest for stability

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
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return f"Scraper Error: {e}"

def clean_description_with_ai(raw_text):
    prompt = f"Format this into a clean job listing with bold headers and bullets. Preserve the original spacing:\n\n{raw_text[:5000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"""
    Compare this Job and Resume. Return ONLY JSON.
    Format: {{"score": "X/10", "feedback": ["point 1", "point 2", "point 3"]}}
    
    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        raw_content = response.text.strip()
        
        # Extracts JSON even if the model adds conversational text
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {"score": "N/A", "feedback": ["Formatting error"]}
    except Exception as e:
        return {"score": "Error", "feedback": [f"Technical error: {str(e)}"]}

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
            except Exception as e:
                await browser.close()
                return False
    return asyncio.run(run())
