import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #0f1117; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #7d2ae8 !important; color: white !important; border-radius: 8px !important; }
    .job-card { background: #1a1f2e; padding: 20px; border-radius: 10px; border-left: 4px solid #7d2ae8; margin-bottom: 15px; }
    .example-card { background: #1a1f2e; padding: 20px; border-radius: 10px; border: 2px dashed #4a5568; opacity: 0.5; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1.2, 1, 1.2])
    with center_col:
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 60px;'>Welcome!</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1:
            u = st.text_input("Username", placeholder="Username", key="li_u")
            p = st.text_input("Password", type="password", placeholder="Password", key="li_p")
            if st.button("Continue"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.rerun()
                else: 
                    st.error("Invalid Login: Please check your username or password.")
        with tab2:
            nu = st.text_input("Choose Username", placeholder="Create username", key="su_u")
            np = st.text_input("Set Password", type="password", placeholder="Create password", key="su_p")
            if st.button("Create Account"):
                if sign_up_user(nu, np): 
                    st.success("Account created! You can now sign in.")

# --- DASHBOARD ---
else:
    st.title("📂 Job Tracker")
    
    with st.expander("➕ Add New Application", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            comp = st.text_input("Company Name", placeholder="e.g. Google")
            pos = st.text_input("Position Title", placeholder="e.g. Data Analyst")
        with col2:
            url_input = st.text_input("Job Posting URL", placeholder="e.g. https://linkedin.com/jobs/...")
            if st.button("✨ Auto-fill Description"):
                if url_input:
                    with st.spinner("Scraping..."):
                        st.session_state['auto_desc'] = scrape_job_link(url_input)
                else: 
                    st.warning("Please paste a link first.")
        
        # FILE UPLOADER
        uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
        
        default_desc = st.session_state.get('auto_desc', "")
        desc = st.text_area("Job Description / Notes", value=default_desc, height=150, placeholder="Details about the role...")
        
        if st.button("Save Application"):
            res_url = None
            if uploaded_resume:
                with st.spinner("Uploading resume..."):
                    res_url = upload_resume(uploaded_resume, st.session_state['username'])
            
            if save_job(comp, pos, desc, url_input, res_url):
                st.session_state['auto_desc'] = "" 
                st.success("Saved!")
                st.rerun()

    st.divider()
    
    jobs = load_jobs()

    if not jobs:
        st.markdown("""
            <div class="example-card">
                <h4 style="margin:0; color: #94a3b8;">Example Position</h4>
                <p style="color:#7d2ae8; margin:0; font-weight: bold;">Example Company Inc.</p>
                <p style="color:#64748b; font-size: 0.9rem; margin-top: 5px;">
                    This is an example. Once you save your first real application, this card will disappear.
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for job in jobs:
            st.markdown(f"""
                <div class="job-card">
                    <h4 style="margin:0; color: white;">{job['position']}</h4>
                    <p style="color:#7d2ae8; margin:0; font-weight: bold;">{job['company']}</p>
                    <p style="color:#94a3b8; font-size: 0.9rem; margin: 10px 0;">{job['description'][:300]}...</p>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1,1,4])
            with c1:
                if job.get('job_url'): st.link_button("🌐 View Listing", job['job_url'])
            with c2:
                if job.get('resume_link'): st.link_button("📄 View Resume", job['resume_link'])
            with c3:
                if st.button("🗑️ Delete", key=f"del_{job['id']}"):
                    delete_job(job['id'])
                    st.rerun()
