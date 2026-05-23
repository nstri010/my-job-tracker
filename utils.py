import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json
import asyncio
import re  # New import for robust cleaning
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
        for junk in soup(["script", "style"]): junk.decompose()
        return soup.get_text(separator=' ', strip=True)
    except: return "Could not scrape site."

def clean_description_with_ai(raw_text):
    prompt = f"Format this into a clean job listing with bold headers and bullets. Keep all details:\n\n{raw_text[:5000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    """
    Analyzes resume vs job description. 
    Uses RegEx to extract JSON if the AI includes conversational filler.
    """
    prompt = f"""
    You are a recruiter. Compare the Job and Resume.
    Return ONLY a JSON object. No conversational text.
    
    Expected JSON:
    {{
        "score": "X/10",
        "feedback": ["point 1", "point 2"]
    }}

    JOB: {job_desc[:2000]}
    RESUME: {resume_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        raw_content = response.text.strip()
        
        # 1. Look for the JSON block using a Regular Expression
        # This finds everything between the first '{' and last '}'
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        
        if json_match:
            clean_json = json_match.group(0)
            return json.loads(clean_json)
        else:
            # If no curly braces were found at all
            return {"score": "N/A", "feedback": ["AI response was not in the correct format."]}

except Exception as e:
    print(f"Error: {e}") 
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
                await browser.close()
                return False
    return asyncio.run(run())
