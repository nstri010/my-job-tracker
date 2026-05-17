import streamlit as st
import datetime
from storage import load_jobs, save_job, build_job_record, update_job_status, update_job_details
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker Portfolio", layout="wide")

# Initialize session state for login if it doesn't exist
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- CUSTOM HEADER WITH TOP-RIGHT MENU ---
head_col1, head_col2 = st.columns([4, 1])

with head_col1:
    st.title("📂 Job Application Tracker")

with head_col2:
    with st.expander("👤 Account Menu"):
        if not st.session_state['logged_in']:
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            with tab1:
                # ADMIN LOGIN CREDENTIALS
                ADMIN_USERNAME = "Nakisha"
                ADMIN_PASSWORD = "Password123" # <--- CHANGE THIS
                
                u_in = st.text_input("Username", key="login_user")
                p_in = st.text_input("Password", type="password", key="login_pw")
                
                if st.button("Login", use_container_width=True):
                    if u_in == ADMIN_USERNAME and p_in == ADMIN_PASSWORD:
                        st.session_state['logged_in'] = True
                        st.success("Welcome, Nakisha!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
            with tab2:
                st.write("✨ **Interested in your own tracker?**")
                st.info("Account creation is currently restricted to the administrator. Please reach out via LinkedIn for a full demo!")
        else:
            st.write(f"Logged in as **Nakisha**")
            if st.button("Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.rerun()

# --- STYLING ---
st.markdown("""
    <style>
    /* Hide Sidebar and customize theme */
    [data-testid="stSidebarNav"] {display: none;}
    .stApp { background: #0b0f19; color: white; }
    .job-header { background: #1a1f2b; padding: 12px 18px; border-radius: 8px 8px 0 0; border-left: 5px solid #ff4b4b; border-bottom: 1px solid #2e3440; display: flex; justify-content: space-between; align-items: center; }
    .button-tray { background: #161b22; padding: 10px; border-radius: 0 0 8px 8px; border: 1px solid #2e3440; border-top: none; margin-bottom: 20px; }
    .stExpander { border: 1px solid #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ADD NEW JOB SECTION (GUEST DEMO READY) ---
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
            # REAL SAVE TO GOOGLE SHEETS
            if save_job(build_job_record(company, position, description, applied_on)):
                st.success("Successfully saved to Private Vault!"); st.rerun()
        else:
            # GUEST DEMO MODE
            st.balloons()
            st.warning("✨ Demo Mode: If you were logged in, this would save to your Google Sheet!")

# --- DISPLAY SECTION (ADMIN GATED) ---
st.header("📋 Your Applications")

if st.session_state.get('logged_in'):
    all_jobs = load_jobs()
    # Filter for jobs that aren't 'Hidden'
    active_jobs = [j for j in all_jobs if str(j.get('status', '')) != "Hidden"]

    if not active_jobs:
        st.info("Your private vault is currently empty.")
    
    for job in reversed(active_jobs):
        job_date = job.get('date_applied', 'N/A')
        st.markdown(f'<div class="job-header"><div><b>{job["company"]}</b> | {job["position"]}</div><div style="color: gray;">📅 {job_date}</div></div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="button-tray">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            
            with c1:
                with st.expander("📝 View / Edit Details"):
                    st.write(job['description'])
                    st.divider()
                    n_c = st.text_input("Company", value=job['company'], key=f"ec_{job['id']}")
                    n_p = st.text_input("Position", value=job['position'], key=f"ep_{job['id']}")
                    n_d = st.text_area("Description", value=job['description'], key=f"ed_{job['id']}", height=200)
                    if st.button("💾 Save Changes", key=f"up_{job['id']}"):
                        update_job_details(job['id'], n_c, n_p, n_d)
                        st.rerun()
            
            with c2:
                if st.button("🗑️ Archive", key=f"h_{job['id']}"):
                    update_job_status(job['id'], "Hidden")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("🔒 Private data is hidden. Log in via the Account Menu to view saved applications.")
    # Portfolio placeholder
    st.image("https://images.unsplash.com/photo-1586281380349-63157106804c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", caption="Admin Dashboard (Private Mode)")
