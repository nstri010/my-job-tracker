import streamlit as st

# --- DEBUG CHECKPOINT 1 ---
st.write("🔍 Debug: Starting Imports...")

import pandas as pd
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
from utils import scrape_job_link, clean_description_with_ai, get_ai_match_feedback, extract_text_from_upload

# --- DEBUG CHECKPOINT 2 ---
st.write("🔍 Debug: Imports Finished. Setting Config...")

st.set_page_config(page_title="Job Tracker", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'formatted_desc' not in st.session_state: st.session_state['formatted_desc'] = ""
if 'match_data' not in st.session_state: st.session_state['match_data'] = None

# --- [Login Logic] ---
# Note: Ensure these functions exist in your 'storage.py'
if not st.session_state['logged_in']:
    st.title("🔐 Job Tracker Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(u, p):
                st.session_state['logged_in'] = True
                st.session_state['username'] = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_u = st.text_input("Choose Username", key="reg_user")
        new_p = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Create Account"):
            if sign_up_user(new_u, new_p):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists.")

# --- [Main App Logic] ---
if st.session_state['logged_in']:
    st.title("📂 Job Tracker")
    st.caption("⚠️ This website uses AI results. Always make sure to verify information for accuracy.")
    
    with st.expander("➕ Add New Application", expanded=True):
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            comp = st.text_input("Company Name", placeholder="e.g. Amazon")
        with row1_col2:
            pos = st.text_input("Position Title", placeholder="e.g. Systems Analyst")

        row2_col1, row2_col2 = st.columns([3, 1])
        with row2_col1:
            url_in = st.text_input("Job Posting URL", placeholder="Paste link here...")
        with row2_col2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("✨ Auto-Fill Job Description"):
                if url_in:
                    with st.spinner("Generating full listing..."):
                        raw = scrape_job_link(url_in)
                        st.session_state['formatted_desc'] = clean_description_with_ai(raw)
                else:
                    st.warning("Please enter a URL first.")

        final_desc = st.text_area("Job Description (click to edit text)", value=st.session_state['formatted_desc'], height=300)

        st.divider()

        st.subheader("🎯 AI Resume Match Scan")
        up_file = st.file_uploader("Upload Resume for Feedback", type=['pdf', 'docx'])
        
        if st.button("🔍 Scan for Match & Feedback"):
            if final_desc and up_file:
                with st.spinner("Analyzing match..."):
                    resume_txt = extract_text_from_upload(up_file)
                    st.session_state['match_data'] = get_ai_match_feedback(final_desc, resume_txt)
            else:
                st.warning("Ensure description is filled and resume is uploaded.")

        if st.session_state['match_data']:
            m = st.session_state['match_data']
            st.info(f"**AI Match Score:** {m.get('score', 'N/A')}")
            for f in m.get('feedback', []):
                st.write(f"✅ {f}")

        if st.button("💾 Save Application"):
            score_to_save = st.session_state['match_data']['score'] if st.session_state['match_data'] else "N/A"
            res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
            if save_job(comp, pos, final_desc, url_in, res_url, score_to_save):
                st.session_state['formatted_desc'] = ""
                st.session_state['match_data'] = None
                st.success("Saved!")
                st.rerun()
