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
    """Extracts text from uploaded PDF or DOCX files."""
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
    """Scrapes raw text from a job posting URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for junk in soup(["script", "style"]): junk.decompose()
        return soup.get_text(separator=' ', strip=True)
    except: return "Could not scrape site."

def clean_description_with_ai(raw_text):
    """Uses AI to format messy scraped text into a readable job description."""
    prompt = f"Format this into a clean job listing with bold headers and bullets. Keep all details:\n\n{raw_text[:5000]}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    """
    Compares the job description and resume. 
    Includes strict cleaning to prevent 'Score: N/A' errors caused by JSON formatting.
    """
    prompt = f"""
    You are a professional recruiter. Compare the following Job Description and Resume.
    
    Return ONLY a valid JSON object. Do not include any introductory text, markdown formatting (like ```json), or explanations.
    
    Expected JSON format:
    {{
        "score": "X/10",
        "feedback": ["point 1", "point 2", "point 3"]
    }}

    JOB DESCRIPTION:
    {job_desc[:2000]}

    RESUME:
    {resume_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        # Cleanup: Remove markdown code blocks if the AI included them
        if text_response.startswith("```"):
            text_response = text_response.strip("`").replace("json", "", 1).strip()
            
        return json.loads(text_response)
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        return {"score": "Error", "feedback": ["AI could not parse the response. Please try again."]}

def generate_pdf_snapshot(url, filename):
    """Uses Playwright to take a PDF snapshot of the job website."""
    async def run():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                # networkidle waits for the page to finish loading images/scripts
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.pdf(path=filename, format="A4")
                await browser.close()
                return True
            except:
                await browser.close()
                return False
    return asyncio.run(run())
