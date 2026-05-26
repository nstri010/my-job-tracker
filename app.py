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

st.set_page_config(page_title="Career Hunt HQ", layout="wide")

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ═══════════════════════════════
   BASE
═══════════════════════════════ */
* { font-family: 'Inter', sans-serif !important; caret-color: transparent !important; box-sizing: border-box; }
input, textarea { caret-color: white !important; }

[data-testid="stAppViewContainer"] {
    background-color: #09090b !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 10% 0%, rgba(244,114,182,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 100%, rgba(139,92,246,0.06) 0%, transparent 60%) !important;
    background-size: 100% 100%, 100% 100% !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 3.5rem !important; max-width: 1200px !important; }

/* ═══════════════════════════════
   TYPOGRAPHY
═══════════════════════════════ */
h1 { font-size: 1.9rem !important; font-weight: 800 !important; color: #fafafa !important; letter-spacing: -0.04em !important; margin-bottom: 0 !important; }
h2 { font-size: 1.4rem !important; font-weight: 700 !important; color: #fafafa !important; letter-spacing: -0.03em !important; }
h3 { font-size: 1rem !important; font-weight: 600 !important; color: #e4e4e7 !important; }
p, label, div { color: #71717a !important; font-size: 13px !important; }
strong { color: #e4e4e7 !important; }

/* ═══════════════════════════════
   LOGIN PANEL (left side)
═══════════════════════════════ */
.login-panel {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 18px !important;
    padding: 52px 44px !important;
    min-height: 540px;
}
.login-brand {
    font-size: 15px;
    font-weight: 700;
    color: #f472b6 !important;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
}
.login-tag {
    font-size: 10px;
    color: #3f3f46 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 44px;
}
.login-hero {
    font-size: 52px;
    font-weight: 800;
    color: #fafafa !important;
    line-height: 1.08;
    letter-spacing: -0.04em;
    margin-bottom: 18px;
}
.login-sub {
    font-size: 15px !important;
    color: #52525b !important;
    line-height: 1.65;
    max-width: 380px;
    margin-bottom: 44px;
}
.stat-row { display: flex; gap: 40px; margin-top: 8px; }
.stat-val { font-size: 22px; font-weight: 800; color: #f472b6; letter-spacing: -0.03em; }
.stat-lbl { font-size: 10px; color: #3f3f46 !important; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }

/* ═══════════════════════════════
   INPUTS
═══════════════════════════════ */
.stTextInput input, .stTextArea textarea {
    background: #111113 !important;
    border: 1px solid #27272a !important;
    color: #fafafa !important;
    border-radius: 8px !important;
    padding: 10px 13px !important;
    font-size: 13.5px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #f472b6 !important;
    box-shadow: 0 0 0 3px rgba(244,114,182,0.08) !important;
    outline: none !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #3f3f46 !important; }
.stTextInput > label, .stTextArea > label { color: #a1a1aa !important; font-size: 12px !important; font-weight: 500 !important; margin-bottom: 4px !important; }

[data-testid="stSelectbox"] > div > div {
    background: #111113 !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    color: #fafafa !important;
    font-size: 13px !important;
}
[data-testid="stDateInput"] input {
    background: #111113 !important;
    border: 1px solid #27272a !important;
    color: #fafafa !important;
    border-radius: 8px !important;
    max-width: 150px !important;
    font-size: 13px !important;
}
[data-testid="stDateInput"] > div { max-width: 150px !important; }
[data-testid="stDateInput"] label { color: #a1a1aa !important; font-size: 12px !important; font-weight: 500 !important; }

/* ═══════════════════════════════
   BUTTONS
═══════════════════════════════ */
.stButton > button {
    background: #111113 !important;
    color: #d4d4d8 !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    height: 38px !important;
    padding: 0 16px !important;
    transition: all 0.15s ease !important;
    letter-spacing: -0.01em !important;
}
.stButton > button:hover {
    background: #18181b !important;
    border-color: #f472b6 !important;
    color: #f9a8d4 !important;
}
/* Primary sign-in button */
.stButton > button[kind="primary"] {
    background: #f472b6 !important;
    color: #09090b !important;
    border: none !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════
   EXPANDER (Add New Application)
═══════════════════════════════ */
[data-testid="stExpander"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 13.5px !important;
    color: #d4d4d8 !important;
    padding: 13px 18px !important;
    background: #111113 !important;
}
[data-testid="stExpander"] summary:hover { background: #18181b !important; }
[data-testid="stExpander"] summary svg { display: inline-block !important; }
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] { display: none !important; }
[data-testid="stExpander"] > div > div { padding: 0 18px 18px 18px !important; }

/* ═══════════════════════════════
   STAT CARDS
═══════════════════════════════ */
.stat-card {
    background: #111113;
    border: 1px solid #1c1c1f;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s ease;
}
.stat-card:hover { border-color: #27272a; }
.stat-number { font-size: 32px; font-weight: 800; line-height: 1; margin-bottom: 6px; letter-spacing: -0.04em; }
.stat-label { font-size: 10.5px; font-weight: 600; color: #3f3f46 !important; text-transform: uppercase; letter-spacing: 0.1em; }

/* ═══════════════════════════════
   JOB ROW CARDS
═══════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 10px !important;
    padding: 4px 16px !important;
    margin-bottom: 6px !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #27272a !important;
}

/* Table header row */
.table-header {
    padding: 0 16px;
    margin-bottom: 4px;
}

/* ═══════════════════════════════
   FILE UPLOADER
═══════════════════════════════ */
[data-testid="stFileUploader"] > div { max-width: 400px !important; }
[data-testid="stFileUploaderDropzone"] {
    background: #111113 !important;
    border: 1px dashed #27272a !important;
    border-radius: 8px !important;
    max-width: 400px !important;
    padding: 10px 14px !important;
    min-height: 52px !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: #f472b6 !important; }
[data-testid="stFileUploaderDropzoneInput"] + div span { display: none !important; }
[data-testid="stFileUploader"] button span { display: none !important; }
[data-testid="stFileUploader"] button::before { content: "Browse files" !important; color: #d4d4d8 !important; }
[data-testid="baseButton-secondary"] span[data-testid="stIconMaterial"] { display: none !important; }
[data-testid="stFileUploader"] label { color: #a1a1aa !important; font-size: 12px !important; font-weight: 500 !important; }

/* ═══════════════════════════════
   DIVIDERS & MISC
═══════════════════════════════ */
hr { border-color: #1c1c1f !important; margin: 20px 0 !important; }
[data-testid="stCaption"] { color: #3f3f46 !important; font-size: 11.5px !important; }
[data-testid="stCaption"] p { color: #3f3f46 !important; }

/* Table column headers */
[data-testid="stMarkdown"] strong { color: #52525b !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.07em !important; }

/* Success/error messages */
[data-testid="stAlert"] { border-radius: 8px !important; border: 1px solid #27272a !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #09090b; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3f3f46; }

/* Shorter date input bar */
[data-testid="stDateInput"] input { max-width: 140px !important; }
[data-testid="stDateInput"] > div { max-width: 140px !important; }

/* Fix file uploader button ghost text */
[data-testid="stFileUploaderDropzoneInput"] + div span { display: none !important; }
[data-testid="baseButton-secondary"] span[data-testid="stIconMaterial"] { display: none !important; }
[data-testid="stFileUploader"] button span { display: none !important; }
[data-testid="stFileUploader"] button::before { content: "Browse files" !important; color: white !important; }

</style>
""", unsafe_allow_html=True)

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    l_col, r_col = st.columns([1.1, 1], gap="large")

    with l_col:
        st.markdown("""
        <div class="login-panel">
            <div class="login-brand">✦ Career Hunt HQ</div>
            <div class="login-tag">AI Resume Tracking Tool</div>
            <div class="login-hero">Find.<br>Match.<br>File.</div>
            <div class="login-sub">The smarter, organized way to career hunt. No more spreadsheets or scattered files.</div>
            <div class="stat-row">
                <div><div class="stat-val">Fit Score</div><div class="stat-lbl">Match Rank</div></div>
                <div><div class="stat-val">AI</div><div class="stat-lbl">Gemini Backed</div></div>
                <div><div class="stat-val">1-Click</div><div class="stat-lbl">Auto-Fill</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col:
        with st.container():
            tab = st.session_state["login_tab"]
            
            if tab == "login":
                st.markdown("<h2 style='font-size:36px; margin-bottom:8px;'>Welcome Back</h2>", unsafe_allow_html=True)
                st.markdown("<p style='margin-bottom:32px;'>Sign in to access your dashboard</p>", unsafe_allow_html=True)
                
                u = st.text_input("Username", key="login_username")
                p = st.text_input("Password", type="password", key="login_password")
                
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.markdown('<style>[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] .stButton:first-of-type > button { background: #f472b6 !important; color: #0a0a0a !important; border: none !important; font-weight: 700 !important; font-size: 14px !important; } [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] .stButton:first-of-type > button:hover { background: #ec4899 !important; }</style>', unsafe_allow_html=True)
                if st.button("Sign In", use_container_width=True):
                    if login_user(u, p):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u
                        st.rerun()
                    else: st.error("Invalid credentials")
                
                if st.button("New Here? Create Account →", use_container_width=True):
                    st.session_state["login_tab"] = "signup"; st.rerun()

            elif tab == "signup":
                st.markdown("<h2 style='font-size:40px; margin-bottom:8px;'>Create Account</h2>", unsafe_allow_html=True)
                st.markdown("<p style='margin-bottom:24px;'>Join the AI-powered career revolution</p>", unsafe_allow_html=True)
                
                new_u = st.text_input("Username", key="s_u")
                new_e = st.text_input("Email", key="s_e")
                new_p = st.text_input("Password", type="password", key="s_p")
                
                st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
                if st.button("Sign Up", use_container_width=True):
                    ok, err = sign_up_user(new_u, new_p, new_e)
                    if ok: st.session_state["login_tab"] = "login"; st.rerun()
                    else: st.error(err)
                
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state["login_tab"] = "login"; st.rerun()


# ── DASHBOARD ──────────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:
    st.markdown(f"<p style='color:#3f3f46;font-size:12px;font-weight:500;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:2px;'>Welcome back</p><h1 style='margin-top:0;'>{st.session_state['username']}</h1>", unsafe_allow_html=True)


# MAIN APP

if st.session_state["logged_in"]:

    t1, t2 = st.columns([5, 1])

    with t1:
        st.title("Career Hunt HQ")
    st.caption("⚠️ This website uses AI which may make errors. Make sure to double-check all results.")

    with t2:
        # FIXED: Added unique key
        if st.button("Sign Out", key="sign_out_main_top"):
            st.session_state.clear()
            st.rerun()

      # ── STAT CARDS ──
    jobs_list = load_jobs()
    if jobs_list:
        df_stats = pd.DataFrame(jobs_list)
        total = len(df_stats)
        interviews = len(df_stats[df_stats.get("status", pd.Series(dtype=str)).str.contains("Interview", na=False)]) if "status" in df_stats else 0
        offers = len(df_stats[df_stats.get("status", pd.Series(dtype=str)).str.contains("Offer", na=False)]) if "status" in df_stats else 0
        def parse_score(s):
            try: return float(str(s).split("/")[0])
            except: return None
        scores = df_stats["match_score"].apply(parse_score).dropna() if "match_score" in df_stats else pd.Series()
        avg_score = f"{scores.mean():.0f}%" if len(scores) > 0 else "—"

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f'''<div class="stat-card"><div class="stat-number" style="color:#fafafa;">{total}</div><div class="stat-label">Applications</div></div>''', unsafe_allow_html=True)
        with sc2:
            st.markdown(f'''<div class="stat-card"><div class="stat-number" style="color:#f472b6;">{interviews}</div><div class="stat-label">Interviews</div></div>''', unsafe_allow_html=True)
        with sc3:
            st.markdown(f'''<div class="stat-card"><div class="stat-number" style="color:#34d399;">{offers}</div><div class="stat-label">Offers</div></div>''', unsafe_allow_html=True)
        with sc4:
            st.markdown(f'''<div class="stat-card"><div class="stat-number" style="color:#a78bfa;">{avg_score}</div><div class="stat-label">Avg Match</div></div>''', unsafe_allow_html=True)


    # ADD JOB

    with st.expander("➕ Add New Application", expanded=True):

        c1, c2 = st.columns(2)

        with c1:
            comp = st.text_input("Company Name")

        with c2:
            pos = st.text_input("Position Title")

        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill Details"):
            if url_in:
                with st.spinner("Doing the heavy lifting... just a few moments more while we set things up..."):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)

        final_desc = st.text_area(
            "Job Description",
            value=st.session_state["formatted_desc"],
            height=220
        )

        col1, col2 = st.columns(2)

        with col1:
            up_file = st.file_uploader(
                "Upload Resume",
                type=["pdf", "docx", "txt"]
            )
            if up_file is not None:
                st.session_state["resume_txt"] = extract_text_from_upload(up_file)

        with col2:
            applied_date = st.date_input("Date Applied", format="MM/DD/YYYY")

        if st.button("🔍 Scan Resume"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Adding the finishing touches... getting you one step closer to your next job."):
                    st.session_state["match_data"] = get_ai_match_feedback(
                        final_desc,
                        st.session_state["resume_txt"]
                    )

        if st.session_state["match_data"]:
            match = st.session_state["match_data"]
            st.markdown("## 🎯 How You Stack Up")
            st.success(f"Your Rank: {match.get('score', 'N/A')}")
            for item in match.get("feedback", []):
                if not item.upper().startswith("SCORE:"):
                    st.write(item)

        # SAVE BUTTON
        if st.button("💾 Save"):

            resume_url = None
            score = "No score found... guess your skills just broke our algorithm."

            if up_file is not None:
                resume_url = upload_resume(
                    up_file,
                    st.session_state["username"]
                )

            if st.session_state.get("resume_txt") and final_desc:
                with st.spinner("Saving your results...time for a quick coffee break while we file this away."):
                    match_result = get_ai_match_feedback(
                        final_desc,
                        st.session_state["resume_txt"]
                    )
                    st.session_state["match_data"] = match_result
                    score = match_result.get("score", "N/A")

            elif st.session_state.get("match_data"):
                score = st.session_state["match_data"].get("score", "N/A")

            success = save_job(
                company=comp,
                position=pos,
                description=final_desc,
                job_url=url_in,
                resume_url=resume_url,
                match_score=score,
                applied_date=applied_date
            )

            if success:
                st.session_state["resume_txt"] = None
                st.session_state["match_data"] = None
                st.session_state["formatted_desc"] = ""
                st.success("Application saved")
                st.rerun()
            else:
                st.error("Save failed")

    st.divider()

    st.markdown("<h2 style='margin-top:8px;margin-bottom:16px;'>Your Career Vault</h2>", unsafe_allow_html=True)

    jobs_list = load_jobs()

    status_options = [
        "📝 Applied",
        "📨 Contacted",
        "📅 Interview",
        "✅ Offer",
        "❌ Rejected"
    ]

    if jobs_list:

        df = pd.DataFrame(jobs_list)

        # SORT CONTROLS
        sort_col, sort_dir_col = st.columns([2, 2])
        with sort_col:
            sort_by = st.selectbox(
                "Sort by",
                ["Date Applied", "Company", "Position", "Match Score", "Application Status"],
                key="sort_by"
            )
        with sort_dir_col:
            sort_dir = st.selectbox(
                "Order",
                ["Newest First", "Oldest First", "A → Z", "Z → A", "Highest First", "Lowest First"],
                key="sort_dir"
            )

        # Apply sort
        if sort_by == "Company":
            df = df.sort_values("company", ascending=(sort_dir == "A → Z"))
        elif sort_by == "Position":
            df = df.sort_values("position", ascending=(sort_dir == "A → Z"))
        elif sort_by == "Match Score":
            def score_val(s):
                try: return int(str(s).split("/")[0])
                except: return 0
            df["_score_num"] = df["match_score"].apply(score_val)
            df = df.sort_values("_score_num", ascending=(sort_dir == "Lowest First"))
        elif sort_by == "Status":
            df = df.sort_values("status", ascending=(sort_dir == "A → Z"))
        else:
            df = df.sort_values("created_at", ascending=(sort_dir == "Oldest First"))

        ratios = [1.5, 1.5, 0.8, 1.5, 1, 0.7, 0.7, 0.7]
        headers = ["Company", "Position/Role", "Match Score", "Application Status", "Date Applied", "Resume", "Snapshot", "Delete"]

        cols = st.columns(ratios)
        for c, h in zip(cols, headers):
            c.markdown(f"<span style='font-size:11px;font-weight:600;color:#3f3f46;text-transform:uppercase;letter-spacing:0.07em;'>{h}</span>", unsafe_allow_html=True)

        st.divider()

        for idx, row in df.iterrows():

            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(ratios, vertical_alignment="center")

                c1.write(row.get("company", ""))
                c2.write(row.get("position", ""))
                c3.write(row.get("match_score", "N/A"))

                curr = row.get("status", "📝 Applied")

                with c4:
                    new_stat = st.selectbox(
                        "Status",
                        status_options,
                        index=(status_options.index(curr) if curr in status_options else 0),
                        key=f"s_{row['id']}",
                        label_visibility="collapsed"
                    )
                    if new_stat != curr:
                        update_job_full(row["id"], {"status": new_stat})
                        st.rerun()

                # DATE APPLIED
                raw_date = row.get("created_at", "")
                try:
                    from datetime import datetime
                    date_str = datetime.fromisoformat(str(raw_date)).strftime("%m/%d/%Y")
                except:
                    date_str = str(raw_date)[:10] if raw_date else "—"
                c5.write(date_str)

                resume_link = str(row.get("resume_link") or "")
                with c6:
                    if resume_link:
                        st.link_button("📄", resume_link)
                    else:
                        st.button("📄", key=f"r_{row['id']}", disabled=True)

                pdf_url = str(row.get("pdf_url") or "")
                with c7:
                    if pdf_url:
                        st.link_button("📸", pdf_url)
                    else:
                        st.button("📸", key=f"p_{row['id']}", disabled=True)

                if c8.button("❌", key=f"d_{row['id']}"):
                    delete_job(row["id"])
                    st.rerun()

    else:
        st.write("You have no applications saved yet.")
