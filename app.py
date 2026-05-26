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

st.set_page_config(page_title="Job Tracker", layout="wide")

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

/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2d1b2e 0%, #3b1f45 40%, #1a1a3e 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stHorizontalBlock"] { gap: 0 !important; align-items: flex-start !important; }

/* Left column padding */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
    padding: 8vh 60px 40px 60px !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    min-height: 100vh !important;
}
/* Right column padding */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    padding: 8vh 80px 40px 80px !important;
    background: none !important;
    border: none !important;
    border-radius: 0 !important;
    min-height: 100vh !important;
}

* { font-family: 'Inter', sans-serif !important; }
h1 { font-family: 'Playfair Display', serif !important; color: #ead8ee !important; }
h2, h3 { font-family: 'Playfair Display', serif !important; color: #ead8ee !important; }
p, label, div[data-testid="stText"] > p { color: #c0a0c4 !important; font-weight: 500 !important; }
[data-testid="stCaptionContainer"] p { color: #e879a0 !important; font-weight: 600 !important; }
strong { color: #ead8ee !important; }
hr { border-color: #4a2248 !important; }

/* ── Buttons ── */
.stButton > button {
    background: #4a2248 !important;
    color: #c090be !important;
    border: 1px solid #6e3868 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #5a2a58 !important; border-color: #8a4a88 !important; }
.stButton > button:disabled {
    background: #2e1a2e !important;
    border-color: #4a2248 !important;
    color: rgba(192,144,190,0.3) !important;
}

/* ── Sign In main button ── */
.signin-btn > button {
    background: linear-gradient(135deg, #7a2a70, #5a1a80) !important;
    color: #f8e8ff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    height: 52px !important;
    letter-spacing: 0.02em !important;
}
.signin-btn > button:hover {
    background: linear-gradient(135deg, #8a3a80, #6a2a90) !important;
}

/* ── Ghost/text-style buttons ── */
.ghost-btn > button {
    background: transparent !important;
    color: #f472b6 !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 0 !important;
    text-decoration: none !important;
}
.ghost-btn > button:hover {
    background: transparent !important;
    color: #f9a8d4 !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stDateInput input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid #4a2a4a !important;
    color: #ead8ee !important;
    border-radius: 10px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    height: 44px !important;
}
.stTextInput input:focus {
    border-color: #a060a0 !important;
    box-shadow: 0 0 0 2px rgba(160,96,160,0.15) !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid #4a2a4a !important;
    color: #ead8ee !important;
    border-radius: 10px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #2a1230 !important;
    border: 1px solid #5a2d58 !important;
    border-radius: 12px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] { color: #c090be !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #f472b6 !important; border-bottom-color: #f472b6 !important; }

/* ── Link buttons ── */
.stLinkButton a {
    background: #4a2248 !important;
    border: 1px solid #6e3868 !important;
    color: #c090be !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 6px 12px !important;
}
.stLinkButton a:hover { background: #5a2a58 !important; }

/* ── Row cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #2e1535 !important;
    border: 1px solid #7a3a78 !important;
    border-radius: 10px !important;
    padding: 4px 8px !important;
    margin-bottom: 8px !important;
    transition: background 0.18s, border-color 0.18s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    background: #3a1d42 !important;
    border-color: #a050a0 !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; }
.stDivider { margin-top: 0.3rem !important; margin-bottom: 0.3rem !important; }
[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] { margin-bottom: 0 !important; }

.login-left { display: flex; flex-direction: column; justify-content: center; }
.login-logo { font-size: 16px; color: #ead8ee; font-weight: 700; margin-bottom: 40px; }
.login-headline { font-size: 52px; font-weight: 800; color: #ead8ee; line-height: 1.15; margin-bottom: 16px; }
.login-sub-text { font-size: 16px; color: #7a5888; line-height: 1.7; max-width: 400px; margin-bottom: 40px; }
.login-stat-row { display: flex; gap: 48px; }
.login-stat-num { font-size: 40px; font-weight: 800; color: #f472b6; line-height: 1; }
.login-stat-num.green { color: #34d399; }
.login-stat-num.purple { color: #c084fc; }
.login-stat-lbl { font-size: 13px; color: #5a4068; margin-top: 4px; }
.login-right { display: flex; flex-direction: column; justify-content: center; }
.login-welcome { font-size: 36px; font-weight: 800; color: #ead8ee; margin-bottom: 6px; }
.login-sub { font-size: 15px; color: #7a5888; margin-bottom: 24px; }
</style>
""", unsafe_allow_html=True)

# ── PASSWORD STRENGTH HELPER ───────────────────────────────────────────────────

def password_strength(pw):
    if not pw:
        return None, None, None
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 12: score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pw): score += 1
    if score <= 1:   return "Weak",   "#ef4444", 20
    elif score == 2: return "Fair",   "#f97316", 40
    elif score == 3: return "Medium", "#eab308", 65
    elif score == 4: return "Strong", "#22c55e", 85
    else:            return "Very Strong", "#10b981", 100

# ── LOGIN PAGE ─────────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:

    left, right = st.columns([1, 1], gap="small")

    with left:
        st.markdown("""
        <div class="login-left">
            <div class="login-logo">✦ Job Tracker</div>
            <div class="login-headline">
                Land Your<br><span style="color:#f472b6;">Dream Job</span>
            </div>
            <div class="login-sub-text">
                Track applications, scan your resume against job descriptions,
                and get AI-powered match scores — all in one place.
            </div>
            <div class="login-stat-row">
                <div>
                    <div class="login-stat-num">AI</div>
                    <div class="login-stat-lbl">Match Scoring</div>
                </div>
                <div>
                    <div class="login-stat-num green">Auto</div>
                    <div class="login-stat-lbl">Job Scraping</div>
                </div>
                <div>
                    <div class="login-stat-num purple">Live</div>
                    <div class="login-stat-lbl">Status Tracking</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        tab = st.session_state["login_tab"]

        # ── SIGN IN ──
        if tab == "login":
            st.markdown("<div class='login-welcome'>Welcome Back</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-sub'>Sign in to continue your journey</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            u = st.text_input("Username", key="login_username", placeholder="Enter your username")
            p = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            rm_col, fp_col = st.columns([1, 1])
            with rm_col:
                st.checkbox("Remember me", key="remember_me")
            with fp_col:
                st.markdown(
                    "<div style='text-align:right;padding-top:8px;'>"
                    "<span style='font-size:14px;color:#f472b6;cursor:pointer;font-weight:600;'"
                    " onclick=\"\">Forgot password?</span></div>",
                    unsafe_allow_html=True
                )
                if st.button("→ Reset password", key="go_forgot", use_container_width=True):
                    st.session_state["login_tab"] = "forgot"
                    st.session_state["reset_sent"] = False
                    st.rerun()

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="signin-btn">', unsafe_allow_html=True)
            if st.button("Sign In", key="do_login", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
            <div style='text-align:center;margin-top:24px;font-size:14px;color:#6a4868;'>
                Don't have an account?
                <span style='color:#f472b6;font-weight:600;cursor:pointer;'> Sign up for free</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Create a free account →", key="go_signup", use_container_width=True):
                st.session_state["login_tab"] = "signup"
                st.rerun()

        # ── SIGN UP ──
        else:
            st.markdown("<div style='font-size:26px;font-weight:700;color:#ead8ee;margin-bottom:4px;'>Create Account</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:13px;color:#8a6888;margin-bottom:24px;'>Start your job tracking journey today</div>", unsafe_allow_html=True)

            new_u = st.text_input("Username", key="signup_username", placeholder="Choose a username")
            new_e = st.text_input("Email", key="signup_email", placeholder="Enter your real email address")
            new_p = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a strong password")

            # Password strength meter
            if new_p:
                label, color, pct = password_strength(new_p)
                st.markdown(f"""
                <div style="margin-top:-8px;margin-bottom:8px;">
                    <div style="background:#2a1230;border-radius:4px;height:5px;width:100%;overflow:hidden;">
                        <div style="background:{color};height:5px;width:{pct}%;border-radius:4px;transition:width 0.3s;"></div>
                    </div>
                    <div style="text-align:right;font-size:12px;color:{color};margin-top:3px;font-weight:600;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            confirm_p = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter your password")

            # Password match indicator
            if confirm_p:
                if new_p == confirm_p:
                    st.markdown("<div style='font-size:12px;color:#22c55e;margin-top:-8px;margin-bottom:8px;'>✓ Passwords match</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-size:12px;color:#ef4444;margin-top:-8px;margin-bottom:8px;'>✗ Passwords do not match</div>", unsafe_allow_html=True)

            # Terms of service
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="agree_terms")
            st.markdown("""
            <div style='font-size:11px;color:#5a3858;margin-top:-8px;margin-bottom:12px;line-height:1.5;'>
                By creating an account you agree to our
                <span style='color:#f472b6;cursor:pointer;'>Terms of Service</span> and
                <span style='color:#f472b6;cursor:pointer;'>Privacy Policy</span>.
                Your data is kept private and never sold.
            </div>
            """, unsafe_allow_html=True)

            if st.button("Create Account", key="do_signup", use_container_width=True):
                if not new_u or not new_e or not new_p:
                    st.error("Please fill in all fields")
                elif "@" not in new_e or "." not in new_e:
                    st.error("Please enter a valid email address")
                elif new_p != confirm_p:
                    st.error("Passwords do not match")
                elif not agree:
                    st.error("Please agree to the Terms of Service to continue")
                elif password_strength(new_p)[0] == "Weak":
                    st.warning("Please choose a stronger password (add uppercase, numbers, or symbols)")
                else:
                    ok, err = sign_up_user(new_u, new_p, new_e)
                    if ok:
                        st.success("Account created! Check your email to confirm, then sign in.")
                        st.session_state["login_tab"] = "login"
                        st.rerun()
                    else:
                        st.error(f"Sign up failed: {err}")

            st.markdown("<div style='text-align:center;margin-top:16px;font-size:13px;color:#7a5878;'>Already have an account?</div>", unsafe_allow_html=True)
            if st.button("Sign in →", key="go_login", use_container_width=True):
                st.session_state["login_tab"] = "login"
                st.rerun()

# ── MAIN APP ───────────────────────────────────────────────────────────────────

if st.session_state["logged_in"]:

    # ── Header ──
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    h1, h2 = st.columns([6, 1])
    with h1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
            <span style="font-size:28px;font-family:'Playfair Display',serif;font-weight:700;color:#ead8ee;">✦ Job Tracker</span>
            <span style="font-size:13px;color:#7a5878;background:#2a1230;border:1px solid #4a2248;
                border-radius:20px;padding:3px 12px;">
                {st.session_state.get('username','') }
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("⚠️ This website uses AI which may make errors. Make sure to double-check all results.")
    with h2:
        if st.button("Sign Out", use_container_width=True):
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
    else:
        total, interviews, offers, avg_score = 0, 0, 0, "—"

    sc1, sc2, sc3, sc4 = st.columns(4)
    cards = [
        (sc1, "📋", total,       "#e8d8ec", "Total Applications"),
        (sc2, "🗓️", interviews,  "#f472b6", "Interviews"),
        (sc3, "✅", offers,      "#34d399", "Offers"),
        (sc4, "🎯", avg_score,   "#c084fc", "Avg AI Match"),
    ]
    for col, icon, val, color, label in cards:
        with col:
            st.markdown(f"""
            <div style="background:#2a1230;border:1px solid #4a2050;border-radius:12px;
                        padding:20px 22px;margin-bottom:12px;position:relative;overflow:hidden;">
                <div style="position:absolute;top:16px;right:18px;font-size:22px;opacity:0.25;">{icon}</div>
                <div style="font-size:30px;font-weight:700;color:{color};line-height:1;margin-bottom:6px;">{val}</div>
                <div style="font-size:11px;font-weight:600;color:#7a5878;text-transform:uppercase;
                            letter-spacing:0.06em;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── ADD JOB ──
    with st.expander("➕  Add New Application"):
        c1, c2 = st.columns(2)
        with c1:
            comp = st.text_input("Company Name")
        with c2:
            pos = st.text_input("Position Title")

        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill from URL"):
            if url_in:
                with st.spinner("Scraping job details..."):
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

        if st.button("🔍 Scan Resume vs Job"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Analyzing match..."):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])

        if st.session_state["match_data"]:
            match = st.session_state["match_data"]
            st.markdown("## 🎯 How You Stack Up")
            st.success(f"Your Rank: {match.get('score', 'N/A')}")
            for item in match.get("feedback", []):
                if not item.upper().startswith("SCORE:"):
                    st.write(item)

        if st.button("💾 Save Application"):
            resume_url = None
            score = "No score found... guess your skills just broke our algorithm."
            if up_file is not None:
                resume_url = upload_resume(up_file, st.session_state["username"])
            if st.session_state.get("resume_txt") and final_desc:
                with st.spinner("Saving..."):
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
                st.success("Application saved!")
                st.rerun()
            else:
                st.error("Save failed")

    st.divider()

    # ── JOBS TABLE ──
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:20px;font-family:'Playfair Display',serif;font-weight:700;color:#ead8ee;">
            📋 My Applied Jobs
        </span>
    </div>
    """, unsafe_allow_html=True)

    status_options = ["📝 Applied", "📨 Contacted", "📅 Interview", "✅ Offer", "❌ Rejected"]

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
            col.markdown(f'<p style="font-size:11px;letter-spacing:0.08em;color:#7a5078;font-weight:700;margin-bottom:2px;margin-top:0;">{label}</p>', unsafe_allow_html=True)

        for idx, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(ratios, vertical_alignment="center")

                c1.markdown(f'<span style="font-size:15px;font-weight:700;color:#ead8ee;">{row.get("company","")}</span>', unsafe_allow_html=True)
                c2.markdown(f'<span style="font-size:14px;color:#c0a0c4;">{row.get("position","")}</span>', unsafe_allow_html=True)

                raw_score = row.get("match_score", "N/A")
                try:
                    score_num = int(str(raw_score).split("/")[0])
                    score_color = "#f472b6" if score_num >= 80 else "#c084fc" if score_num >= 65 else "#8a6888"
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
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#7a5878;">
            <div style="font-size:40px;margin-bottom:12px;">📭</div>
            <div style="font-size:16px;font-weight:600;">No applications yet</div>
            <div style="font-size:13px;margin-top:6px;">Add your first job above to get started</div>
        </div>
        """, unsafe_allow_html=True)
