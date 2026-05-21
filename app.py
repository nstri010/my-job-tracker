import streamlit as st
import pandas as pd
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume, update_job_status
from utils import scrape_job_link, clean_description_with_ai, get_ai_match_feedback, extract_text_from_upload

# Page Configuration
st.set_page_config(page_title="Job Tracker", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'formatted_desc' not in st.session_state: st.session_state['formatted_desc'] = ""
if 'match_data' not in st.session_state: st.session_state['match_data'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

# --- AUTHENTICATION ---
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

# --- MAIN APP INTERFACE ---
if st.session_state['logged_in']:
    col_title, col_user, col_logout = st.columns([4, 1.5, 1])
    
    with col_title:
        st.title("📂 Job Tracker")
    with col_user:
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        st.write(f"👤 **{st.session_state['username']}**")
    with col_logout:
        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        if st.button("Sign Out", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state.clear()
            st.rerun()

    # STEP 1: ADD JOB
    with st.expander("➕ Add New Application", expanded=True):
        c1, c2 = st.columns(2)
        with c1: comp = st.text_input("Company Name")
        with c2: pos = st.text_input("Position Title")

        row2_c1, row2_c2 = st.columns([3, 1])
        with row2_c1: url_in = st.text_input("Job Posting URL")
        with row2_c2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("✨ Auto-Fill"):
                if url_in:
                    with st.spinner("Scraping..."):
                        raw = scrape_job_link(url_in)
                        st.session_state['formatted_desc'] = clean_description_with_ai(raw)
                else: st.warning("Enter URL first.")

        final_desc = st.text_area("Job Description", value=st.session_state['formatted_desc'], height=200)

        st.subheader("🎯 AI Match Scan")
        up_file = st.file_uploader("Upload Resume", type=['pdf', 'docx'])
        if st.button("🔍 Scan"):
            if final_desc and up_file:
                with st.spinner("Analyzing..."):
                    resume_txt = extract_text_from_upload(up_file)
                    st.session_state['match_data'] = get_ai_match_feedback(final_desc, resume_txt)
            else: st.warning("Need description and resume.")

        if st.session_state['match_data']:
            m = st.session_state['match_data']
            st.info(f"**Score:** {m.get('score', 'N/A')}")

        if st.button("💾 Save Application"):
            if comp and pos:
                with st.spinner("Saving..."):
                    score = st.session_state['match_data']['score'] if st.session_state['match_data'] else "N/A"
                    res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
                    if save_job(comp, pos, final_desc, url_in, res_url, score):
                        st.session_state['formatted_desc'] = ""
                        st.session_state['match_data'] = None
                        st.success("Saved!")
                        st.rerun()

    # STEP 4: VIEW & EDIT SAVED JOBS
    st.divider()
    st.header("📋 My Applied Jobs")

    jobs_list = load_jobs()

    if jobs_list:
        df = pd.DataFrame(jobs_list)
        
        # Time Formatting (Miami/Local)
        df['created_at'] = pd.to_datetime(
