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
    page_title="CareerFlow | Professional Job Tracker",
    page_icon="💼",
    layout="wide"
)

# ── PROFESSIONAL GRADIENT THEME CSS ──────────────────────────────────────────
PROFESSIONAL_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* High-End Gradient Background */
[data-testid="stAppViewContainer"] {
    background-color: #0f172a !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%), 
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.15) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(67, 56, 202, 0.1) 0px, transparent 50%),
        radial-gradient(at 0% 100%, rgba(30, 58, 138, 0.1) 0px, transparent 50%) !important;
    background-attachment: fixed !important;
}

/* Global Font Override */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
}

h1, h2, h3 {
    color: #f8fafc !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* Transparent Header */
[data-testid="stHeader"] { background: transparent !important; }

/* Stat Cards with subtle Glassmorphism */
.stat-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* Job Row Containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(30, 41, 59, 0.5) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin-bottom: 0.75rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(99, 102, 241, 0.5) !important;
    background: rgba(30, 41, 59, 0.8) !important;
    transform: translateY(-3px);
    box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.3) !important;
}

/* Professional Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
}

.stButton > button:hover {
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4) !important;
    transform: translateY(-1px);
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

/* Dividers */
hr { border-color: rgba(255, 255, 255, 0.05) !important; }

</style>
"""

st.markdown(PROFESSIONAL_STYLE, unsafe_allow_html=True)

# Session State Initialization
for key in ["logged_in", "formatted_desc", "match_data", "resume_txt", "username"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else None
if st.session_state["formatted_desc"] is None: st.session_state["formatted_desc"] = ""

# ── AUTHENTICATION ──────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("CareerFlow")
        st.write("Professional Job Pipeline")
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"], st.session_state["username"] = True, u
                    st.rerun()
                else: st.error("Invalid credentials")
        with tab2:
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            if st.button("Create Account", use_container_width=True):
                if sign_up_user(new_u, new_p): st.success("Account Ready")

# ── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if st.session_state["logged_in"]:
    header_col, action_col = st.columns([4, 1])
    with header_col:
        st.caption(f"CONNECTED AS {st.session_state['username'].upper()}")
        st.title("Career Pipeline")
    with action_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── STATS ──
    jobs = load_jobs()
    df = pd.DataFrame(jobs) if jobs else pd.DataFrame()
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-card"><h3>{len(df)}</h3><p style="color:#94a3b8;margin:0">Active Apps</p></div>', unsafe_allow_html=True)
    with s2:
        ints = len(df[df['status'].str.contains("Interview", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-card"><h3>{ints}</h3><p style="color:#94a3b8;margin:0">Interviews</p></div>', unsafe_allow_html=True)
    with s3:
        offs = len(df[df['status'].str.contains("Offer", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-card"><h3 style="color:#10b981">{offs}</h3><p style="color:#94a3b8;margin:0">Offers</p></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-card"><h3>—</h3><p style="color:#94a3b8;margin:0">Avg Score</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── NEW APPLICATION ──
    with st.expander("＋ LOG NEW APPLICATION"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name")
        pos = c2.text_input("Position Title")
        url = st.text_input("Job URL (Optional)")
        
        if st.button("✨ Auto-Fill with AI"):
            if url:
                with st.spinner("Parsing job details..."):
                    raw = scrape_job_link(url)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)
        
        desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=180)
        
        if st.button("Save to Pipeline", use_container_width=True):
            save_job(company=comp, position=pos, description=desc, job_url=url, applied_date=datetime.now())
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PIPELINE TABLE ──
    if not df.empty:
        # Simple sorting
        df = df.sort_values(by="id", ascending=False)
        
        # Header Row
        h1, h2, h3, h4, h5 = st.columns([1.5, 2, 1.2, 1, 0.4])
        h1.caption("COMPANY")
        h2.caption("POSITION")
        h3.caption("STATUS")
        h4.caption("DATE")
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
    else:
        st.info("Your pipeline is empty. Add your first application above.")
