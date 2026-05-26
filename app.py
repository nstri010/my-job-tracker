import streamlit as st
import pandas as pd
import os
from datetime import datetime

from storage import (
    load_jobs,
    save_job,
    delete_job,
    sign_up_user,
    login_user,
    upload_resume,
    update_job_full,
    send_password_reset
)

from utils import (
    scrape_job_link,
    clean_description_with_ai,
    get_ai_match_feedback,
    extract_text_from_upload
)

st.set_page_config(page_title="Job Tracker", layout="wide")

# SESSION
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""
if "match_data" not in st.session_state:
    st.session_state["match_data"] = None
if "resume_txt" not in st.session_state:
    st.session_state["resume_txt"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "login_tab" not in st.session_state:
    st.session_state["login_tab"] = "login"
if "reset_sent" not in st.session_state:
    st.session_state["reset_sent"] = False

# ── CSS ────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600;700&display=swap');

/* ── Reference-Matched Background ── */
[data-testid="stAppViewContainer"] {
    background-color: #0d0d12 !important;
    /* Layer 1: Radial Glows | Layer 2: Grid Pattern | Layer 3: Base Dark */
    background-image: 
        radial-gradient(circle at 15% 25%, rgba(244, 114, 182, 0.12) 0%, transparent 35%),
        radial-gradient(circle at 85% 75%, rgba(192, 132, 252, 0.1) 0%, transparent 40%),
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 45px 45px, 45px 45px !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 100% !important; }

/* ── Typography ── */
* { font-family: 'Inter', sans-serif !important; }
h1, .login-logo { font-family: 'Playfair Display', serif !important; color: #ffffff !important; letter-spacing: -0.02em; }
p, label { color: #94a3b8 !important; font-weight: 400 !important; }

/* ── Glassmorphism Login Panels ── */
.login-left {
    background: rgba(18, 18, 24, 0.7) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 24px;
    padding: 60px 50px;
    height: 100%;
}
.login-right {
    background: transparent !important;
    padding: 60px 50px;
}

/* ── Inputs (Terminal Style) ── */
.stTextInput input, .stTextArea textarea {
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 12px !important;
}
.stTextInput input:focus { border-color: #f472b6 !important; box-shadow: 0 0 10px rgba(244, 114, 182, 0.2) !important; }

/* ── Buttons ── */
.stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover { 
    background: rgba(244, 114, 182, 0.1) !important; 
    border-color: #f472b6 !important;
}

/* Primary "Create Account" Action */
div[data-testid="stForm"] .stButton > button, 
.primary-btn > button {
    background: linear-gradient(135deg, #f472b6 0%, #d946ef 100%) !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ── Dashboard Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    st.markdown("<div style='height:5rem'></div>", unsafe_allow_html=True)
    l_col, r_col = st.columns([1.1, 1], gap="large")

    with l_col:
        st.markdown("""
        <div class="login-left">
            <div style="font-size:32px; color:#f472b6; margin-bottom:8px; font-family:'Playfair Display'">✦ Job Tracker</div>
            <div style="color:#64748b; font-size:12px; margin-bottom:40px; letter-spacing:2px; text-transform:uppercase;">AI Career Intelligence</div>
            <h1 style="font-size:62px; line-height:1.1; margin-bottom:24px;">Land Your<br>Dream Job.</h1>
            <p style="font-size:17px; line-height:1.6; max-width:400px; margin-bottom:60px;">
                The modern command center for your job search. Track applications and optimize your resume with AI-driven matching.
            </p>
            <div style="display:flex; gap:60px;">
                <div><div style="font-size:32px; font-weight:700; color:#f472b6;">98%</div><div style="color:#64748b; font-size:12px;">Match Accuracy</div></div>
                <div><div style="font-size:32px; font-weight:700; color:#c084fc;">24/7</div><div style="color:#64748b; font-size:12px;">Auto Tracking</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)
        tab = st.session_state["login_tab"]

        if tab == "login":
            st.markdown("<h2 style='font-size:36px; margin-bottom:8px;'>Welcome Back</h2>", unsafe_allow_html=True)
            st.markdown("<p style='margin-bottom:32px;'>Enter your credentials to access your dashboard</p>", unsafe_allow_html=True)
            u = st.text_input("Username", key="login_username")
            p = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Sign In", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else: st.error("Invalid credentials")
            
            st.markdown("<p style='text-align:center; margin-top:20px;'>New here? <span style='color:#f472b6;'>Create account</span></p>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True):
                st.session_state["login_tab"] = "signup"; st.rerun()

        elif tab == "signup":
            st.markdown("<h2 style='font-size:36px; margin-bottom:8px;'>Create Account</h2>", unsafe_allow_html=True)
            new_u = st.text_input("Username")
            new_e = st.text_input("Email")
            new_p = st.text_input("Password", type="password")
            
            st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
            if st.button("Sign Up", use_container_width=True):
                ok, err = sign_up_user(new_u, new_p, new_e)
                if ok: st.session_state["login_tab"] = "login"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("← Back to Login", use_container_width=True):
                st.session_state["login_tab"] = "login"; st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ── MAIN DASHBOARD ─────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:
    # Minimalist Header
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding: 2rem 0;">
        <h2 style="margin:0; font-size:24px;">✦ Dashboard</h2>
        <div style="background:rgba(255,255,255,0.05); padding:8px 16px; border-radius:20px; font-size:13px; border:1px solid rgba(255,255,255,0.1);">
            Logged in as <b>{st.session_state['username']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Simplified Stats
    jobs_list = load_jobs()
    total = len(jobs_list) if jobs_list else 0
    
    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val in zip([c1, c2, c3, c4], ["Total", "Interviews", "Offers", "Match"], [total, 0, 0, "—"]):
        with col:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); padding:20px; border-radius:16px;">
                <div style="color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:1px;">{lbl}</div>
                <div style="font-size:28px; font-weight:700; margin-top:8px; color:#ffffff;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if st.button("Sign Out"):
        st.session_state.clear(); st.rerun()
