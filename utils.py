import requests
from bs4 import BeautifulSoup
import pypdf
import docx2txt
import io

def extract_text_from_upload(uploaded_file):
    """Extracts text from an uploaded PDF or DOCX file object."""
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
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)[:2000]
    except Exception as e:
        return f"Could not fetch description: {e}"
