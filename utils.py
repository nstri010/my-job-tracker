import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io
import google.generativeai as genai
import streamlit as st
import json

# Configure AI (Ensure GOOGLE_API_KEY is in your Streamlit Secrets)
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
    prompt = f"""
    You are an expert career coach. 
    1. Clean up the following raw job description text. Reformat it into professional bullet points with clear headers (Responsibilities, Requirements, Benefits). Fix all spacing issues.
    2. If a resume is provided, analyze the match and provide a score from 0 to 10.
    
    JOB TEXT:
    {raw_job_text[:4000]}
    
    RESUME TEXT:
    {resume_text if resume_text else "No resume provided."}
    
    Return the result in this exact JSON format:
    {{
        "formatted_desc": "the cleaned text here",
        "match_score": "X/10",
        "brief_reasoning": "one sentence why"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Clean the response text to ensure it's valid JSON
        json_data = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_data)
    except Exception as e:
        return {
            "formatted_desc": "Error formatting text. Please paste manually.",
            "match_score": "N/A",
            "brief_reasoning": str(e)
        }
