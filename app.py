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

    /* Collapses vertical spacing to remove the "block" effect */
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

    .instruction-text {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 20px;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CLEAN LOGIN SCREEN ---
if not st.session_state['logged_in']:
    _, center_col, _ = st.columns([1.2, 1, 1.2])
    
    with center_col:
        # Minimalist Header
        st.markdown("<h2 style='text-align: center; color: white; margin-top: 60px;'>Welcome!</h2>", unsafe_allow_html=True)

        # Tabs for Auth
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            email_in = st.text_input("Email", placeholder="email@address.com", key="li_email", label_visibility="collapsed")
            pass_in = st.text_input("Password", type="password", placeholder="Password", key="li_pass", label_visibility="collapsed")
            if st.button("Continue", key="login_btn"):
                if login_user(email_in, pass_in):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid Login")
        
        with tab2:
            new_email = st.text_input("New Email", placeholder="email@address.com", key="su_email", label_visibility="collapsed")
            new_pass = st.text_input("New Password", type="password", placeholder="Password", key="su_pass", label_visibility="collapsed")
            if st.button("Create Account", key="signup_btn"):
                if sign_up_user(new_email, new_pass):
                    st.success("Account created!")

        # --- TEXT POSITIONED UNDER THE MENU ---
        st.markdown("""
            <div style="text-align: center; margin-top: 20px;">
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;">A calm, organized space created just for you to track your saved jobs and resumes.</p>
                <p style="color: #94a3b8; font-size: 0.85rem; font-weight: bold;">Sign in to access your saved jobs and resumes.</p>
            </div>
        """, unsafe_allow_html=True)

    # Footer
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
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company")
        pos = c2.text_input("Position")
        desc = st.text_area("Notes")
        if st.form_submit_button("Save Application"):
            if save_job(comp, pos, desc):
                st.success("Saved!")
                st.rerun()

    st.divider()
    
    # List jobs
    for job in load_jobs():
        st.markdown(f"""
            <div style="background: #1a1f2e; padding: 20px; border-radius: 10px; border-left: 4px solid #7d2ae8; margin-bottom: 10px;">
                <h4 style="margin:0; color: white;">{job['position']}</h4>
                <p style="color:#7d2ae8; margin:0; font-weight: bold;">{job['company']}</p>
                <p style="color:#94a3b8; font-size: 0.9rem; margin-top: 5px;">{job['description']}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Delete", key=f"del_{job['id']}"):
            delete_job(job['id'])
            st.rerun()
