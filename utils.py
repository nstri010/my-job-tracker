import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json

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
    """Restored the double-newline separator for perfect spacing."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for junk in soup(["script", "style", "nav", "footer", "header", "aside"]):
            junk.extract()
            
        # The key for spacing: separator='\n\n'
        return soup.get_text(separator='\n\n', strip=True)
    except Exception as e:
        return f"Scraper Error: {e}"

def clean_description_with_ai(raw_text):
    """Restores the full, non-summarized formatting logic."""
    prompt = f"""
    Act as a professional document editor. 
    Take the following job text and reformat it into a beautiful, easy-to-read job listing.
    
    RULES:
    1. Use clear bold headers (e.g., **Responsibilities**, **Requirements**).
    2. Use bullet points for all lists.
    3. Ensure there is a double space between sections.
    4. DO NOT summarize. Keep the full details of the job.
    
    TEXT:
    {raw_text[:5000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return raw_text

def get_ai_match_feedback(job_desc, resume_text):
    """New separate function for the Match Score and Feedback."""
    prompt = f"""
    Compare this Job and Resume. 
    Return a Match Score (0-10) and 3 bullet points of feedback for the candidate.
    Return ONLY JSON: {{"score": "X/10", "feedback": ["point 1", "point 2", "point 3"]}}
    
    JOB: {job_desc[:2500]}
    RESUME: {resume_text[:2500]}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {"score": "N/A", "feedback": ["Analysis currently unavailable."]}

