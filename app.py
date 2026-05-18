import streamlit as st
import datetime
# FIXED: Separated the imports correctly onto new lines
from storage import load_jobs, save_job, update_job_status, delete_job
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker Portfolio", layout="wide")

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- STYLING ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
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
    .job-header {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        padding: 15px 20px;
        border-radius: 15px 15px 0 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .button-tray {
        background: rgba(15, 23, 42, 0.7);
        padding: 15px;
        border-radius: 0 0 15px 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        margin-bottom: 25px;
    }
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER & ACCOUNT MENU ---
head_col1, head_col2 = st.columns([4, 1])

with head_col1:
    st.title("📂 Job Application Tracker")

with head_col2:
    with st.expander("👤 Account Menu"):
        if not st.session_state['logged_in']:
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            with tab1:
                u_in = st.text_input("Username", key="login_user")
                p_in = st.text_input("Password", type="password", key="login_pw")
                if st.button("Login", use_container_width=True):
                    # Admin credentials
                    if u_in == "Nakisha" and p_in == "Password123":
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
            with tab2:
                st.info("Public registration is in development.")
        else:
            st.write(f"Logged in as **Administrator**")
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
    
    if st.button("💾 Save to Tracker"):
        if st.session_state.get('logged_in'):
            # UPDATED: Matches the new save_job function signature
            if save_job(company, position, description):
                st.success("Saved to Back4App!"); st.rerun()
        else:
            st.balloons()
            st.warning("Administrative access required to save to the database.")

# --- DISPLAY SECTION ---
st.header("📋 Your Applications")

if st.session_state.get('logged_in'):
    all_jobs = load_jobs()
    # UPDATED: Filter jobs where status is not 'Hidden'
    active_jobs = [j for j in all_jobs if j.get('status') != "Hidden"]
    
    if not active_jobs:
        st.info("Your application vault is currently empty.")
    
    for job in active_jobs:
        # UPDATED: Using 'objectId' from Back4App instead of 'id'
        obj_id = job.get('objectId')
        st.markdown(f'<div class="job-header"><div><b>{job.get("company")}</b> | {job.get("position")}</div></div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="button-tray">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                with st.expander("📝 View Details"):
                    st.write(job.get('description'))
            with c2:
                # UPDATED: Use objectId for the archive function
                if st.button("🗑️ Archive", key=f"h_{obj_id}"):
                    update_job_status(obj_id, "Hidden")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.divider()
    st.markdown("""
        <div style="text-align: center; padding: 40px 20px;">
            <h2 style="color: #ffffff;">🚧 This website is still in development</h2>
            <p style="color: #94a3b8;">Building private tracking and account management systems.</p>
        </div>
    """, unsafe_allow_html=True)
