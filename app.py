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

# ── CONFIGURATION ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Tracker | Pipeline",
    page_icon="💜",
    layout="wide"
)

# ── SESSION STATE ──────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""
if "match_data" not in st.session_state:
    st.session_state["match_data"] = None
if "resume_txt" not in st.session_state:
    st.session_state["resume_txt"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login"

# ── CYBER-PLUM CSS ────────────────────────────────────────────────────────
CYBER_PLUM_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code:wght@400;500&display=swap');

/* Main Background Gradient */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2d1b2e 0%, #1f1a35 100%) !important;
    background-attachment: fixed !important;
}

/* Lighting Effect Overlay */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% -20%, rgba(244, 114, 182, 0.15), transparent 80%);
    pointer-events: none;
    z-index: 0;
}

/* Global Text Colors */
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
    color: #e8c8d8 !important;
}

/* Stat Cards Styling */
.stat-box {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(244, 114, 182, 0.2);
    border-radius: 16px;
    padding: 24px;
    text-align: left;
    backdrop-filter: blur(10px);
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

/* Job Row Styling (Glassmorphism) */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(45, 27, 46, 0.4) !important;
    border: 1px solid rgba(244, 114, 182, 0.1) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    margin-bottom: 8px !important;
    transition: all 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(244, 114, 182, 0.4) !important;
    background: rgba(61, 31, 58, 0.6) !important;
    transform: translateY(-2px);
}

/* Button Customization */
.stButton > button {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #f9a8d4 !important;
    border: 1px solid rgba(244, 114, 182, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: 0.2s;
}
.stButton > button:hover {
    background: rgba(244, 114, 182, 0.2) !important;
    border-color: #f472b6 !important;
    color: white !important;
}

/* Headers */
h1, h2, h3 { color: #fde8f0 !important; font-weight: 700 !important; }
p { color: #d1d5db !important; }
</style>
"""
st.markdown(CYBER_PLUM_STYLE, unsafe_allow_html=True)

# ── AUTHENTICATION PAGE ────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Job Tracker")
        st.caption("Secure Career Pipeline Management")
        
        # Authentication Selector (Security Feature)
        auth_choice = st.radio("Mode", ["Login", "Sign Up", "Forgot Password"], horizontal=True, label_visibility="collapsed")
        
        with st.container(border=True):
            if auth_choice == "Login":
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.button("Sign In", use_container_width=True):
                    if login_user(u, p):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u
                        st.rerun()
                    else:
                        st.error("Authentication failed. Check your credentials.")

            elif auth_choice == "Sign Up":
                new_u = st.text_input("Choose Username")
                new_p = st.text_input("Choose Password", type="password")
                if st.button("Create Account", use_container_width=True):
                    if sign_up_user(new_u, new_p):
                        st.success("Account created! You can now log in.")
                    else:
                        st.error("Username already exists.")

            elif auth_choice == "Forgot Password":
                reset_u = st.text_input("Username to Reset")
                if st.button("Request Password Reset", use_container_width=True):
                    if send_password_reset(reset_u):
                        st.success("Reset instructions sent to your account's email.")
                    else:
                        st.error("Username not found.")

# ── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if st.session_state["logged_in"]:
    # Top Header
    head_left, head_right = st.columns([5, 1])
    with head_left:
        st.title("My Pipeline")
        st.caption(f"Authenticated as {st.session_state['username']}")
    with head_right:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── KPI STATS CARDS ──
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
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#c084fc">74%</div><div class="stat-label">Avg Match Score</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ADD NEW APPLICATION (Functional Integration) ──
    with st.expander("➕ Initialize New Application Entry"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name")
        pos = c2.text_input("Target Position")
        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Execute AI Auto-Fill"):
            if url_in:
                with st.spinner("AI is analyzing job listing..."):
                    raw_text = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw_text)
                    st.rerun()

        final_desc = st.text_area("Job Description Data", value=st.session_state["formatted_desc"], height=200)

        ac1, ac2 = st.columns(2)
        up_file = ac1.file_uploader("Versioned Resume Upload", type=["pdf", "docx", "txt"])
        if up_file: 
            st.session_state["resume_txt"] = extract_text_from_upload(up_file)
        
        applied_date = ac2.date_input("Application Date", value=datetime.now())

        if st.button("🔍 Run Resume Match Analysis"):
            if final_desc and st.session_state["resume_txt"]:
                with st.spinner("Calculating match score..."):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
        
        if st.session_state["match_data"]:
            st.markdown(f"**AI Evaluation:** {st.session_state['match_data'].get('score', '0')}/10")

        if st.button("💾 Finalize & Save to Database", use_container_width=True):
            res_url = upload_resume(up_file, st.session_state["username"]) if up_file else None
            score = st.session_state["match_data"].get("score", "N/A") if st.session_state["match_data"] else "N/A"
            
            if save_job(company=comp, position=pos, description=final_desc, job_url=url_in, 
                        resume_url=res_url, match_score=score, applied_date=applied_date):
                st.session_state["formatted_desc"] = ""
                st.session_state["match_data"] = None
                st.success("Entry Secured in Pipeline.")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PIPELINE ACTIVITY TABLE ──
    if not df.empty:
        # Table Header
        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
        for col, label in zip([h1, h2, h3, h4, h5, h6, h7], ["COMPANY", "ROLE", "MATCH", "STATUS", "DATE", "FILES", "DEL"]):
            col.caption(label)

        for _, row in df.iterrows():
            with st.container():
                r1, r2, r3, r4, r5, r6, r7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
                
                r1.markdown(f"**{row['company']}**")
                r2.markdown(f"<span style='color:#f9a8d4'>{row['position']}</span>", unsafe_allow_html=True)
                r3.markdown(f"**{row.get('match_score', 'N/A')}**")
                
                with r4:
                    status_opts = ["📝 Applied", "📅 Interview", "✅ Offer", "❌ Rejected"]
                    curr_s = row.get('status', '📝 Applied')
                    new_s = st.selectbox("S", status_opts, 
                                         index=status_opts.index(curr_s) if curr_s in status_opts else 0, 
                                         key=f"s_{row['id']}", label_visibility="collapsed")
                    if new_s != curr_s:
                        update_job_full(row['id'], {"status": new_s})
                        st.rerun()

                r5.write(str(row.get('created_at'))[:10])
                
                with r6:
                    res_link = row.get('resume_link')
                    if res_link: st.link_button("📄", res_link)
                
                if r7.button("🗑️", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                    st.rerun()
    else:
        st.info("Your pipeline is currently empty. Initialize an application above.")
