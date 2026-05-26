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

/* ── Base & Terminal Background ── */
[data-testid="stAppViewContainer"] {
    background-color: #0d0d12 !important;
    /* Grid Pattern Overlay */
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        radial-gradient(circle at 20% 30%, rgba(244, 114, 182, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 80% 70%, rgba(192, 132, 252, 0.08) 0%, transparent 40%) !important;
    background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100% !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; max-width: 1100px !important; }

/* ── Typography ── */
* { font-family: 'Inter', sans-serif !important; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ffffff !important; }
p, label { color: #94a3b8 !important; font-weight: 400 !important; }

/* ── Glassmorphism Login Panels ── */
.login-left, .login-right {
    background: rgba(15, 15, 20, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 24px !important;
    padding: 50px 40px !important;
    height: 100%;
    min-height: 550px;
}

/* ── Buttons (Terminal Style) ── */
.stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover { 
    background: rgba(244, 114, 182, 0.1) !important; 
    border-color: #f472b6 !important;
}

/* Primary Action Buttons */
div[data-testid="stForm"] .stButton > button, 
.primary-btn > button {
    background: #f472b6 !important;
    color: #000000 !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
.stTextInput input:focus { border-color: #f472b6 !important; }

/* ── Stat Cards ── */
.stat-card {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 24px !important;
}

/* ── Row Cards (Dashboard) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── PASSWORD STRENGTH HELPER ───────────────────────────────────────────────────

def password_strength(pw):
    if not pw: return None, None, None
    score = 0
    if len(pw) >= 8: score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()" for c in pw): score += 1
    
    if score <= 1: return "Weak", "#ef4444", 25
    elif score == 2: return "Medium", "#eab308", 60
    else: return "Strong", "#22c55e", 100

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    st.markdown("<div style='height:4rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown(f"""
        <div class="login-left">
            <div style="font-size:32px; color:#f472b6; margin-bottom:8px;">✦ Job Tracker</div>
            <div style="color:#64748b; font-size:12px; margin-bottom:40px; letter-spacing:2px; text-transform:uppercase;">AI Career Intelligence</div>
            <h1 style="font-size:56px; line-height:1.1; margin-bottom:24px;">Land Your<br>Dream Job.</h1>
            <p style="font-size:16px; color:#94a3b8; line-height:1.6; max-width:400px; margin-bottom:60px;">
                The modern command center for your job search. Track applications and optimize your resume with AI-driven matching.
            </p>
            <div style="display:flex; gap:60px;">
                <div><div style="font-size:28px; font-weight:700; color:#f472b6;">98%</div><div style="font-size:12px; color:#64748b;">Match Accuracy</div></div>
                <div><div style="font-size:28px; font-weight:700; color:#c084fc;">24/7</div><div style="font-size:12px; color:#64748b;">Auto Tracking</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)
        tab = st.session_state["login_tab"]
        
        if tab == "login":
            st.markdown("<h2 style='margin-bottom:8px;'>Welcome Back</h2>", unsafe_allow_html=True)
            st.markdown("<p style='margin-bottom:32px;'>Enter your credentials to access your dashboard</p>", unsafe_allow_html=True)
            
            u = st.text_input("Username", key="login_username")
            p = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Sign In", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else: st.error("Invalid credentials")
            
            st.markdown("<p style='text-align:center; margin-top:24px;'>New here? <span style='color:#f472b6;'>Create an account</span></p>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True):
                st.session_state["login_tab"] = "signup"; st.rerun()

        elif tab == "signup":
            st.markdown("<h2>Create Account</h2>", unsafe_allow_html=True)
            new_u = st.text_input("Username")
            new_e = st.text_input("Email")
            new_p = st.text_input("Password", type="password")
            
            if new_p:
                lbl, clr, pct = password_strength(new_p)
                st.progress(pct/100)
                st.markdown(f"<div style='color:{clr}; font-size:12px; text-align:right;'>{lbl}</div>", unsafe_allow_html=True)
            
            if st.button("Sign Up", use_container_width=True):
                ok, err = sign_up_user(new_u, new_p, new_e)
                if ok: st.session_state["login_tab"] = "login"; st.rerun()
                else: st.error(err)
            
            if st.button("← Back to Login", use_container_width=True):
                st.session_state["login_tab"] = "login"; st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ── MAIN APP ───────────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:
    # Dashboard Header
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
        <div>
            <h2 style="margin:0;">Dashboard</h2>
            <p style="margin:0;">Welcome back, {st.session_state['username']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    jobs_list = load_jobs()
    total = len(jobs_list) if jobs_list else 0
    
    s1, s2, s3, s4 = st.columns(4)
    for col, label, val, icon in zip([s1, s2, s3, s4], 
                                    ["Total Jobs", "Interviews", "Offers", "Avg Match"],
                                    [total, 0, 0, "0%"],
                                    ["📋", "🗓️", "✅", "🎯"]):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="color:#64748b; font-size:12px; text-transform:uppercase;">{label}</div>
                <div style="font-size:32px; font-weight:700; margin:8px 0;">{val}</div>
                <div style="opacity:0.3; font-size:20px;">{icon}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Jobs Table
    if jobs_list:
        df = pd.DataFrame(jobs_list)
        for _, row in df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                c1.markdown(f"**{row.get('company')}**")
                c2.markdown(row.get('position'))
                c3.markdown(f"<span style='color:#f472b6;'>{row.get('match_score', '—')}</span>", unsafe_allow_html=True)
                if c4.button("🗑", key=f"del_{row['id']}"):
                    delete_job(row['id']); st.rerun()
    else:
        st.info("No applications yet. Start tracking to see them here.")
