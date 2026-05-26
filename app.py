import streamlit as st
import pandas as pd
from datetime import datetime

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600;700&display=swap');

/* Base Terminal Background */
[data-testid="stAppViewContainer"] {
    background-color: #0d0d12 !important;
    background-image: 
        radial-gradient(circle at 15% 25%, rgba(244, 114, 182, 0.12) 0%, transparent 35%),
        radial-gradient(circle at 85% 75%, rgba(192, 132, 252, 0.1) 0%, transparent 40%),
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 45px 45px, 45px 45px !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 6rem !important; max-width: 1200px !important; }

/* ── Glassmorphism Panels ── */
.login-panel {
    background: rgba(18, 18, 24, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 24px !important;
    padding: 50px 45px !important;
    min-height: 600px;
}

/* Typography */
* { font-family: 'Inter', sans-serif !important; }
h1, h2 { font-family: 'Playfair Display', serif !important; color: #ffffff !important; margin-bottom: 1rem !important; }
p, label { color: #94a3b8 !important; font-size: 14px !important; }

/* ── THE FIX: Styling the Column itself as the Panel ── */
[data-testid="column"] > div {
    background: rgba(18, 18, 24, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 24px !important;
    padding: 50px 40px !important;
    min-height: 580px !important;
    display: flex;
    flex-direction: column;
}

/* Input Fields */
.stTextInput input {
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 12px !important;
}

/* Buttons */
.stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    height: 48px !important;
    font-weight: 600 !important;
    margin-top: 10px !important;
}
.stButton > button:hover { 
    border-color: #f472b6 !important;
    background: rgba(244, 114, 182, 0.1) !important;
}

</style>
""", unsafe_allow_html=True)

# ── LOGIN PAGE UI ──
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    l_col, r_col = st.columns([1.1, 1], gap="large")

    with l_col:
        # Header Section
        st.markdown('<div style="font-size:32px; color:#f472b6; font-family:\'Playfair Display\'">✦ Job Tracker</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#64748b; font-size:11px; letter-spacing:2px; text-transform:uppercase; margin-bottom:40px;">AI Career Intelligence</div>', unsafe_allow_html=True)
        
        st.markdown('<h1 style="font-size:56px; line-height:1.1;">Land Your<br>Dream Job.</h1>', unsafe_allow_html=True)
        st.markdown('<p style="line-height:1.6; max-width:380px; margin-bottom:40px;">The modern command center for your job search. Track applications and optimize your resume with AI-driven matching.</p>', unsafe_allow_html=True)
        
        # Stats Row (using simple markdown to avoid nested column styling issues)
        st.markdown("""
        <div style="display:flex; gap:50px; margin-top:auto;">
            <div><div style="font-size:32px; font-weight:700; color:#f472b6;">98%</div><div style="font-size:12px; color:#64748b;">Match Accuracy</div></div>
            <div><div style="font-size:32px; font-weight:700; color:#c084fc;">24/7</div><div style="font-size:12px; color:#64748b;">Auto Tracking</div></div>
        </div>
        """, unsafe_allow_html=True)

    with r_col:
        if "login_tab" not in st.session_state:
            st.session_state["login_tab"] = "login"
            
        if st.session_state["login_tab"] == "login":
            st.markdown("<h2>Welcome Back</h2>", unsafe_allow_html=True)
            st.markdown("<p>Enter your credentials to access your dashboard</p>", unsafe_allow_html=True)
            
            st.text_input("Username", key="login_u")
            st.text_input("Password", type="password", key="login_p")
            
            if st.button("Sign In", use_container_width=True):
                st.session_state["logged_in"] = True
                st.rerun()
            
            st.markdown("<p style='text-align:center; margin-top:20px;'>New here?</p>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True):
                st.session_state["login_tab"] = "signup"
                st.rerun()

        else: # Signup View
            st.markdown("<h2>Create Account</h2>", unsafe_allow_html=True)
            st.markdown("<p>Join the AI-powered career revolution</p>", unsafe_allow_html=True)
            
            st.text_input("Username", key="reg_u")
            st.text_input("Email", key="reg_e")
            st.text_input("Password", type="password", key="reg_p")
            
            if st.button("Sign Up", use_container_width=True):
                st.session_state["login_tab"] = "login"
                st.rerun()
            
            if st.button("← Back to Login", use_container_width=True):
                st.session_state["login_tab"] = "login"
                st.rerun()
