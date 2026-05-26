
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
    page_title="Job Tracker | Pipeline",
    page_icon="💜",
    layout="wide"
)

# ── CYBER-PLUM GRADIENT THEME ──────────────────────────────────────────────
CYBER_PLUM_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Dynamic Pink to Purple Gradient Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2d1b2e 0%, #1f1a35 100%) !important;
    background-attachment: fixed !important;
}

/* Subtle overlay to give it that "Screenshot" depth */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% -20%, rgba(244, 114, 182, 0.15), transparent 80%);
    pointer-events: none;
}

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
    color: #e8c8d8 !important;
}

/* Stat Cards (Top Row) */
.stat-box {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(244, 114, 182, 0.2);
    border-radius: 16px;
    padding: 24px;
    text-align: left;
}
.stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
}
.stat-label {
    color: #f9a8d4;
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 4px;
}

/* Job Rows - Exactly like the screenshot */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(45, 27, 46, 0.6) !important;
    border: 1px solid rgba(244, 114, 182, 0.15) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    margin-bottom: 10px !important;
    transition: transform 0.2s, border-color 0.2s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(244, 114, 182, 0.5) !important;
    background: rgba(61, 31, 58, 0.8) !important;
}

/* Status Badges - Pill Style */
.status-pill {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}

/* Buttons and UI Elements */
.stButton > button {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #f9a8d4 !important;
    border: 1px solid rgba(244, 114, 182, 0.3) !important;
    border-radius: 8px !important;
}
.stButton > button:hover {
    background: rgba(244, 114, 182, 0.2) !important;
    border-color: #f472b6 !important;
}

/* Typography Overrides */
h1, h2, h3 { color: #fde8f0 !important; font-weight: 700 !important; }
p { color: #d1d5db !important; }

</style>
"""

st.markdown(CYBER_PLUM_STYLE, unsafe_allow_html=True)

# Session State
for key in ["logged_in", "username"]:
    if key not in st.session_state: st.session_state[key] = False

# Sign Out Button
    if st.button("Sign Out"):
        st.session_state.clear()
        st.rerun()
        
# ── AUTHENTICATION ──────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Job Tracker")
        st.caption("This website uses AI which may make errors. Double-check results.")
        
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"], st.session_state["username"] = True, u
                    st.rerun()

# ── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if st.session_state["logged_in"]:
    st.title("Job Tracker")
    st.caption("This website uses AI which may make errors. Make sure to double-check all results.")

    # ── STATS CARDS ──
    jobs = load_jobs()
    df = pd.DataFrame(jobs) if jobs else pd.DataFrame()
    
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{len(df)}</div><div class="stat-label">Applications</div></div>', unsafe_allow_html=True)
    with s2:
        ints = len(df[df['status'].str.contains("Interview", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#f472b6">{ints}</div><div class="stat-label">Interviews</div></div>', unsafe_allow_html=True)
    with s3:
        offs = len(df[df['status'].str.contains("Offer", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#fbbf24">{offs}</div><div class="stat-label">Offers</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#c084fc">74%</div><div class="stat-label">Avg match</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PIPELINE TABLE ──
    if not df.empty:
        # Header Row
        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
        cols = ["COMPANY", "POSITION", "MATCH", "STATUS", "DATE", "CV", "DEL"]
        for col, label in zip([h1, h2, h3, h4, h5, h6, h7], cols):
            col.caption(label)

        for _, row in df.iterrows():
            with st.container(border=True):
                r1, r2, r3, r4, r5, r6, r7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
                
                r1.markdown(f"**{row['company']}**")
                r2.markdown(f"<span style='color:#f9a8d4'>{row['position']}</span>", unsafe_allow_html=True)
                r3.markdown(f"**{row.get('match_score', '90')}**")
                
                with r4:
                    # Status badges with pill styling
                    status = row.get('status', '📝 Applied')
                    st.selectbox("Status", 
                        ["📝 Applied", "📅 Interview", "✅ Offer", "❌ Rejected"],
                        index=0, key=f"s_{row['id']}", label_visibility="collapsed")

                r5.write(str(row.get('applied_date'))[:10])
                
                r6.button("📄", key=f"cv_{row['id']}")
                if r7.button("🗑️", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                    st.rerun()
    else:
        st.info("No applications yet. Add one to get started!")
