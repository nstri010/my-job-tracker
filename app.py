import streamlit as st
import pandas as pd
import os
import subprocess
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume, update_job_full
from utils import scrape_job_link, clean_description_with_ai, get_ai_match_feedback, extract_text_from_upload

# PLAYWRIGHT INSTALLATION (Required for snapshots)
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Browser install error: {e}")

st.set_page_config(page_title="Job Tracker", layout="wide")

# SESSION STATE INITIALIZATION
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "formatted_desc" not in st.session_state: st.session_state["formatted_desc"] = ""
if "match_data" not in st.session_state: st.session_state["match_data"] = None
if "username" not in st.session_state: st.session_state["username"] = None

# AUTHENTICATION UI
if not st.session_state["logged_in"]:
    st.title("🔐 Job Tracker Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(u, p):
                st.session_state["logged_in"], st.session_state["username"] = True, u
                st.rerun()
            else: st.error("Invalid login")
    with tab2:
        nu = st.text_input("Create Username")
        np = st.text_input("Create Password", type="password")
        if st.button("Create Account"):
            if sign_up_user(nu, np): st.success("Account created!")
            else: st.error("Username already exists")

# MAIN APP INTERFACE
if st.session_state["logged_in"]:
    t1, t2 = st.columns([5,1])
    t1.title("📂 Job Tracker")
    if t2.button("Sign Out"):
        st.session_state.clear()
        st.rerun()

    with st.expander("➕ Add New Application"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name")
        pos = c2.text_input("Position Title")
        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill Description"):
            if url_in:
                with st.spinner("Fetching details..."):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)

        final_desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=200)
        
        col1, col2 = st.columns(2)
        up_file = col1.file_uploader("Upload Resume Used", type=["pdf", "docx"])
        applied_date = col2.date_input("Date Applied")

        if st.button("🔍 Scan Match & Save"):
            if comp and pos:
                with st.spinner("Saving application and taking snapshot..."):
                    res_url = upload_resume(up_file, st.session_state["username"]) if up_file else None
                    score = "N/A"
                    if up_file and final_desc:
                        match = get_ai_match_feedback(final_desc, extract_text_from_upload(up_file))
                        score = match["score"]
                    
                    if save_job(comp, pos, final_desc, url_in, res_url, score, applied_date):
                        st.success("Application Saved!")
                        time.sleep(1)
                        st.rerun()
            else:
                st.warning("Please enter Company and Position.")

    st.divider()
    st.header("📋 My Applied Jobs")
    jobs = load_jobs()
    status_options = ["📝 Applied", "📨 Recruiter Contacted", "📅 Interview Scheduled", "🎤 Interviewed", "✅ Offer", "❌ Rejected"]

    if jobs:
        df = pd.DataFrame(jobs)
        ratios = [2, 2, 0.8, 1.5, 0.6, 0.6, 0.5]
        h = st.columns(ratios)
        cols = ["Company", "Position", "Match", "Status", "Resume", "Page", "Del"]
        for i, name in enumerate(cols): h[i].markdown(f"**{name}**")

        for _, row in df.iterrows():
            c = st.columns(ratios, vertical_alignment="center")
            c[0].write(row.get("company"))
            c[1].write(row.get("position"))
            c[2].write(row.get("match_score", "N/A"))
            
            with c[3]:
                cur = row.get("status", "📝 Applied")
                new_stat = st.selectbox("Status", status_options, index=status_options.index(cur) if cur in status_options else 0, key=f"s_{row['id']}", label_visibility="collapsed")
                if new_stat != cur:
                    update_job_full(row["id"], {"status": new_stat})
                    st.rerun()

            if row.get("resume_link"): c[4].link_button("📄", row["resume_link"])
            if row.get("pdf_url"): c[5].link_button("🌐", row["pdf_url"]) # This opens the high-quality PDF
            
            if c[6].button("❌", key=f"d_{row['id']}"):
                delete_job(row["id"])
                st.rerun()
    else:
        st.info("No applications yet.")
