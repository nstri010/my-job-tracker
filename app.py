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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600;700&display=swap');

/* ── Base & Terminal Background ── */
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
[data-testid="stMainBlockContainer"] { padding-top: 5rem !important; max-width: 1200px !important; }

/* ── Typography ── */
* { font-family: 'Inter', sans-serif !important; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #ffffff !important; letter-spacing: -0.02em; }
p, label { color: #94a3b8 !important; font-weight: 400 !important; font-size: 14px !important; }

/* ── Glassmorphism Login Panel ── */
.login-panel {
    background: rgba(18, 18, 24, 0.7) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 24px !important;
    padding: 60px 50px !important;
    height: 600px;
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
    height: 45px !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover { 
    background: rgba(244, 114, 182, 0.1) !important; 
    border-color: #f472b6 !important;
}

/* ── Stat Grid ── */
.stat-row { display: flex; gap: 40px; margin-top: 40px; }
.stat-val { font-size: 32px; font-weight: 700; color: #f472b6; }
.stat-lbl { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }


/* ── Fix expander icon text showing as words ── */
[data-testid="stExpander"] summary svg {
    display: inline-block !important;
}
/* Hide any rogue icon label text in expander */
[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
    display: none !important;
}

/* ── File uploader: prevent overflow into adjacent column ── */
[data-testid="stFileUploader"] {
    min-height: 80px !important;
}
[data-testid="stFileUploadDropzone"] {
    min-height: 60px !important;
    height: auto !important;
}


/* ── Remove ghost cursor / focus caret on non-input elements ── */
* { caret-color: transparent !important; }
input, textarea { caret-color: white !important; }


/* ── Job row cards ── */
div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"].job-row-card {
    background: rgba(18, 18, 24, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    margin-bottom: 10px !important;
}

/* Style every job row via container hack */
.job-card-wrap {
    background: rgba(18, 18, 24, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 20px;
    margin-bottom: 10px;
}


/* ── Job row cards — match stat card style ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18, 18, 24, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 6px 12px !important;
    margin-bottom: 8px !important;
}


/* ── Fix file uploader button ghost text ── */
[data-testid="stFileUploaderDropzoneInput"] + div span {
    display: none !important;
}
[data-testid="baseButton-secondary"] span[data-testid="stIconMaterial"] {
    display: none !important;
}



/* ── Shorter date input bar ── */
[data-testid="stDateInput"] input {
    max-width: 140px !important;
}
[data-testid="stDateInput"] > div {
    max-width: 140px !important;
}


/* ── Shorter Upload Resume bar ── */
[data-testid="stFileUploader"] > div {
    max-width: 400px !important;
}
[data-testid="stFileUploaderDropzone"] {
    max-width: 400px !important;
    padding: 8px 12px !important;
    min-height: 50px !important;
}

</style>
""", unsafe_allow_html=True)

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    l_col, r_col = st.columns([1.1, 1], gap="large")

    with l_col:
        st.markdown("""
        <div class="login-panel">
            <div style="font-size:32px; color:#f472b6; margin-bottom:8px; font-family:'Playfair Display'">✦ Career Hunt HQ</div>
            <div style="color:#64748b; font-size:12px; margin-bottom:40px; letter-spacing:2px; text-transform:uppercase;">AI Resume Tracking Tool</div>
            <h1 style="font-size:62px; line-height:1.1; margin-bottom:24px;">Find. Match. File.</h1>
            <p style="font-size:17px; line-height:1.6; max-width:400px;">
                The smarter, organized way to career hunt. No more overwhelming spreadsheets or disorganized files.
            </p>
            <div class="stat-row">
                <div><div class="stat-val">Fit Score</div><div class="stat-lbl">Check Your Rank</div></div>
                <div><div class="stat-val">AI</div><div class="stat-lbl">Gemini Backed Analysis</div></div>
                <div><div class="stat-val">Hassel Free</div><div class="stat-lbl">Saved In One Location </div></div>
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
    st.markdown(f"<h2>Welcome, {st.session_state['username']}</h2>", unsafe_allow_html=True)


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
        card_style = "background:#3d2040;border:1.5px solid #5a2a55;border-radius:10px;padding:16px 20px;margin-bottom:8px;"
        lbl_color = "#8a6a88"

        with sc1:
            st.markdown(f'<div style="{card_style}"><div style="font-size:26px;font-weight:700;color:#e8d8ec;line-height:1;margin-bottom:4px;">{total}</div><div style="font-size:12px;font-weight:600;color:{lbl_color};text-transform:uppercase;letter-spacing:0.05em;">Applications</div></div>', unsafe_allow_html=True)
        with sc2:
            st.markdown(f'<div style="{card_style}"><div style="font-size:26px;font-weight:700;color:#f472b6;line-height:1;margin-bottom:4px;">{interviews}</div><div style="font-size:12px;font-weight:600;color:{lbl_color};text-transform:uppercase;letter-spacing:0.05em;">Interviews</div></div>', unsafe_allow_html=True)
        with sc3:
            st.markdown(f'<div style="{card_style}"><div style="font-size:26px;font-weight:700;color:#34d399;line-height:1;margin-bottom:4px;">{offers}</div><div style="font-size:12px;font-weight:600;color:{lbl_color};text-transform:uppercase;letter-spacing:0.05em;">Offers</div></div>', unsafe_allow_html=True)
        with sc4:
            st.markdown(f'<div style="{card_style}"><div style="font-size:26px;font-weight:700;color:#c084fc;line-height:1;margin-bottom:4px;">{avg_score}</div><div style="font-size:12px;font-weight:600;color:{lbl_color};text-transform:uppercase;letter-spacing:0.05em;">Avg match</div></div>', unsafe_allow_html=True)


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

    st.header("📋 Your Career Vault")

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
            c.markdown(f"**{h}**")

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
