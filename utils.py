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

# AI Setup - Using stable model name
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
        # Using \n separator helps preserve original structure for the AI
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        return f"Scraper Error: {e}"

def clean_description_with_ai(raw_text):
    # Instructions added to preserve spacing and prevent "one large paragraph"
    prompt = f"Format this into a clean job listing with bold headers and bullets. IMPORTANT: Preserve original paragraph spacing and do not summarize:\n\n{raw_text[:5000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    prompt = f"""
    Compare this Job and Resume. Provide a score out of 10 and 3 improvement points.
    Return ONLY a JSON object. No conversational text.
    
    Format: {{"score": "X/10", "feedback": ["point 1", "point 2", "point 3"]}}

    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        # JSON Mode enabled for portfolio stability
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
            except:
                if 'browser' in locals():
                    await browser.close()
                return False
    return asyncio.run(run())
