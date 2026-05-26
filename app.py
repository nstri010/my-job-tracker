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

if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

# ── THEME CSS ──────────────────────────────────────────────────────────────────

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #2d1b2e 0%, #3d1f3a 45%, #1f1a35 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #fde8f0 !important;
}
p, label, .stMarkdown, [data-testid="stText"] {
    color: #f9a8d4 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stCaptionContainer"] p { color: #c084fc !important; font-weight: 600 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #f472b6, #c084fc) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stDateInput input {
    background: rgba(255,182,213,0.07) !important;
    border: 1px solid rgba(244,114,182,0.25) !important;
    color: #fde8f0 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stSelectbox > div > div {
    background: rgba(255,182,213,0.07) !important;
    border: 1px solid rgba(244,114,182,0.25) !important;
    color: #fde8f0 !important;
    border-radius: 8px !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,182,213,0.06) !important;
    border: 1px solid rgba(244,114,182,0.15) !important;
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: rgba(244,114,182,0.15) !important; }

/* Tabs */
.stTabs [data-baseweb="tab"] { color: #f9a8d4 !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #f472b6 !important; border-bottom-color: #f472b6 !important; }

/* Link buttons */
.stLinkButton a {
    background: rgba(244,114,182,0.12) !important;
    border: 2px solid rgba(244,114,182,0.35) !important;
    color: #f472b6 !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}

/* Row and card borders */
[data-testid="stHorizontalBlock"] {
    background: rgba(255,182,213,0.06) !important;
    border: 1px solid rgba(244,114,182,0.2) !important;
    border-radius: 12px !important;
    padding: 6px 10px !important;
    margin-bottom: 6px !important;
}

/* Sidebar/metric */
[data-testid="metric-container"] { color: #fde8f0 !important; }

/* Success/error */
[data-testid="stAlert"] { border-radius: 8px !important; }
</style>
"""

LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #c9a0bb 0%, #b8c98a 60%, #7bbec4 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #6b1f38 !important;
}
p, label, .stMarkdown, [data-testid="stText"] {
    color: #2a4a38 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stCaptionContainer"] p { color: #2a4a38 !important; font-weight: 600 !important; }

/* Buttons */
.stButton > button {
    background: #E27396 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Inputs */
.stTextInput input, .stTextArea textarea, .stDateInput input {
    background: rgba(255,255,255,0.55) !important;
    border: 1px solid rgba(226,115,150,0.3) !important;
    color: #2a0a18 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.55) !important;
    border: 1px solid rgba(226,115,150,0.3) !important;
    color: #2a0a18 !important;
    border-radius: 8px !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.35) !important;
    border: 1px solid rgba(255,255,255,0.5) !important;
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: rgba(226,115,150,0.2) !important; }

/* Tabs */
.stTabs [data-baseweb="tab"] { color: #6b1f38 !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #E27396 !important; border-bottom-color: #E27396 !important; }

/* Link buttons */
.stLinkButton a {
    background: rgba(255,255,255,0.4) !important;
    border: 2px solid rgba(107,31,56,0.35) !important;
    color: #6b1f38 !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
}
/* Row and card borders */
[data-testid="stHorizontalBlock"] {
    background: rgba(255,255,255,0.35) !important;
    border: 1px solid rgba(255,255,255,0.6) !important;
    border-radius: 12px !important;
    padding: 6px 10px !important;
    margin-bottom: 6px !important;
}
</style>
"""

# Inject theme
if st.session_state["dark_mode"]:
    st.markdown(DARK_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)

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

    t1, t2, t3 = st.columns([5, 1, 1])

    with t1:
        st.title("Job Tracker")
    st.caption("⚠️ This website uses AI which may make errors. Make sure to double-check all results.")

    with t2:
        mode_label = "☀️ Light" if st.session_state["dark_mode"] else "🌙 Dark"
        if st.button(mode_label):
            st.session_state["dark_mode"] = not st.session_state["dark_mode"]
            st.rerun()

    with t3:
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

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

    st.header("📋 My Applied Jobs")

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
                ["Date Applied", "Company", "Position", "Match Score", "Status"],
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

        ratios = [1.5, 1.5, 0.8, 1.5, 1, 0.5, 0.5, 0.5]
        headers = ["Company", "Position", "Match", "Status", "Date Applied", "Resume", "Snapshot", "Delete"]

        cols = st.columns(ratios)
        for c, h in zip(cols, headers):
            c.markdown(f"**{h}**")

        st.divider()

        for idx, row in df.iterrows():

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

            st.divider()

    else:
        st.write("You have no applications saved yet.")
