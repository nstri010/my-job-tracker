import streamlit as st
from storage import load_jobs, save_job, update_job_status, sign_up_user, login_user
from utils import scrape_job_link

# Page Config
st.set_page_config(page_title="Job Tracker Portfolio", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- IMPROVED GLASSMORHIC STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;600&display=swap');
    
    .stApp {
        background-color: #0f1117;
        font-family: 'Geist', sans-serif;
    }

    /* Fixed Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Glass Cards for Jobs */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* Status Badges */
    .badge {
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-applied { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
    .status-under-review { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .status-interview { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .status-offer { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
    .status-rejected { background: rgba(239, 68, 68, 0.2); color: #f87171; }

    /* Buttons */
    div.stButton > button {
        background: #6366f1 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background: #4f46e5 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Now Always Visible) ---
with st.sidebar:
    st.markdown("## 👤 Account")
    
    # Removed st.expander so the login/signup is always visible
    if not st.session_state['logged_in']:
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            u_in = st.text_input("Username", key="login_u")
            p_in = st.text_input("Password", type="password", key="login_p")
            if st.button("Access Dashboard"):
                if login_user(u_in, p_in):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u_in
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        
        with tab2:
            new_u = st.text_input("Choose Username", key="reg_u")
            new_p = st.text_input("Set Password", type="password", key="reg_p")
            if st.button("Create My Account"):
                if new_u and new_p:
                    if sign_up_user(new_u, new_p):
                        st.success("Account Ready! Please Sign In.")
                else:
                    st.warning("Please fill all fields.")
    else:
        st.markdown(f"### Welcome back, **{st.session_state['username']}**")
        st.info("You are currently logged into your private application vault.")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.rerun()

# --- MAIN CONTENT AREA ---
col_main, col_spacer = st.columns([3, 1])

with col_main:
    st.title("📂 Job Application Tracker")
    st.markdown("<p style='color: #94a3b8; font-size: 1.1em;'>Organize and monitor your career journey</p>", unsafe_allow_html=True)

    # ADD NEW FORM
    with st.container():
        st.markdown("### ➕ Add New Application")
        with st.form("add_job_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                comp = st.text_input("Company Name", placeholder="e.g. Google")
                pos = st.text_input("Position Title", placeholder="e.g. QA Analyst")
            with c2:
                link = st.text_input("Job Link", placeholder="https://linkedin.com/...")
                stat = st.selectbox("Status", ["Applied", "Under Review", "Interview", "Offer", "Rejected"])
            
            desc = st.text_area("Notes / Resume Highlights", placeholder="Key skills or interview dates...")
            
            submit = st.form_submit_button("Save to My Tracker")
            
            if submit:
                if st.session_state['logged_in']:
                    if save_job(comp, pos, desc, stat):
                        st.success(f"Successfully saved {pos} at {comp}!")
                        st.rerun()
                else:
                    st.error("You must be logged in to save applications.")

    st.markdown("---")
    st.subheader("📋 Application History")

    if st.session_state['logged_in']:
        jobs = load_jobs()
        active_jobs = [j for j in jobs if j.get('status') != "Hidden"]
        
        if not active_jobs:
            st.info("Your vault is empty. Add an application above to get started!")
        
        for job in active_jobs:
            # Format the status name for CSS classes
            status_class = job.get('status').lower().replace(" ", "-")
            
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="margin:0; color:#e2e8f0; font-size: 1.2em;">{job.get('position')}</h3>
                            <p style="margin:0; color:#6366f1; font-weight: 600;">{job.get('company')}</p>
                        </div>
                        <span class="badge status-{status_class}">{job.get('status')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Details & Actions"):
                st.write(job.get('description'))
                if st.button("🗑️ Archive Application", key=f"del_{job.get('id')}"):
                    update_job_status(job.get('id'), "Hidden")
                    st.rerun()
    else:
        st.markdown("<h4 style='text-align: center; color: #4a5568; margin-top: 50px;'>Sign in to view your past saved applications and track your progress.</h4>", unsafe_allow_html=True)
