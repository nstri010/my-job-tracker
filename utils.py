import os
import requests
import pypdf
import docx2txt
import pdfkit
from bs4 import BeautifulSoup

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext in ['.docx', '.doc']:
            return docx2txt.process(file_path)
    except Exception as e:
        print(f"Error: {e}")
    return ""

def scrape_job_link(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.extract()
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)[:5000]
    except Exception as e:
        return f"Could not fetch: {e}"

def generate_pdf_snapshot(url, filename):
    try:
        output_path = f"resumes/{filename}"
        path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
        pdfkit.from_url(url, output_path, configuration=config)
        return True
    except:
        return False