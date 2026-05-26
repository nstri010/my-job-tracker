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

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2d1b2e 0%, #1f1a35 100%) !important;
    background-attachment: fixed !important;
}

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

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(45, 27, 46, 0.6) !important;
    border: 1px solid rgba(244, 114, 182, 0.15) !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    margin-bottom: 10px !important;
}

.stButton > button {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #f9a8d4 !important;
    border: 1px solid rgba(244, 114, 182, 0.3) !important;
    border-radius: 8px !important;
}

h1, h2, h3 { color: #fde8f0 !important; font-weight: 700 !important; }
</style>
"""
st.markdown(CYBER_PLUM_STYLE, unsafe_allow_html=True)

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

# ── AUTHENTICATION ──────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Job Tracker")
        with st.container(border=True):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()

# ── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if st.session_state["logged_in"]:
    head_col, signout_col = st.columns([5, 1])
    with head_col:
        st.title("Job Tracker")
    with signout_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── STATS ──
    jobs = load_jobs()
    df = pd.DataFrame(jobs) if jobs else pd.DataFrame()
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.markdown(f'<div class="stat-box"><div class="stat-number">{len(df)}</div><div class="stat-label">Applications</div></div>', unsafe_allow_html=True)
    with s2: 
        ints = len(df[df['status'].str.contains("Interview", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#f472b6">{ints}</div><div class="stat-label">Interviews</div></div>', unsafe_allow_html=True)
    with s3:
        offs = len(df[df['status'].str.contains("Offer", na=False)]) if not df.empty else 0
        st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#fbbf24">{offs}</div><div class="stat-label">Offers</div></div>', unsafe_allow_html=True)
    with s4: st.markdown(f'<div class="stat-box"><div class="stat-number" style="color:#c084fc">74%</div><div class="stat-label">Avg match</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ADD NEW APPLICATION (THE MISSING PART) ──
    with st.expander("➕ Add New Application"):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name")
        pos = c2.text_input("Position Title")
        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill Details"):
            if url_in:
                with st.spinner("Scraping..."):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)

        final_desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=200)

        col1, col2 = st.columns(2)
        up_file = col1.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
        if up_file: st.session_state["resume_txt"] = extract_text_from_upload(up_file)
        applied_date = col2.date_input("Date Applied")

        if st.button("🔍 Scan Resume"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Analyzing Match..."):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])

        if st.session_state["match_data"]:
            st.success(f"Score: {st.session_state['match_data'].get('score', 'N/A')}")

        if st.button("💾 Save Application", use_container_width=True):
            res_url = upload_resume(up_file, st.session_state["username"]) if up_file else None
            score = st.session_state["match_data"].get("score", "N/A") if st.session_state["match_data"] else "N/A"
            
            if save_job(company=comp, position=pos, description=final_desc, job_url=url_in, 
                        resume_url=res_url, match_score=score, applied_date=applied_date):
                st.session_state["formatted_desc"] = ""
                st.session_state["match_data"] = None
                st.success("Saved!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PIPELINE TABLE ──
    if not df.empty:
        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
        for col, label in zip([h1, h2, h3, h4, h5, h6, h7], ["COMPANY", "POSITION", "MATCH", "STATUS", "DATE", "CV", "DEL"]):
            col.caption(label)

        for _, row in df.iterrows():
            with st.container(border=True):
                r1, r2, r3, r4, r5, r6, r7 = st.columns([1.5, 1.5, 0.8, 1.2, 1, 0.5, 0.5])
                r1.markdown(f"**{row['company']}**")
                r2.markdown(f"<span style='color:#f9a8d4'>{row['position']}</span>", unsafe_allow_html=True)
                r3.markdown(f"**{row.get('match_score', 'N/A')}**")
                
                with r4:
                    opts = ["📝 Applied", "📅 Interview", "✅ Offer", "❌ Rejected"]
                    curr = row.get('status', '📝 Applied')
                    new_s = st.selectbox("S", opts, index=opts.index(curr) if curr in opts else 0, key=f"s_{row['id']}", label_visibility="collapsed")
                    if new_s != curr:
                        update_job_full(row['id'], {"status": new_s})
                        st.rerun()

                r5.write(str(row.get('created_at'))[:10])
                if r6.button("📄", key=f"cv_{row['id']}"): pass
                if r7.button("🗑️", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                    st.rerun()
    else:
        st.info("No applications yet.")
