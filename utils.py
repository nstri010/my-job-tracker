import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json
import asyncio
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
        # timeout reduced slightly for better UX
        response = requests.get(url, headers=headers, timeout=10) 
        soup = BeautifulSoup(response.text, 'html.parser')
        for junk in soup(["script", "style", "nav", "footer", "header"]):
            junk.decompose()
        # separator='\n' helps the AI see the original list structure
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return f"Scraper Error: {e}"

def clean_description_with_ai(raw_text):
    # Added instructions to prevent the "one large paragraph" issue
    prompt = f"""
    Format this into a clean job listing. 
    1. Use bold headers for sections.
    2. Use bullet points for requirements and responsibilities.
    3. IMPORTANT: Preserve original paragraph spacing and do not summarize details into a block.
    
    TEXT:
    {raw_text[:5000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"""
    Compare this Job and Resume. 
    Provide a match score out of 10 and 3 actionable bullet points for improvement.
    
    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        # Using JSON Mode to prevent "Score: Error"
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "string"},
                        "feedback": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        )
        return json.loads(response.text)
    except: 
        return {"score": "N/A", "feedback": ["Could not generate feedback. Check API connection."]}

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
                print(f"Snapshot Error: {e}")
                if 'browser' in locals():
                    await browser.close()
                return False
    return asyncio.run(run())

