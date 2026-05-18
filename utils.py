import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json

# --- AI CONFIGURATION ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
# Using Gemini 1.5 Flash - it's faster and better at handling messy data
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_upload(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(uploaded_file)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['docx', 'doc']:
            return docx2txt.process(io.BytesIO(uploaded_file.getvalue()))
    except Exception as e:
        return ""
    return ""

def scrape_job_link(url):
    """Enhanced scraper with real-user headers to bypass basic blocks."""
    try:
        # These headers make the script look like a real Chrome browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return f"Error: Received status {response.status_code} from site."

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Focus on the 'main' content areas where job descriptions usually live
        for junk in soup(["script", "style", "nav", "footer", "header"]):
            junk.extract()
            
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return str(e)

def analyze_job_with_ai(raw_job_text, resume_text=None):
    """Uses Gemini's JSON mode to ensure the app never gets a 'formatting error'."""
    
    # If the scraper failed and returned an error message, we tell the AI
    job_input = raw_job_text[:5000] if len(raw_job_text) > 100 else "The scraper failed to find text. Please ask the user to paste the description."
    resume_input = resume_text[:5000] if resume_text else "No resume provided."

    prompt = f"""
    Act as a Career Consultant. 
    1. Clean the JOB TEXT into professional bullet points. 
    2. Score the RESUME against the job from 0/10.
    
    JOB TEXT: {job_input}
    RESUME TEXT: {resume_input}

    IMPORTANT: You MUST return a valid JSON object with 'formatted_desc' and 'match_score' keys. 
    If the JOB TEXT is empty or looks like an error, set 'formatted_desc' to 'Scraper blocked. Please paste description manually.'
    """

    try:
        # response_mime_type forces the AI to output ONLY JSON
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "formatted_desc": "AI was unable to process. Please paste the description manually.",
            "match_score": "N/A"
        }
