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

/* ── Base & Background ── */
[data-testid="stAppViewContainer"] {
    background-color: #0f0a15 !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(122, 58, 120, 0.15) 0px, transparent 50%), 
        radial-gradient(at 100% 100%, rgba(90, 42, 136, 0.15) 0px, transparent 50%),
        linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; max-width: 1200px !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }

* { font-family: 'Inter', sans-serif !important; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ead8ee !important; letter-spacing: -0.02em; }
p, label { color: #c0a0c4 !important; font-weight: 500 !important; }

/* ── Glassmorphism Login Panels ── */
.login-left, .login-right {
    background: rgba(25, 15, 35, 0.65) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    border-radius: 24px !important;
    padding: 48px 40px !important;
    min-height: 540px;
}

/* ── Buttons ── */
.stButton > button {
    background: rgba(74, 34, 72, 0.5) !important;
    color: #ead8ee !important;
    border: 1px solid rgba(110, 56, 104, 0.5) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover { 
    background: #5a2a58 !important; 
    border-color: #f472b6 !important;
    box-shadow: 0 0 15px rgba(244, 114, 182, 0.2) !important;
}

/* Primary Action Buttons */
div[data-testid="stForm"] .stButton > button, 
.primary-btn > button {
    background: linear-gradient(135deg, #7a3a78, #5a2a88) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(122, 58, 120, 0.4) !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: rgba(20, 10, 25, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ead8ee !important;
    border-radius: 10px !important;
}
.stTextInput input:focus { border-color: #f472b6 !important; }

/* ── Metrics/Stat Cards ── */
.stat-card {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    transition: transform 0.2s ease;
}
.stat-card:hover { transform: translateY(-5px); border-color: rgba(244, 114, 182, 0.3); }

/* ── Job Row Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    background: rgba(255, 255, 255, 0.04) !important;
    border-color: rgba(244, 114, 182, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# ── PASSWORD STRENGTH HELPER ───────────────────────────────────────────────────

def password_strength(pw):
    if not pw:
        return None, None, None
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 12: score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pw): score += 1
    if score <= 1:   return "Weak",   "#ef4444", 20
    elif score == 2: return "Fair",   "#f97316", 40
    elif score == 3: return "Medium", "#eab308", 65
    elif score == 4: return "Strong", "#22c55e", 85
    else:            return "Very Strong", "#10b981", 100

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    st.markdown("<div style='height:4rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("""
        <div class="login-left">
            <div style="font-family:'Playfair Display'; font-size:32px; color:#f472b6; margin-bottom:8px;">✦ Job Tracker</div>
            <div style="color:#8a6888; font-size:14px; margin-bottom:40px; letter-spacing:1px; text-transform:uppercase;">AI Career Intelligence</div>
            <h1 style="font-size:48px; line-height:1.1; margin-bottom:20px;">Land Your<br>Dream Job.</h1>
            <p style="font-size:16px; color:#a080a4; line-height:1.6; max-width:400px;">
                The modern command center for your job search. Track applications and optimize your resume with AI-driven matching.
            </p>
            <div style="display:flex; gap:40px; margin-top:60px;">
                <div><div style="font-size:24px; font-weight:700; color:#f472b6;">98%</div><div style="font-size:12px; color:#6a4868;">Match Accuracy</div></div>
                <div><div style="font-size:24px; font-weight:700; color:#c084fc;">24/7</div><div style="font-size:12px; color:#6a4868;">Auto Tracking</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        tab = st.session_state["login_tab"]
        
        with st.container():
            st.markdown('<div class="login-right">', unsafe_allow_html=True)
            
            if tab == "login":
                st.markdown("<h2 style='text-align:center; margin-bottom:8px;'>Welcome Back</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; font-size:14px; margin-bottom:32px;'>Enter your credentials to access your dashboard</p>", unsafe_allow_html=True)
                
                u = st.text_input("Username", key="login_username", placeholder="john_doe")
                p = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
                
                col_a, col_b = st.columns(2)
                with col_a: st.checkbox("Remember me")
                with col_b: 
                    if st.button("Forgot password?", key="go_forgot", use_container_width=True):
                        st.session_state["login_tab"] = "forgot"; st.rerun()
                
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                if st.button("Sign In", key="do_login", use_container_width=True):
                    if login_user(u, p):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u
                        st.rerun()
                    else: st.error("Invalid credentials")
                
                st.markdown("<p style='text-align:center; margin-top:24px; font-size:13px;'>New here? <span style='color:#f472b6; cursor:pointer;'>Create an account below</span></p>", unsafe_allow_html=True)
                if st.button("Create Account →", key="go_signup", use_container_width=True):
                    st.session_state["login_tab"] = "signup"; st.rerun()

            elif tab == "signup":
                st.markdown("<h2>Create Account</h2>", unsafe_allow_html=True)
                new_u = st.text_input("Username", key="signup_u")
                new_e = st.text_input("Email", key="signup_e")
                new_p = st.text_input("Password", type="password", key="signup_p")
                
                if new_p:
                    lbl, clr, pct = password_strength(new_p)
                    st.markdown(f"<div style='font-size:11px; color:{clr}; text-align:right;'>Strength: {lbl}</div>", unsafe_allow_html=True)
                    st.progress(pct/100)
                
                confirm_p = st.text_input("Confirm Password", type="password", key="signup_c")
                agree = st.checkbox("I agree to the Terms of Service")
                
                if st.button("Sign Up", key="do_signup", use_container_width=True):
                    if new_p == confirm_p and agree:
                        ok, err = sign_up_user(new_u, new_p, new_e)
                        if ok: st.session_state["login_tab"] = "login"; st.rerun()
                        else: st.error(err)
                
                if st.button("← Back to Login", key="back_login_signup", use_container_width=True):
                    st.session_state["login_tab"] = "login"; st.rerun()

            elif tab == "forgot":
                st.markdown("<h2>Reset Password</h2>", unsafe_allow_html=True)
                res_u = st.text_input("Username", key="res_u")
                if st.button("Send Link", use_container_width=True):
                    send_password_reset(res_u)
                    st.success("Link sent!")
                if st.button("← Back", key="back_login_forgot", use_container_width=True):
                    st.session_state["login_tab"] = "login"; st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ── MAIN APP ───────────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:
    # Header
    h1, h2 = st.columns([6, 1])
    with h1:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:15px;">
            <span style="font-size:28px; font-family:'Playfair Display'; font-weight:700; color:#ead8ee;">✦ Job Tracker</span>
            <span style="background:rgba(244,114,182,0.1); color:#f472b6; padding:4px 12px; border-radius:20px; font-size:12px; border:1px solid rgba(244,114,182,0.2);">
                {st.session_state['username']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear(); st.rerun()

    st.divider()

    # Stats
    jobs_list = load_jobs()
    total = len(jobs_list) if jobs_list else 0
    
    s1, s2, s3, s4 = st.columns(4)
    stat_data = [("📋", total, "Total Jobs"), ("🗓️", 0, "Interviews"), ("✅", 0, "Offers"), ("🎯", "0%", "AI Score")]
    
    for col, icon, val, label in stat_data:
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:12px; color:#8a6888; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">{label}</div>
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span style="font-size:32px; font-weight:700; color:#ead8ee;">{val}</span>
                    <span style="font-size:24px; opacity:0.5;">{icon}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    # Add Job
    with st.expander("✨ Add New Application", expanded=False):
        c1, c2 = st.columns(2)
        with c1: comp = st.text_input("Company")
        with c2: pos = st.text_input("Position")
        url = st.text_input("Job URL")
        desc = st.text_area("Job Description", height=200)
        up_file = st.file_uploader("Upload Resume")
        
        if st.button("Save Application", use_container_width=True):
            save_job(company=comp, position=pos, description=desc, job_url=url)
            st.rerun()

    st.divider()

    # Jobs Table
    st.markdown("<h3>Active Applications</h3>", unsafe_allow_html=True)
    if jobs_list:
        df = pd.DataFrame(jobs_list)
        ratios = [1.5, 1.5, 1, 1.5, 1, 0.5, 0.5]
        
        # Table Header
        cols = st.columns(ratios)
        headers = ["COMPANY", "POSITION", "MATCH", "STATUS", "DATE", "CV", "DEL"]
        for col, h in zip(cols, headers):
            col.markdown(f"<div style='font-size:11px; color:#6a4868; font-weight:700;'>{h}</div>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            with st.container():
                c1, c2, c3, c4, c5, c6, c7 = st.columns(ratios, vertical_alignment="center")
                c1.markdown(f"**{row.get('company')}**")
                c2.markdown(row.get('position'))
                c3.markdown(f"<span style='color:#f472b6;'>{row.get('match_score', '—')}</span>", unsafe_allow_html=True)
                
                with c4:
                    st.selectbox("Status", ["Applied", "Interview", "Offer", "Rejected"], key=f"stat_{row['id']}", label_visibility="collapsed")
                
                c5.markdown(str(row.get('created_at'))[:10])
                
                with c6:
                    st.button("📄", key=f"cv_{row['id']}")
                with c7:
                    if st.button("🗑", key=f"del_{row['id']}"):
                        delete_job(row['id']); st.rerun()
    else:
        st.info("No applications yet. Click 'Add New Application' to start tracking.")
