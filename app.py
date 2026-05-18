import streamlit as st
from storage import load_jobs, save_job, update_job_status, sign_up_user, login_user
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- THE NEW AESTHETIC (Tailwind/Glass Inspired) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;600&display=swap');
    
    .stApp {
        background-color: #0f1117;
        font-family: 'Geist', sans-serif;
    }

    /* Glass Cards for Jobs */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 4px solid #6366f1;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
    }

    /* Status Badges */
    .badge {
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .status-applied { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
    .status-interview { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .status-offer { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
    .status-rejected { background: rgba(239, 68, 68, 0.2); color: #f87171; }

    /* Buttons */
    div.stButton > button {
        background: #6366f1 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("📂 Job Application Tracker")
st.markdown("<p style='color: #94a3b8;'>Organize and monitor your career applications</p>", unsafe_allow_html=True)

# --- ACCOUNT MENU ---
with st.sidebar:
    st.markdown("### 👤 Account")
    if not st.session_state['logged_in']:
        menu = st.tabs(["Sign In", "Sign Up"])
        with menu[0]:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Login"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.rerun()
        with menu[1]:
            nu = st.text_input("New Username", key="r_u")
            np = st.text_input("New Password", type="password", key="r_p")
            if st.button("Create Account"):
                if sign_up_user(nu, np): st.success("Created! Sign in now.")
    else:
        st.write(f"Welcome, **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

# --- ADD FORM (Matches your HTML structure) ---
with st.container():
    st.markdown("### Add New Application")
    with st.form("job_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name")
            position = st.text_input("Position Title")
        with col2:
            job_link = st.text_input("Job Link (URL)")
            status = st.selectbox("Application Status", 
                                ["Applied", "Under Review", "Interview", "Offer", "Rejected"])
        
        description = st.text_area("Notes / Description")
        
        if st.form_submit_button("+ Add Application"):
            if st.session_state['logged_in']:
                if save_job(company, position, description, status):
                    st.success("Application Added!")
                    st.rerun()
            else:
                st.warning("Sign in to save applications.")

# --- HISTORY SECTION ---
st.markdown("---")
st.subheader("Application History")

if st.session_state['logged_in']:
    jobs = load_jobs()
    active_jobs = [j for j in jobs if j.get('status') != "Hidden"]
    
    if not active_jobs:
        st.info("📭 No applications yet. Add your first one above!")
    
    for job in active_jobs:
        s = job.get('status', 'Applied').lower().replace(" ", "-")
        
        # This renders the "Glass Card" look from your design
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin:0; color:#e2e8f0;">{job.get('position')}</h3>
                        <p style="margin:0; color:#6366f1; font-size:0.9em;">{job.get('company')}</p>
                    </div>
                    <span class="badge status-{s}">{job.get('status')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("View Details & Actions"):
            st.write(job.get('description'))
            if st.button("🗑️ Archive Application", key=f"del_{job.get('id')}"):
                update_job_status(job.get('id'), "Hidden")
                st.rerun()
else:
    st.markdown("<h4 style='text-align: center; color: #4a5568;'>Sign in to view your application history.</h4>", unsafe_allow_html=True)
