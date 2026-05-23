import streamlit as st
import pandas as pd
import os
import subprocess

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

# PLAYWRIGHT INSTALL
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Browser install error: {e}")

# PAGE CONFIG
st.set_page_config(page_title="Job Tracker", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""
if "match_data" not in st.session_state:
    st.session_state["match_data"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# LOGIN LOGIC (Omitted for brevity, keep your existing logic)
# ... 

# MAIN APP
if st.session_state["logged_in"]:
    top1, top2 = st.columns([5,1])
    with top1:
        st.title("📂 Job Tracker")
    with top2:
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

    with st.expander("➕ Add New Application"):
        c1,c2 = st.columns(2)
        with c1: comp = st.text_input("Company Name")
        with c2: pos = st.text_input("Position Title")
        
        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill"):
            if url_in:
                with st.spinner("Filling out description..."):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)

        final_desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=220)

        col1,col2 = st.columns(2)
        with col1: up_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
        with col2: applied_date = st.date_input("Date Applied")

        if st.button("🔍 Scan & Save Application"):
            if final_desc and up_file and comp and pos:
                with st.spinner("Saving application and taking snapshot..."):
                    resume_txt = extract_text_from_upload(up_file)
                    match = get_ai_match_feedback(final_desc, resume_txt)
                    
                    # Upload Resume
                    res_url = upload_resume(up_file, st.session_state["username"])
                    
                    # Save Job (This triggers the snapshot)
                    success = save_job(comp, pos, final_desc, url_in, res_url, match['score'], applied_date)
                    
                    if success:
                        st.success("Application Saved!")
                        st.rerun()
            else:
                st.warning("Please fill in all fields before scanning.")

    st.divider()
    # Table logic remains the same
