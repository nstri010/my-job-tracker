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
    padding: 48px 44px 52px 44px !important;
    height: auto;
    overflow: visible;
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
.stat-row { display: flex; gap: 32px; margin-top: 40px; }
.stat-val { font-size: 22px; font-weight: 700; color: #f472b6; white-space: nowrap; }
.stat-lbl { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }


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
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    padding: 2px 12px !important;
    margin-bottom: 5px !important;
}

/* Zero out ALL internal gaps so content sits flush */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    min-height: 54px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stColumn"] > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stVerticalBlockBorderWrapper"] p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
}

/* Selectbox: hide label */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] label {
    display: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stSelectbox"] > div {
    margin-top: 0 !important;
}

/* All 3 icon buttons: uniform size and style */
[data-testid="stVerticalBlockBorderWrapper"] button {
    width: 34px !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.22) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] a[data-testid="stLinkButton"] {
    width: 34px !important;
    height: 34px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

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
    l_col, r_col = st.columns([1.1, 1], gap="large")

    with l_col:
        st.markdown("""
        <div style="background:rgba(18,18,24,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:20px;padding:36px 36px 40px 36px;">
            <div style="font-size:15px;font-weight:700;color:#f472b6;margin-bottom:4px;">✦ Career Hunt HQ</div>
            <div style="font-size:10px;color:#52525b;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:28px;">AI Resume Tracking Tool</div>
            <div style="font-size:38px;font-weight:800;color:#fafafa;line-height:1.05;letter-spacing:-0.04em;margin-bottom:14px;">Find.<br><span style="color:#f472b6;">Match.</span><br>File.</div>
            <div style="font-size:13px;color:#52525b;line-height:1.6;margin-bottom:28px;">The smarter way to career hunt. No more spreadsheets or disorganized files.</div>
            <div style="font-size:13px;color:#52525b;line-height:1.6;margin-bottom:28px;">A smarter way to career hunt. No more spreadsheets or disorganized files.</div>
            <div style="display:flex;gap:32px;">
                <div><div style="font-size:18px;font-weight:700;color:#f472b6;white-space:nowrap;">Fit Score</div><div style="font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:2px;white-space:nowrap;">Check Your Rank</div></div>
                <div><div style="font-size:18px;font-weight:700;color:#f472b6;white-space:nowrap;">AI</div><div style="font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:2px;white-space:nowrap;">Gemini Backed</div></div>
                <div><div style="font-size:18px;font-weight:700;color:#f472b6;white-space:nowrap;">1-Click</div><div style="font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:2px;white-space:nowrap;">Auto-Fill</div></div>
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
            try:
                parts = str(s).split("/")
                numerator = float(parts[0])
                if len(parts) > 1:
                    denominator = float(parts[1])
                    return (numerator / denominator) * 100 if denominator != 0 else None
                return numerator  # already a percentage if no denominator
            except:
                return None
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

    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;">
        <span style="font-size:32px;">📋</span>
        <span style="font-family:'Playfair Display',serif;font-size:36px;font-weight:700;color:#fff;letter-spacing:-0.02em;">Your Career Vault</span>
    </div>
    """, unsafe_allow_html=True)

    jobs_list = load_jobs()

    status_options = [
        "📝 Applied",
        "📨 Contacted",
        "📅 Interview",
        "✅ Offer",
        "❌ Rejected"
    ]

    STATUS_STYLES = {
        "📝 Applied":   ("rgba(148,163,184,0.12)", "#94a3b8"),
        "📨 Contacted": ("rgba(96,165,250,0.15)",  "#60a5fa"),
        "📅 Interview": ("rgba(251,191,36,0.15)",  "#fbbf24"),
        "✅ Offer":     ("rgba(52,211,153,0.15)",  "#34d399"),
        "❌ Rejected":  ("rgba(248,113,113,0.12)", "#f87171"),
    }

    if jobs_list:
        df = pd.DataFrame(jobs_list)

        # ── Sort controls ──────────────────────────────────────────────
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

        col_ratios = [2, 2, 1.4, 2, 1.5, 1, 1, 1]

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Inject CSS so st.columns has zero padding, making headers align perfectly ──
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        /* re-add left padding only for bordered containers so row content isn't flush */
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stColumn"] {
            padding-left: 4px !important;
            padding-right: 4px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Headers: one div per column, alignment matches cell content below ──
        header_cfg = [
            ("Company Name",   "left"),
            ("Position/Title", "left"),
            ("Match Score",    "center"),
            ("Status",         "left"),
            ("Date Applied",   "left"),
            ("Resume",         "center"),
            ("Snapshot",       "center"),
            ("Delete",         "center"),
        ]
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(col_ratios)
        for col, (label, align) in zip([h1, h2, h3, h4, h5, h6, h7, h8], header_cfg):
            col.markdown(
                f'<div style="text-align:{align};font-size:10px;font-weight:700;'
                f'color:#4b5563;text-transform:uppercase;letter-spacing:0.08em;white-space:nowrap;">{label}</div>',
                unsafe_allow_html=True
            )

        # ── Job rows ───────────────────────────────────────────────────
        for _, row in df.iterrows():
            curr      = row.get("status", "📝 Applied")
            raw_score = row.get("match_score", "")
            raw_date  = row.get("created_at", "")
            company   = row.get("company", "—")
            position  = row.get("position", "—")

            try:
                parts = str(raw_score).split("/")
                num   = float(parts[0])
                denom = float(parts[1]) if len(parts) > 1 else 10
                pct   = int((num / denom) * 100)
                sc    = "#34d399" if pct >= 75 else "#fbbf24" if pct >= 50 else "#f87171"
                score_disp = f'<b style="color:{sc};font-size:15px;">{raw_score}</b>'
            except:
                score_disp = '<span style="color:#64748b;">—</span>'

            try:
                date_str = datetime.fromisoformat(str(raw_date)).strftime("%b %d, %Y")
            except:
                date_str = str(raw_date)[:10] if raw_date else "—"

            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(col_ratios, vertical_alignment="center")
                c1.write(company)
                c2.write(position)
                c3.markdown(score_disp, unsafe_allow_html=True)
                with c4:
                    new_stat = st.selectbox(
                        "Status", status_options,
                        index=(status_options.index(curr) if curr in status_options else 0),
                        key=f"s_{row['id']}", label_visibility="collapsed"
                    )
                    if new_stat != curr:
                        update_job_full(row["id"], {"status": new_stat})
                        st.rerun()
                c5.write(date_str)
                resume_link = str(row.get("resume_link") or "")
                with c6:
                    if resume_link:
                        st.link_button("📄", resume_link, key=f"rl_{row['id']}")
                    else:
                        st.button("📄", key=f"r_{row['id']}", disabled=True)
                pdf_url = str(row.get("pdf_url") or "")
                with c7:
                    if pdf_url:
                        st.link_button("📸", pdf_url, key=f"pl_{row['id']}")
                    else:
                        st.button("📸", key=f"p_{row['id']}", disabled=True)
                if c8.button("✕", key=f"d_{row['id']}"):
                    delete_job(row["id"])
                    st.rerun()

    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#4b5563;">
            <div style="font-size:40px;margin-bottom:12px;">📭</div>
            <div style="font-size:16px;font-weight:500;">No applications yet</div>
            <div style="font-size:13px;margin-top:6px;">Add your first one above to get started.</div>
        </div>
        """, unsafe_allow_html=True)
