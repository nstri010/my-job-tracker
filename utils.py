import os
import requests
from bs4 import BeautifulSoup

def scrape_job_link(url):
    """Fetches the webpage and extracts the main text for the job description."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove clutter like scripts and footers
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.extract()
            
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        # Return first 2000 characters to keep it clean
        return '\n'.join(lines)[:2000]
    except Exception as e:
        return f"Could not fetch description automatically: {e}"
