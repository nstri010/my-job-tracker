import google.generativeai as genai
import streamlit as st
import fitz
import docx
import re
import requests
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# GEMINI CONFIG
genai.configure(
    api_key=st.secrets["GOOGLE_API_KEY"]
)

# PDF SNAPSHOT
def generate_pdf_snapshot(
    job_url,
    output_file
):

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(

                headless=True,

                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]

            )

            context = browser.new_context(

                user_agent=
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36",

                viewport={
                    "width": 1440,
                    "height": 3000
                }

            )

            page = context.new_page()

            page.goto(

                job_url,

                wait_until=
                "networkidle",

                timeout=60000

            )

            time.sleep(5)

            # Remove popups/banners

            page.evaluate(
                """
                () => {

                    const selectors = [

                        '[role="dialog"]',

                        '.popup',

                        '.modal',

                        '.cookie-banner',

                        '#onetrust-banner-sdk',

                        '.privacy-policy',

                        '.sign-up-modal'

                    ];

                    selectors.forEach(

                        s => {

                            document
                            .querySelectorAll(s)

                            .forEach(
                                el => el.remove()
                            );

                        }

                    );

                }
                """
            )

            # Create REAL webpage PDF

            page.emulate_media(
                media="screen"
            )

            page.pdf(

                path=
                output_file,

                print_background=
                True,

                format=
                "A4",

                margin={

                    "top":
                    "0.3in",

                    "bottom":
                    "0.3in",

                    "left":
                    "0.3in",

                    "right":
                    "0.3in"

                }

            )

            browser.close()

        return True

    except Exception as e:

        st.error(
            f"Snapshot Error: {e}"
        )

        return False


# SCRAPE JOB PAGE

def scrape_job_link(
    url
):

    try:

        response = requests.get(

            url,

            headers={
                "User-Agent":
                "Mozilla/5.0"
            },

            timeout=10

        )

        soup = BeautifulSoup(

            response.text,

            "html.parser"

        )

        text = soup.get_text(
            separator="\n"
        )

        return text

    except Exception as e:

        return (
            f"Scrape error: {e}"
        )


# EXTRACT RESUME TEXT

def extract_text_from_upload(
    uploaded_file
):

    text = ""

    if uploaded_file.name.endswith(
        ".pdf"
    ):

        pdf = fitz.open(

            stream=
            uploaded_file.read(),

            filetype="pdf"

        )

        for page in pdf:

            text += page.get_text()

    elif uploaded_file.name.endswith(
        ".docx"
    ):

        document = docx.Document(
            uploaded_file
        )

        for para in document.paragraphs:

            text += (
                para.text + "\n"
            )

    return text
