import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai # Or use openai
import streamlit as st

# Configure your AI (Example using Google Gemini, which has a free tier)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

def extract_text_from_upload(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['docx', 'doc']:
            return docx2txt.process(io.BytesIO(uploaded_file.getvalue()))
    except Exception as e:
        return f"Error reading file: {e}"
    return ""

def scrape_job_link(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.extract()
        return soup.get_text(separator=' ')
    except Exception as e:
        return f"Error: {e}"

def analyze_job_with_ai(raw_job_text, resume_text=None):
    """Uses AI to format the job description and score the resume match."""
    prompt = f"""
    You are a career assistant. I will provide raw text from a job posting.
    1. Reformat the job description into clean, professional bullet points with proper spacing.
    2. If a resume is provided, compare it to the job and give a 'Match Score' out of 10.
    
    JOB TEXT:
    {raw_job_text[:4000]}
    
    RESUME TEXT:
    {resume_text if resume_text else "No resume provided."}
    
    RETURN ONLY A JSON OBJECT with these keys: 
    'formatted_desc' (string), 'match_score' (string like "8/10"), 'analysis' (short 2-sentence summary).
    """
    try:
        response = model.generate_content(prompt)
        # In a real app, use json.loads(response.text). For simplicity here:
        return response.text 
    except Exception as e:
        return f"AI Error: {e}"
