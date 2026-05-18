import streamlit as st
from storage import load_jobs, save_job, update_job_status, sign_up_user, login_user
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker Portfolio", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); color: #f8fafc; }
    div.stButton > button {
        border-radius: 50px !important;
        background: linear-gradient(90deg, #f97316 0%, #faa05a 100%) !important;
        color: #0f172a !important; font-weight: bold !important;
        border: none !important; padding: 10px 25px !important;
    }
    .job-header {
        background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(12px);
        padding: 15px 20px; border-radius: 15px 15px 0 0; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .button-tray {
        background: rgba(15, 23, 42, 0.7); padding: 15px;
        border-radius: 0 0 15px 15px; border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none; margin-bottom: 25px;
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
                    if login_user(u_in, p_in):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = u_in
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
            
            with tab2:
                st.write("### Create an Account")
                new_user = st.text_input("New Username", key="reg_user")
                new_pw = st.text_input("New Password", type="password", key="reg_pw")
                if st.button("Register Account", use_container_width=True):
                    if new_user and new_pw:
                        if sign_up_user(new_user, new_pw):
                            st.success("Account created! You can now Sign In.")
                        else:
                            st.error("Registration failed.")
                    else:
                        st.warning("Please fill in all fields.")
        else:
            st.write(f"Logged in as: **{st.session_state.get('username', 'User')}**")
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
            if save_job(company, position, description):
                st.success("Successfully saved to Supabase!")
                st.rerun()
        else:
            st.warning("Please Sign In to save jobs.")

# --- DISPLAY SECTION ---
st.header("📋 Your Applications")

if st.session_state.get('logged_in'):
    all_jobs = load_jobs()
    active_jobs = [j for j in all_jobs if j.get('status') != "Hidden"]
    
    if not active_jobs:
        st.info("Your application vault is currently empty.")
    
    for job in active_jobs:
        job_id = job.get('id') 
        st.markdown(f'''
            <div class="job-header">
                <div><b>{job.get("company")}</b> | {job.get("position")}</div>
            </div>
        ''', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="button-tray">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 1])
            with c1:
                with st.expander("📝 View Details"):
                    st.write(job.get('description'))
            with c2:
                if st.button("🗑️ Archive", key=f"h_{job_id}"):
                    update_job_status(job_id, "Hidden")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
else:
    st.divider()
    st.markdown("<h3 style='text-align: center;'>Sign In to view your private tracker.</h3>", unsafe_allow_html=True)
