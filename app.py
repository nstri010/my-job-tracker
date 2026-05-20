import streamlit as st
import pandas as pd
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
from utils import scrape_job_link, clean_description_with_ai, get_ai_match_feedback, extract_text_from_upload

st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'formatted_desc' not in st.session_state: st.session_state['formatted_desc'] = ""
if 'match_data' not in st.session_state: st.session_state['match_data'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

if not st.session_state['logged_in']:
    st.title("🔐 Job Tracker Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(u, p):
                st.session_state['logged_in'], st.session_state['username'] = True, u
                st.rerun()
    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Create Account"):
            if sign_up_user(new_u, new_p): st.success("Created! Login above.")

if st.session_state['logged_in']:
    col_t, col_u, col_l = st.columns([4, 1.5, 1])
    with col_t: st.title("📂 Job Tracker")
    with col_u: st.write(f"👤 **{st.session_state['username']}**")
    with col_l:
        if st.button("Sign Out"):
            st.session_state['logged_in'] = False
            st.rerun()

    with st.expander("➕ Add New Application", expanded=True):
        c1, c2 = st.columns(2)
        comp, pos = c1.text_input("Company"), c2.text_input("Position")
        url_in = st.text_input("Job URL")
        if st.button("✨ Auto-Fill"):
            with st.spinner("Scraping..."):
                raw = scrape_job_link(url_in)
                st.session_state['formatted_desc'] = clean_description_with_ai(raw)
        
        final_desc = st.text_area("Description", value=st.session_state['formatted_desc'], height=200)
        up_file = st.file_uploader("Upload Resume", type=['pdf', 'docx'])
        
        if st.button("💾 Save Application"):
            with st.spinner("Taking Snapshot & Saving..."):
                score = st.session_state['match_data']['score'] if st.session_state['match_data'] else "N/A"
                res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
                if save_job(comp, pos, final_desc, url_in, res_url, score):
                    st.success("Saved!")
                    st.rerun()

    st.divider()
    st.header("📋 My Applied Jobs")
    jobs = load_jobs()
    if jobs:
        df = pd.DataFrame(jobs)
        st.dataframe(df, use_container_width=True, column_config={
            "pdf_url": st.column_config.LinkColumn("Job PDF"),
            "resume_link": st.column_config.LinkColumn("My Resume")
        })
    else:
        st.info("No saved applications yet.")
