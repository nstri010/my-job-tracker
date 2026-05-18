import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json

# --- AI CONFIGURATION ---
# Uses the key saved in your Streamlit Cloud Secrets
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"AI Configuration Error: {e}")

def extract_text_from_upload(uploaded_file):
    """Extracts raw text from an uploaded PDF or DOCX file."""
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['docx', 'doc']:
            # Reads docx into memory and extracts text
            return docx2txt.process(io.BytesIO(uploaded_file.getvalue()))
    except Exception as e:
        return f"Error reading resume file: {e}"
    return ""

def scrape_job_link(url):
    """Scrapes the webpage and prepares it for AI analysis."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip out code and navigation junk to save AI tokens
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.extract()
            
        # Using a newline separator helps the AI distinguish between sections
        raw_text = soup.get_text(separator='\n')
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return '\n'.join(lines)
    except Exception as e:
        return f"Scraping Error: {e}"

def analyze_job_with_ai(raw_job_text, resume_text=None):
    """
    Uses Gemini AI to:
    1. Reformat messy text into clean bullet points.
    2. Compare the job to the resume for a 0/10 score.
    """
    # Truncate inputs to prevent "Context Window" errors (max ~3000 chars each)
    job_snippet = raw_job_text[:4000]
    resume_snippet = resume_text[:4000] if resume_text else "No resume provided."

    prompt = f"""
    You are an expert Career Coach.
    
    TASKS:
    1. Clean the following raw job text into a professional, well-spaced format using bullet points.
    2. Use headers like 'Core Responsibilities', 'Required Skills', and 'Benefits'.
    3. If a resume is provided, analyze the fit and provide a match score out of 10 (e.g., '8/10').

    JOB TEXT:
    {job_snippet}

    RESUME TEXT:
    {resume_snippet}

    RESPONSE FORMAT (Return ONLY valid JSON):
    {{
        "formatted_desc": "The cleaned, bulleted job description here",
        "match_score": "X/10"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text_content = response.text.strip()
        
        # Logic to strip away extra AI chatter (like ```json ... ```)
        if "{" in text_content:
            text_content = text_content[text_content.find("{"):text_content.rfind("}")+1]
        
        return json.loads(text_content)
        
    except Exception as e:
        # If AI fails, we return a graceful fallback so the app doesn't crash
        return {
            "formatted_desc": f"The AI had trouble formatting this specific link. Please try again or paste the text manually.\n\nRaw Snippet: {raw_job_text[:500]}...",
            "match_score": "N/A"
        }
