import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user

# Page Config
st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- CSS OVERRIDE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #0f1117;
        font-family: 'Inter', sans-serif;
    }

    div[data-testid="stVerticalBlock"] > div {
        gap: 0rem !important;
    }

    div.stButton > button {
        background-color: #7d2ae8 !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 10px;
    }

    /* Styling for the Job Cards */
    .job-card {
        background: #1a1f2e; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 4px solid #7d2ae8; 
        margin-bottom: 15px;
    }

    /* Styling for the Empty State / Example Card */
    .example-card {
        background: #1a1f2e; 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px dashed #4a5568; 
        opacity: 0.5;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1.2, 1, 1.2])
    
    with center_col:
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 60px;'>Welcome!</h2>", unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 0.9rem;">A calm, organized space to track your career journey.</p>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            user_in = st.text_input("Username", placeholder="Username", key="li_user", label_visibility="collapsed")
            pass_in = st.text_input("Password", type="password", placeholder="Password", key="li_pass", label_visibility="collapsed")
            if st.button("Continue", key="login_btn"):
                if login_user(user_in, pass_in):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid Login: Please check your username or password.")
        
        with tab2:
            new_user = st.text_input("Choose Username", placeholder="Create username", key="su_user", label_visibility="collapsed")
            new_pass = st.text_input("Set Password", type="password", placeholder="Create password", key="su_pass", label_visibility="collapsed")
            if st.button("Create Account", key="signup_btn"):
                if sign_up_user(new_user, new_pass):
                    st.success("Account created! You can now sign in.")

        st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 0.85rem; font-weight: bold; margin-top: 20px;">Sign in to access your saved jobs and resumes.</p>', unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; color: #4a5568; font-size: 0.7rem; margin-top: 60px;'>Powered by Supabase</p>", unsafe_allow_html=True)

# --- MAIN DASHBOARD ---
else:
    header_col, logout_col = st.columns([5, 1])
    with header_col:
        st.title("📂 Job Tracker")
    with logout_col:
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Form to add jobs
    with st.form("job_form", clear_on_submit=True):
        st.markdown("<h3 style='color: white;'>Add New Application</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name", placeholder="e.g. Google")
        pos = c2.text_input("Position Title", placeholder="e.g. Data Analyst")
        desc = st.text_area("Application Notes", placeholder="Link to job post or resume version used...")
        if st.form_submit_button("Save to Tracker"):
            if save_job(comp, pos, desc):
                st.success("Application Saved!")
                st.rerun()

    st.divider()
    
    # FETCH JOBS
    jobs = load_jobs()

    # IF NO JOBS: SHOW THE EXAMPLE CARD
    if not jobs:
        st.markdown("""
            <div class="example-card">
                <h4 style="margin:0; color: #94a3b8;">Example Position</h4>
                <p style="color:#7d2ae8; margin:0; font-weight: bold;">Example Company Inc.</p>
                <p style="color:#64748b; font-size: 0.9rem; margin-top: 5px;">
                    This is what your tracker will look like. Once you add your first job, this example will disappear!
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # IF JOBS EXIST: LIST THEM
    else:
        for job in jobs:
            st.markdown(f"""
                <div class="job-card">
                    <h4 style="margin:0; color: white;">{job['position']}</h4>
                    <p style="color:#7d2ae8; margin:0; font-weight: bold;">{job['company']}</p>
                    <p style="color:#94a3b8; font-size: 0.9rem; margin-top: 5px;">{job['description']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Delete Application", key=f"del_{job['id']}"):
                delete_job(job['id'])
                st.rerun()
