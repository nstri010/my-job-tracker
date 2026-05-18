import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user

# Page Config
st.set_page_config(page_title="Job Tracker", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- PROFESSIONAL UI STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background-color: #0f1117;
        font-family: 'Inter', sans-serif;
    }

    /* The Login Card Container */
    .auth-card {
        background-color: #1a1f2e;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #2d3748;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }

    /* Big Bold Header */
    .auth-header {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
    }

    /* Buttons - Matching your purple example */
    div.stButton > button {
        background-color: #7d2ae8 !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #6a22c4 !important;
        box-shadow: 0 4px 15px rgba(125, 42, 232, 0.4);
    }

    /* Input field styling */
    input {
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CENTERED LOGIN INTERFACE ---
if not st.session_state['logged_in']:
    # This creates the "centered" effect using empty columns
    left_spacer, center_column, right_spacer = st.columns([1, 1.5, 1])
    
    with center_column:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<p class="auth-header">Jump back in!</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            email_in = st.text_input("Email Address", placeholder="e.g. name@email.com")
            pass_in = st.text_input("Password", type="password", placeholder="••••••••")
            if st.button("Continue", key="login_btn"):
                if login_user(email_in, pass_in):
                    st.session_state['logged_in'] = True
                    st.session_state['user_email'] = email_in
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        
        with tab2:
            new_email = st.text_input("Choose Email", placeholder="yourname@email.com")
            new_pass = st.text_input("Create Password", type="password", placeholder="Minimum 6 characters")
            if st.button("Create My Account", key="signup_btn"):
                if new_email and new_pass:
                    if sign_up_user(new_email, new_pass):
                        st.success("Account created! Please Sign In.")
                else:
                    st.warning("Please fill out all fields.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 20px;'>By continuing, you agree to the Terms of Service.</p>", unsafe_allow_html=True)

# --- MAIN DASHBOARD (Only visible after login) ---
else:
    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.title("📂 Job Application Tracker")
    with col_logout:
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()

    # --- ADD NEW JOB FORM ---
    with st.expander("➕ Track a New Application", expanded=True):
        with st.form("job_form"):
            c1, c2 = st.columns(2)
            comp = c1.text_input("Company Name")
            pos = c2.text_input("Position Title")
            desc = st.text_area("Job Description / Notes")
            if st.form_submit_button("Save Application"):
                if save_job(comp, pos, desc):
                    st.success("Application tracked!")
                    st.rerun()

    # --- DISPLAY JOBS ---
    st.divider()
    jobs = load_jobs()
    if jobs:
        for job in jobs:
            st.markdown(f"""
                <div style="background: #1a1f2e; padding: 20px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #7d2ae8;">
                    <h3 style="margin:0;">{job['position']}</h3>
                    <p style="color:#7d2ae8; font-weight:bold;">{job['company']}</p>
                    <p style="font-size:0.9rem; color:#94a3b8;">{job['description']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Delete", key=f"del_{job['id']}"):
                delete_job(job['id'])
                st.rerun()
    else:
        st.info("No applications found. Start by adding one above!")
