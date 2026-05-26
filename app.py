import streamlit as st
import pandas as pd
import os

from storage import (
    load_jobs,
    save_job,
    delete_job,
    sign_up_user,
    login_user,
    upload_resume,
    update_job_full
)

from utils import (
    scrape_job_link,
    clean_description_with_ai,
    get_ai_match_feedback,
    extract_text_from_upload
)


st.set_page_config(
    page_title="Job Tracker",
    layout="wide"
)

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

# ── THEME CSS ──────────────────────────────────────────────────────────────────

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2d1b2e 0%, #3b1f45 40%, #1a1a3e 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 2rem !important; }

h1 {
    font-family: 'Playfair Display', serif !important;
    color: #ead8ee !important;
}
h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #ead8ee !important;
}
p, label, div[data-testid="stText"] > p {
    color: #c0a0c4 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stCaptionContainer"] p {
    color: #e879a0 !important;
    font-weight: 600 !important;
}
strong { color: #ead8ee !important; }

/* Buttons */
.stButton > button {
    background: #4a2248 !important;
    color: #c090be !important;
    border: 1px solid #6e3868 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background: #5a2a58 !important;
    border-color: #8a4a88 !important;
}
.stButton > button:disabled {
    background: #2e1a2e !important;
    border-color: #4a2248 !important;
    color: rgba(192,144,190,0.3) !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stDateInput input {
    background: #3a1e3c !important;
    border: 1px solid #5a2d58 !important;
    color: #ead8ee !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stSelectbox > div > div {
    background: #3a1e3c !important;
    border: 1px solid #5a2d58 !important;
    color: #ead8ee !important;
    border-radius: 8px !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #3a1e3c !important;
    border: 1px solid #5a2d58 !important;
    border-radius: 12px !important;
}

/* Divider */
hr { border-color: #4a2248 !important; }

/* Tabs */
.stTabs [data-baseweb="tab"] { color: #c090be !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #f472b6 !important; border-bottom-color: #f472b6 !important; }

/* Link buttons */
.stLinkButton a {
    background: #4a2248 !important;
    border: 1px solid #6e3868 !important;
    color: #c090be !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 6px 12px !important;
}
.stLinkButton a:hover {
    background: #5a2a58 !important;
}

/* Row cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #3d1f42 !important;
    border: 1px solid #7a3a78 !important;
    border-radius: 10px !important;
    padding: 4px 8px !important;
    margin-bottom: 8px !important;
    transition: background 0.18s, border-color 0.18s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    background: #4a2450 !important;
    border-color: #a050a0 !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; }

/* Collapse excess vertical gaps */
.stDivider { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] { margin-bottom: 0 !important; }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ── LOGIN ──────────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:

    st.title("🔐 Job Tracker Login")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        u = st.text_input("Username", key="login_username")
        p = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login_user(u, p):
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        new_u = st.text_input("Username", key="signup_username")
        new_p = st.text_input("Password", type="password", key="signup_password")
        if st.button("Create Account"):
            if sign_up_user(new_u, new_p):
                st.success("Account created")
            else:
                st.error("Username exists")


# ── MAIN APP ───────────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:

    t1, t2 = st.columns([6, 1])

    with t1:
        st.title("Job Tracker")

    st.caption("⚠️ This website uses AI which may make errors. Make sure to double-check all results.")

    with t2:
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

    st.divider()

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
    with st.expander("➕ Add New Application"):
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

        final_desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=220)

        col1, col2 = st.columns(2)
        with col1:
            up_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
            if up_file is not None:
                st.session_state["resume_txt"] = extract_text_from_upload(up_file)
        with col2:
            applied_date = st.date_input("Date Applied", format="MM/DD/YYYY")

        if st.button("🔍 Scan Resume"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Adding the finishing touches... getting you one step closer to your next job."):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])

        if st.session_state["match_data"]:
            match = st.session_state["match_data"]
            st.markdown("## 🎯 How You Stack Up")
            st.success(f"Your Rank: {match.get('score', 'N/A')}")
            for item in match.get("feedback", []):
                if not item.upper().startswith("SCORE:"):
                    st.write(item)

        if st.button("💾 Save"):
            resume_url = None
            score = "No score found... guess your skills just broke our algorithm."

            if up_file is not None:
                resume_url = upload_resume(up_file, st.session_state["username"])

            if st.session_state.get("resume_txt") and final_desc:
                with st.spinner("Saving your results... time for a quick coffee break while we file this away."):
                    match_result = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
                    st.session_state["match_data"] = match_result
                    score = match_result.get("score", "N/A")
            elif st.session_state.get("match_data"):
                score = st.session_state["match_data"].get("score", "N/A")

            success = save_job(
                company=comp, position=pos, description=final_desc,
                job_url=url_in, resume_url=resume_url,
                match_score=score, applied_date=applied_date
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
    st.header("📋 My Applied Jobs")

    status_options = [
        "📝 Applied", "📨 Contacted", "📅 Interview", "✅ Offer", "❌ Rejected"
    ]

    if jobs_list:
        df = pd.DataFrame(jobs_list)

        sort_col, sort_dir_col = st.columns([2, 2])
        with sort_col:
            sort_by = st.selectbox("Sort by", ["Date Applied", "Company", "Position", "Match Score", "Status"], key="sort_by")
        with sort_dir_col:
            sort_dir = st.selectbox("Order", ["Newest First", "Oldest First", "A → Z", "Z → A", "Highest First", "Lowest First"], key="sort_dir")

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

        ratios = [1.5, 1.5, 0.8, 1.5, 1, 0.5, 0.5, 0.5]

        hdr = st.columns(ratios)
        for col, label in zip(hdr, ["COMPANY", "POSITION", "MATCH", "STATUS", "DATE APPLIED", "CV", "SNAP", "DEL"]):
            col.markdown(f'<p style="font-size:11px;letter-spacing:0.08em;color:#7a5078;font-weight:700;margin-bottom:2px;margin-top:0px;">{label}</p>', unsafe_allow_html=True)

        for idx, row in df.iterrows():

            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(ratios, vertical_alignment="center")

                c1.markdown(f'<span style="font-size:15px;font-weight:700;color:#ead8ee;">{row.get("company","")}</span>', unsafe_allow_html=True)
                c2.markdown(f'<span style="font-size:14px;color:#c0a0c4;">{row.get("position","")}</span>', unsafe_allow_html=True)

                raw_score = row.get("match_score", "N/A")
                try:
                    score_num = int(str(raw_score).split("/")[0])
                    if score_num >= 80:
                        score_color = "#f472b6"
                    elif score_num >= 65:
                        score_color = "#c084fc"
                    else:
                        score_color = "#8a6888"
                except:
                    score_color = "#8a6888"
                c3.markdown(f'<span style="font-size:16px;font-weight:700;color:{score_color};">{raw_score}</span>', unsafe_allow_html=True)

                curr = row.get("status", "📝 Applied")
                with c4:
                    new_stat = st.selectbox(
                        "Status", status_options,
                        index=(status_options.index(curr) if curr in status_options else 0),
                        key=f"s_{row['id']}", label_visibility="collapsed"
                    )
                    if new_stat != curr:
                        update_job_full(row["id"], {"status": new_stat})
                        st.rerun()

                raw_date = row.get("created_at", "")
                try:
                    from datetime import datetime
                    date_str = datetime.fromisoformat(str(raw_date)).strftime("%m/%d/%Y")
                except:
                    date_str = str(raw_date)[:10] if raw_date else "—"
                c5.markdown(f'<span style="font-size:13px;color:#8a6888;">{date_str}</span>', unsafe_allow_html=True)

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

                if c8.button("🗑", key=f"d_{row['id']}"):
                    delete_job(row["id"])
                    st.rerun()

    else:
        st.write("You have no applications saved yet.")
