import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from PIL import Image

# GEMINI CONFIG
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def generate_pdf_snapshot(job_url, output_file):
    try:
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            
            # Set a standard Desktop Viewport to avoid mobile/text layouts
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 3000}
            )
            
            page = context.new_page()
            
            # Wait for networkidle so images and CSS are fully loaded
            page.goto(job_url, wait_until="networkidle", timeout=60000)
            
            # Allow time for dynamic content/branding to appear
            time.sleep(5)

            # SCRIPT: Remove banners or popups that block the visual view
            page.evaluate("""
                () => {
                    const selectors = [
                        '[role="dialog"]', '.popup', '.modal', '.cookie-banner', 
                        '#onetrust-banner-sdk', '.privacy-policy', '.sign-up-modal'
                    ];
                    selectors.forEach(s => {
                        document.querySelectorAll(s).forEach(el => el.remove());
                    });
                }
            """)

            # TAKE THE VISUAL SNAPSHOT
            page.emulate_media(media="screen")

page.pdf(
    path=output_file,
    print_background=True,
    format="A4",
    margin={
        "top": "0.3in",
        "bottom": "0.3in",
        "left": "0.3in",
        "right": "0.3in"
    }
)

browser.close()
        
        # Cleanup
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            
        return True

    except Exception as e:
        st.error(f"Snapshot Error: {e}")
        return False
