import streamlit as st
import datetime
from storage import load_jobs, save_job, build_job_record, update_job_status, update_job_details
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker Portfolio", layout="wide")

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- STYLING (Inspired by "Still Here Hope") ---
st.markdown("""
    <style>
    /* 1. Background Gradient */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }

    /* 2. Rounded, Glowing Gradient Buttons */
    div.stButton > button {
        border-radius: 50px !important;
        background: linear-gradient(90deg, #f97316 0%, #faa05a 100%) !important;
        color: #0f172a !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 25px !important;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0px 0px 20px rgba(249, 115, 22, 0.4);
    }

    /* 3. Transparent Glass Cards */
    .job-header {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        padding: 15px 20px;
        border-radius: 15px 15px 0 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: none;
    }
    
    .button-tray {
        background: rgba(15, 23, 42, 0.7);
        padding: 15px;
        border-radius: 0 0 15px 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        margin-bottom: 25px;
    }

    /* Account Menu Expander */
    .stExpander {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Hiding Sidebar */
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- CUSTOM HEADER ---
head_col1, head_col2 = st.columns([4, 1])

with head_col1:
    st.title("📂 Job Application Tracker")

with head_col2:
    with st.expander("👤 Account Menu"):
        if not st.session_state['logged_in']:
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            with tab1:
                ADMIN_USERNAME = "Nakisha"
                ADMIN_PASSWORD = "Password123" # <--- Change this on GitHub!
                
                u_in = st.text_input("Username", key="login_user")
                p_in = st.text_input("Password", type="password", key="login_pw")
                
                if st.button("Login", use_container_width=True):
                    if u_in == ADMIN_USERNAME and p_in == ADMIN_PASSWORD:
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
            with tab2:
                st.info("Account creation is restricted to the administrator.")
        else:
            st.write(f"Hello, **{ADMIN_USERNAME}**")
            if st.button("Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()

# --- ADD NEW JOB SECTION ---
with st.expander("➕ Add New Application"):
    c1, c2 = st.columns(2)
    with c1: company = st.text_input("Company Name")
    with c2: position = st.text_input("Position")
    job_link = st.text_input("Job Listing URL")
    
    if st.button("🔍 Auto-Fill Description"):
        if job_link:
            st.session_state['fetched_text'] = scrape_job_link(job_link)
        else: st.warning("Please paste a link first.")

    description = st.text_area("Job Description", value=st.session_state.get('fetched_text', ""), height=150)
    applied_on = st.date_input("Date Applied", datetime.date.today())
    
    if st.button("💾 Save to Tracker"):
        if st.session_state.get('logged_in'):
            if save_job(build_job_record(company, position, description, applied_on)):
                st.success("Successfully saved!"); st.rerun()
        else:
            st.balloons()
            st.warning("✨ Demo Mode: Sign in to save this to the real database!")

# --- DISPLAY SECTION ---
st.header("📋 Your Applications")

if st.session_state.get('logged_in'):
    all_jobs = load_jobs()
    active_jobs = [j for j in all_jobs if str(j.get('status', '')) != "Hidden"]

    if not active_jobs:
        st.info("No applications found.")
    
    for job in reversed(active_jobs):
        job_date = job.get('date_applied', 'N/A')
        st.markdown(f'<div class="job-header"><div><b>{job["company"]}</b> | {job["position"]}</div><div style="color: #94a3b8;">📅 {job_date}</div></div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="button-tray">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                with st.expander("📝 View / Edit"):
                    st.write(job['description'])
                    st.divider()
                    n_c = st.text_input("Company", value=job['company'], key=f"ec_{job['id']}")
                    n_p = st.text_input("Position", value=job['position'], key=f"ep_{job['id']}")
                    n_d = st.text_area("Description", value=job['description'], key=f"ed_{job['id']}", height=200)
                    if st.button("💾 Save Changes", key=f"up_{job['id']}"):
                        update_job_details(job['id'], n_c, n_p, n_d); st.rerun()
            with c2:
                if st.button("🗑️ Archive", key=f"h_{job['id']}"):
                    update_job_status(job['id'], "Hidden"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- USER FRIENDLY GUEST MESSAGE ---
    st.divider()
    st.markdown("""
        <div style="text-align: center; padding: 40px 20px;">
            <h2 style="color: #ffffff; margin-bottom: 10px;">✨ Try it out!</h2>
            <p style="color: #94a3b8; font-size: 1.2em;">
                This website is currently in development. More features coming soon!
            </p>
            <p style="color: #64748b; font-size: 1.1em; max-width: 600px; margin: 0 auto;">
                If you would like to save your applications and track your progress, 
                please <b>create an account</b> or <b>sign in</b>.
            </p>
            <p style="color: #f97316; font-size: 0.9em; margin-top: 25px; opacity: 0.8;">
                <i>Note: Private tracking is currently reserved for the site administrator.</i>
            </p>
        </div>
    """, unsafe_allow_html=True)
