import streamlit as st
import pandas as pd
import os
from datetime import datetime

from storage import (
    load_jobs,
    save_job,
    delete_job,
    sign_up_user,
    login_user,
    upload_resume,
    update_job_full
)

from utils import (
    scrape_job_link,
    clean_description_with_ai,
    get_ai_match_feedback,
    extract_text_from_upload
)

st.set_page_config(
    page_title="Job Tracker",
    layout="wide"
)

# SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""
if "match_data" not in st.session_state:
    st.session_state["match_data"] = None
if "resume_txt" not in st.session_state:
    st.session_state["resume_txt"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True  # Defaulting to true for your screenshot look

# ── THEME CSS ──────────────────────────────────────────────────────────────────

DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Global Background and Font */
    .stApp {
        background-color: #0f0f0f;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1a151c !important;
        border-right: 1px solid #2d2631;
    }

    /* Headers and Titles */
    h1, h2, h3 {
        color: #d1b3ff !important;
        font-weight: 700 !important;
    }

    /* Input Boxes */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #3d3446 !important;
        border-radius: 8px !important;
    }

    /* Buttons (The Lavender Glow) */
    .stButton button {
        background-color: #4b306b !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background-color: #6b469b !important;
        box-shadow: 0px 0px 12px rgba(179, 136, 255, 0.4);
    }

    /* Metric/Match Score Highlights */
    [data-testid="stMetricValue"] {
        color: #b388ff !important;
    }

    /* Table/Row Containers */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #161616 !important;
        border: 1px solid #2d2631 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }
</style>
"""

if st.session_state["dark_mode"]:
    st.markdown(DARK_CSS, unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Job Tracker")
    
    if not st.session_state["logged_in"]:
        mode = st.radio("Access", ["Login", "Sign Up"])
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Submit"):
            if mode == "Login":
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                if sign_up_user(u, p):
                    st.success("Account created!")
                else:
                    st.error("Error creating account")
        st.stop()

    st.write(f"Logged in as: **{st.session_state['username']}**")
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

# ── MAIN CONTENT ──────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["➕ Add New Application", "📋 Application History"])

with tab1:
    st.header("New Application")
    
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company Name")
        position = st.text_input("Position Title")
        job_url = st.text_input("Job URL")
        
    with col2:
        res_file = st.file_uploader("Upload Resume Used", type=["pdf", "docx"])
        if res_file:
            st.session_state["resume_txt"] = extract_text_from_upload(res_file)

    if st.button("Scrape & Analyze"):
        if job_url:
            with st.spinner("Analyzing job details..."):
                raw_desc = scrape_job_link(job_url)
                st.session_state["formatted_desc"] = clean_description_with_ai(raw_desc)
                
                if st.session_state["resume_txt"]:
                    st.session_state["match_data"] = get_ai_match_feedback(
                        st.session_state["formatted_desc"], 
                        st.session_state["resume_txt"]
                    )

    if st.session_state["formatted_desc"]:
        st.subheader("Job Description")
        desc_area = st.text_area("Review/Edit Description", st.session_state["formatted_desc"], height=250)
        
        if st.session_state["match_data"]:
            st.subheader("AI Match Analysis")
            st.write(st.session_state["match_data"])

        if st.button("Save to Tracker"):
            score = "N/A"
            if st.session_state["match_data"]:
                import re
                m = re.search(r"SCORE:\s*(\d+)", st.session_state["match_data"])
                if m: score = m.group(1)

            res_url = upload_resume(res_file, st.session_state["username"]) if res_file else None
            
            success = save_job(
                company, position, desc_area, job_url, 
                res_url, score, datetime.now()
            )
            if success:
                st.success("Application tracked!")
                st.session_state["formatted_desc"] = ""
                st.rerun()

with tab2:
    st.header("Application Log")
    jobs = load_jobs()
    
    if not jobs:
        st.info("No applications found.")
    else:
        # Header Row
        h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([2, 2, 2, 2, 1])
        h_col1.write("**Company**")
        h_col2.write("**Position**")
        h_col3.write("**Score**")
        h_col4.write("**Status**")
        h_col5.write("**Actions**")
        
        for job in jobs:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                c1.write(job["company"])
                c2.write(job["position"])
                c3.write(f"🎯 {job['match_score']}/10")
                
                status_options = ["Active", "Interviewing", "Offer", "Rejected", "Ghosted"]
                new_status = c4.selectbox(
                    "Status", status_options, 
                    index=status_options.index(job["status"]) if job["status"] in status_options else 0,
                    key=f"status_{job['id']}",
                    label_visibility="collapsed"
                )
                
                if new_status != job["status"]:
                    update_job_full(job["id"], {"status": new_status})
                
                if c5.button("🗑️", key=f"del_{job['id']}"):
                    delete_job(job["id"])
                    st.rerun()
