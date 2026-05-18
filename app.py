import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #0f1117; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #7d2ae8 !important; color: white !important; border-radius: 8px !important; }
    .job-card { background: #1a1f2e; padding: 20px; border-radius: 10px; border-left: 4px solid #7d2ae8; margin-bottom: 15px; }
    .link-btn { text-decoration: none; background: #2d3748; color: white; padding: 5px 12px; border-radius: 5px; font-size: 0.8rem; margin-right: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1.2, 1, 1.2])
    with center_col:
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 60px;'>Welcome!</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1:
            u = st.text_input("Username", key="li_u")
            p = st.text_input("Password", type="password", key="li_p")
            if st.button("Continue"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Invalid login details.")
        with tab2:
            nu = st.text_input("Choose Username", key="su_u")
            np = st.text_input("Set Password", type="password", key="su_p")
            if st.button("Create Account"):
                if sign_up_user(nu, np): st.success("Created! Please Sign In.")

# --- DASHBOARD ---
else:
    st.title("📂 Job Tracker")
    
    with st.expander("➕ Add New Application", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            comp = st.text_input("Company")
            pos = st.text_input("Position")
        with col2:
            url_input = st.text_input("Job Posting URL")
            if st.button("✨ Auto-fill from Link"):
                if url_input:
                    with st.spinner("Scraping..."):
                        st.session_state['auto_desc'] = scrape_job_link(url_input)
                else: st.warning("Please paste a link first.")
        
        resume_url = st.text_input("Resume Link (Cloud Storage URL)")
        
        # Prefill description if scraped
        default_desc = st.session_state.get('auto_desc', "")
        desc = st.text_area("Job Description / Notes", value=default_desc, height=150)
        
        if st.button("Save Application"):
            if save_job(comp, pos, desc, url_input, resume_url):
                st.session_state['auto_desc'] = "" # Reset
                st.success("Saved!")
                st.rerun()

    st.divider()
    
    jobs = load_jobs()
    if not jobs:
        st.info("No applications yet. Use the form above to start tracking.")
    else:
        for job in jobs:
            with st.container():
                st.markdown(f"""
                    <div class="job-card">
                        <h4 style="margin:0; color: white;">{job['position']}</h4>
                        <p style="color:#7d2ae8; margin:0; font-weight: bold;">{job['company']}</p>
                        <p style="color:#94a3b8; font-size: 0.9rem; margin: 10px 0;">{job['description'][:300]}...</p>
                    </div>
                """, unsafe_allow_html=True)
                
                btn_col1, btn_col2, btn_col3 = st.columns([1,1,4])
                with btn_col1:
                    if job.get('job_url'):
                        st.link_button("🌐 View Listing", job['job_url'])
                with btn_col2:
                    if job.get('resume_link'):
                        st.link_button("📄 View Resume", job['resume_link'])
                with btn_col3:
                    if st.button("🗑️ Delete", key=f"del_{job['id']}"):
                        delete_job(job['id'])
                        st.rerun()
