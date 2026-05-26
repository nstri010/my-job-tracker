import streamlit as st
import pandas as pd
from datetime import datetime

from storage import (
    load_jobs, save_job, delete_job, sign_up_user, 
    login_user, upload_resume, update_job_full
)
from utils import (
    scrape_job_link, clean_description_with_ai, 
    get_ai_match_feedback, extract_text_from_upload
)

st.set_page_config(
    page_title="CareerFlow | Master Your Search",
    page_icon="🟢",
    layout="wide"
)

# ── RAEDJIN INSPIRED CSS ──────────────────────────────────────────────────
RAEDJIN_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code:wght@400;500&display=swap');

/* High-End Background */
[data-testid="stAppViewContainer"] {
    background-color: #000000 !important;
    background-image: radial-gradient(circle at 20% 30%, rgba(16, 185, 129, 0.08) 0%, transparent 40%) !important;
}

/* Global Font */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
    color: #94a3b8 !important;
}

/* Marketing Column (Left Side) */
.marketing-title {
    font-size: 3rem !important;
    font-weight: 800 !important;
    color: white !important;
    line-height: 1.1;
    margin-bottom: 1rem;
}
.neon-text {
    color: #10b981 !important;
    text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

/* Terminal Component */
.terminal-card {
    background: #0a0a0a;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px;
    font-family: 'Fira Code', monospace;
    font-size: 0.9rem;
    color: #10b981;
    margin-top: 2rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}

/* Sign-In Box (Right Side) */
[data-testid="stExpander"], .stTabs, div.stButton > button {
    border-radius: 8px !important;
}

/* Inputs styling */
.stTextInput input {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    color: white !important;
    padding: 12px !important;
}

/* Main Action Button */
div.stButton > button {
    background-color: #10b981 !important;
    color: #000 !important;
    font-weight: 700 !important;
    width: 100%;
    border: none !important;
    padding: 10px !important;
    transition: all 0.2s;
}
div.stButton > button:hover {
    background-color: #34d399 !important;
    transform: translateY(-1px);
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
}

/* Dashboard Cards */
.stat-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 1.5rem;
}

</style>
"""

st.markdown(RAEDJIN_STYLE, unsafe_allow_html=True)

# Session State Initialization
for key in ["logged_in", "formatted_desc", "match_data", "resume_txt", "username"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else None

# ── AUTHENTICATION PAGE (SPLIT LAYOUT) ──────────────────────────────────────
if not st.session_state["logged_in"]:
    left_col, right_col = st.columns([1.2, 1])
    
    with left_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div class="marketing-title">Organize Your Career <br><span class="neon-text">The Pro Way</span></div>', unsafe_allow_html=True)
        st.write("Join the elite league of organized job seekers. Master your pipeline through AI-driven tracking and resume matching.")
        
        # Terminal Visual
        st.markdown("""
        <div class="terminal-card">
            <span style="color:#ef4444">●</span> <span style="color:#fbbf24">●</span> <span style="color:#10b981">●</span><br>
            <span style="color:#6366f1">$</span> ./start_career_growth.sh<br>
            <span style="color:#94a3b8">[*] Initializing AI match engine...</span><br>
            <span style="color:#94a3b8">[*] Loading resume templates...</span><br>
            <span style="color:#10b981">[v] Welcome to CareerFlow!</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("📈 **50K+** Apps Tracked &nbsp; ⚡ **200ms** AI Processing")

    with right_col:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        with st.container():
            st.subheader("Welcome Back")
            st.caption("Sign in to continue your journey")
            
            tab1, tab2 = st.tabs(["Sign In", "Register"])
            
            with tab1:
                u = st.text_input("Username or Email", placeholder="your_name")
                p = st.text_input("Password", type="password", placeholder="••••••••")
                st.markdown('<p style="text-align:right; font-size:0.8rem; color:#10b981; cursor:pointer;">Forgot password?</p>', unsafe_allow_html=True)
                if st.button("Sign In", key="login_btn"):
                    if login_user(u, p):
                        st.session_state["logged_in"], st.session_state["username"] = True, u
                        st.rerun()
                    else: st.error("Invalid credentials")
            
            with tab2:
                new_u = st.text_input("Choose Username")
                new_p = st.text_input("Secure Password", type="password")
                if st.button("Create Account", key="reg_btn"):
                    if sign_up_user(new_u, new_p): st.success("Success! Please log in.")
            
            st.markdown("<br><center><p style='font-size:0.8rem;'>Don't have an account? <span style='color:#10b981;'>Sign up for free</span></p></center>", unsafe_allow_html=True)

# ── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if st.session_state["logged_in"]:
    header_col, action_col = st.columns([4, 1])
    with header_col:
        st.markdown(f'<p style="color:#10b981; font-weight:700; margin:0; letter-spacing:1px;">DASHBOARD_ACCESS_GRANTED</p>', unsafe_allow_html=True)
        st.title("Career Pipeline")
    with action_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()

    # ── STATS ──
    jobs = load_jobs()
    df = pd.DataFrame(jobs) if jobs else pd.DataFrame()
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-card"><h2 style="margin:0">{len(df)}</h2><p style="margin:0; font-size:0.8rem; color:#64748b">ACTIVE_APPLICATIONS</p></div>', unsafe_allow_html=True)
    with s2:
        ints = len(df[df['status'].str.contains("Interview", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-card"><h2 style="margin:0">{ints}</h2><p style="margin:0; font-size:0.8rem; color:#64748b">INTERVIEWS_SECURED</p></div>', unsafe_allow_html=True)
    with s3:
        offs = len(df[df['status'].str.contains("Offer", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-card"><h2 style="margin:0; color:#10b981">{offs}</h2><p style="margin:0; font-size:0.8rem; color:#64748b">OFFERS_RECEIVED</p></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-card"><h2 style="margin:0">15+</h2><p style="margin:0; font-size:0.8rem; color:#64748b">SKILL_MATCHES</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── NEW APPLICATION ──
    with st.expander("＋ INITIALIZE_NEW_APPLICATION"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Target Company")
        pos = c2.text_input("Role Title")
        url = st.text_input("Job URL Source")
        
        if st.button("⚡ EXECUTE_AI_PARSE"):
            if url:
                with st.spinner("Analyzing target..."):
                    raw = scrape_job_link(url)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)
        
        desc = st.text_area("Job Description Data", value=st.session_state.get("formatted_desc", ""), height=150)
        
        if st.button("SAVE_RECORD", use_container_width=True):
            save_job(company=comp, position=pos, description=desc, job_url=url, applied_date=datetime.now())
            st.rerun()

    # ── PIPELINE TABLE ──
    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        # Header Row
        h1, h2, h3, h4, h5 = st.columns([1.5, 2, 1.2, 1, 0.4])
        h1.caption("ENTITY")
        h2.caption("OPERATIONAL_ROLE")
        h3.caption("STATUS_LEVEL")
        h4.caption("TIMESTAMP")
        h5.caption("")

        for _, row in df.iterrows():
            with st.container(border=True):
                r1, r2, r3, r4, r5 = st.columns([1.5, 2, 1.2, 1, 0.4])
                r1.write(f"**{row['company']}**")
                r2.write(row['position'])
                
                with r3:
                    new_status = st.selectbox("Status", 
                        ["📝 Applied", "📨 Contacted", "📅 Interview", "✅ Offer", "❌ Rejected"],
                        index=0, key=f"stat_{row['id']}", label_visibility="collapsed")
                    if new_status != row.get('status'):
                        update_job_full(row['id'], {"status": new_status})

                r4.write(str(row.get('applied_date'))[:10])
                
                if r5.button("🗑️", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                    st.rerun()
