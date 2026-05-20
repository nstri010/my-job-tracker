import streamlit as st
import pandas as pd
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
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

# --- MAIN APPLICATION ---
if st.session_state['logged_in']:
    # Top Header Row with Logout Button
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
            st.session_state['username'] = None
            st.rerun()
            
    st.caption("⚠️ This website uses AI results. Always verify for accuracy.")
    
    # ADD NEW JOB SECTION
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
            if st.button("✨ Auto-Fill Description"):
                if url_in:
                    with st.spinner("Generating listing..."):
                        raw = scrape_job_link(url_in)
                        st.session_state['formatted_desc'] = clean_description_with_ai(raw)
                else:
                    st.warning("Please enter a URL first.")

        final_desc = st.text_area("Job Description (editable)", value=st.session_state['formatted_desc'], height=300)

        st.divider()

        # AI MATCH SECTION
        st.subheader("🎯 AI Resume Match Scan")
        up_file = st.file_uploader("Upload Resume for Feedback", type=['pdf', 'docx'])
        
        if st.button("🔍 Scan for Match"):
            if final_desc and up_file:
                with st.spinner("Analyzing..."):
                    resume_txt = extract_text_from_upload(up_file)
                    st.session_state['match_data'] = get_ai_match_feedback(final_desc, resume_txt)
            else:
                st.warning("Ensure description is filled and resume is uploaded.")

        if st.session_state['match_data']:
            m = st.session_state['match_data']
            st.info(f"**AI Match Score:** {m.get('score', 'N/A')}")
            for f in m.get('feedback', []):
                st.write(f"✅ {f}")

        # SAVE BUTTON
        if st.button("💾 Save Application"):
            if comp and pos:
                with st.spinner("Saving data and generating PDF..."):
                    score_to_save = st.session_state['match_data']['score'] if st.session_state['match_data'] else "N/A"
                    res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
                    
                    if save_job(comp, pos, final_desc, url_in, res_url, score_to_save):
                        st.session_state['formatted_desc'] = ""
                        st.session_state['match_data'] = None
                        st.success("Application and Job PDF saved successfully!")
                        st.rerun()
            else:
                st.warning("Please provide a Company Name and Position.")

    # VIEW SAVED JOBS SECTION (Fixed Indentation)
    st.divider()
    st.header("📋 My Applied Jobs")
    jobs_list = load_jobs()
    
    if jobs_list:
        df = pd.DataFrame(jobs_list)
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "pdf_url": st.column_config.LinkColumn("Job PDF"),
                "resume_link": st.column_config.LinkColumn("My Resume"),
                "job_url": st.column_config.LinkColumn("Original Link")
            }
        )
    else:
        st.info("No applications saved yet. Start by adding one above!")
