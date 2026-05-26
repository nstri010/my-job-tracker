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
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 100% !important; }

/* Kill ALL vertical gaps globally on login */
[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* Right column card background */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    background: linear-gradient(160deg, #1a0a20 0%, #1e0e28 60%, #161230 100%) !important;
    border: 1px solid #3a1a45 !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
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

/* ── Specific styling for the Text-Link Forgot Password Button ── */
.forgot-pw-container {
    text-align: right;
    margin-top: -12px;
    margin-bottom: 10px;
}
div.forgot-pw-container > div.stButton > button {
    background: transparent !important;
    border: none !important;
    color: #f472b6 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-decoration: underline !important;
    padding: 0 !important;
    width: auto !important;
    display: inline-block !important;
    box-shadow: none !important;
}
div.forgot-pw-container > div.stButton > button:hover {
    color: #ead8ee !important;
    background: transparent !important;
    text-decoration: none !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stDateInput input {
    background: #2a1230 !important;
    border: 1px solid #5a2d58 !important;
    color: #ead8ee !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] { color: #c090be !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #f472b6 !important; border-bottom-color: #f472b6 !important; }

/* ── Split login panel ── */
.login-left {
    background: linear-gradient(160deg, #1a0a20 0%, #2a1040 60%, #1a1535 100%);
    border-radius: 16px;
    padding: 48px 40px;
    height: 100%;
    min-height: 520px;
    border: 1px solid #3a1a45;
}
.login-logo {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    color: #ead8ee;
    margin-bottom: 8px;
}
.login-tagline {
    font-size: 14px;
    color: #8a6888;
    margin-bottom: 40px;
}
.login-stat-row {
    display: flex;
    gap: 32px;
    margin-top: 40px;
}
.login-stat-num { font-size: 24px; font-weight: 700; color: #f472b6; }
.login-stat-num.green { color: #34d399; }
.login-stat-num.purple { color: #c084fc; }
.login-stat-lbl { font-size: 12px; color: #7a5888; margin-top: 2px; }
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

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="medium")

    with left:
        st.markdown("""
        <div class="login-left">
            <div class="login-logo">✦ Job Tracker</div>
            <div class="login-tagline">Your AI-powered career command center</div>
            <div style="font-size:28px;font-weight:700;color:#ead8ee;line-height:1.3;margin-bottom:12px;">
                Land Your<br><span style="color:#f472b6;">Dream Job</span>
            </div>
            <div style="font-size:14px;color:#8a6888;line-height:1.7;max-width:320px;">
                Track applications, scan your resume against job descriptions, and get AI-powered match scores — all in one place.
            </div>
            <div class="login-stat-row">
                <div><div class="login-stat-num">AI</div><div class="login-stat-lbl">Match Scoring</div></div>
                <div><div class="login-stat-num green">Auto</div><div class="login-stat-lbl">Job Scraping</div></div>
                <div><div class="login-stat-num purple">Live</div><div class="login-stat-lbl">Status Tracking</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        tab = st.session_state["login_tab"]

        # ── SIGN IN ──
        if tab == "login":
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:26px;font-weight:700;color:#ead8ee;margin-bottom:4px;text-align:center;'>Welcome Back</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:13px;color:#8a6888;margin-bottom:28px;text-align:center;'>Sign in to continue your journey</div>", unsafe_allow_html=True)

            u = st.text_input("Username", key="login_username", placeholder="Enter your username")
            p = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            # Link-style Forgot Password right under password field
            st.markdown('<div class="forgot-pw-container">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="go_forgot"):
                st.session_state["login_tab"] = "forgot"
                st.session_state["reset_sent"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Remember me checkbox
            st.checkbox("Remember me", key="remember_me")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if st.button("Sign In", key="do_login", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("Invalid username or password")

            st.markdown("""
            <div style='text-align:center;margin-top:20px;font-size:13px;color:#7a5878;'>
                Don't have an account?
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sign up for free →", key="go_signup", use_container_width=True):
                st.session_state["login_tab"] = "signup"
                st.rerun()

        # ── FORGOT PASSWORD ──
        elif tab == "forgot":
            st.markdown("<div style='font-size:26px;font-weight:700;color:#ead8ee;margin-bottom:4px;'>Reset Password</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:13px;color:#8a6888;margin-bottom:28px;'>Enter your username and we'll send you a reset link</div>", unsafe_allow_html=True)

            if st.session_state["reset_sent"]:
                st.markdown("""
                <div style="background:#1a3a2a;border:1px solid #2a6a4a;border-radius:10px;padding:20px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:8px;">📬</div>
                    <div style="font-size:15px;font-weight:600;color:#34d399;margin-bottom:6px;">Reset email sent!</div>
                    <div style="font-size:13px;color:#8a9888;">Check your inbox and follow the link to reset your password.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                reset_u = st.text_input("Username", key="reset_username", placeholder="Enter your username")
                if st.button("Send Reset Link", key="do_reset", use_container_width=True):
                    if not reset_u:
                        st.error("Please enter your username")
                    else:
                        send_password_reset(reset_u)
                        st.session_state["reset_sent"] = True
                        st.rerun()

            st.markdown("<div style='text-align:center;margin-top:20px;font-size:13px;color:#7a5878;'>Remember your password?</div>", unsafe_allow_html=True)
            if st.button("Back to Sign In →", key="back_login", use_container_width=True):
                st.session_state["login_tab"] = "login"
                st.session_state["reset_sent"] = False
                st.rerun()

        # ── SIGN UP ──
        else:
            st.markdown("<div style='font-size:26px;font-weight:700;color:#ead8ee;margin-bottom:4px;'>Create Account</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:13px;color:#8a6888;margin-bottom:24px;'>Start your job tracking journey today</div>", unsafe_allow_html=True)

            new_u = st.text_input("Username", key="signup_username", placeholder="Choose a username")
            new_e = st.text_input("Email", key="signup_email", placeholder="Enter your real email address")
            new_p = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a strong password")

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
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="agree_terms")

            if st.button("Create Account", key="do_signup", use_container_width=True):
                if not new_u or not new_e or not new_p:
                    st.error("Please fill in all fields")
                elif new_p != confirm_p:
                    st.error("Passwords do not match")
                elif not agree:
                    st.error("Please agree to the Terms of Service to continue")
                else:
                    ok, err = sign_up_user(new_u, new_p, new_e)
                    if ok:
                        st.success("Account created! Sign in below.")
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
    cards = [(sc1, "📋", total, "#e8d8ec", "Total Applications"), (sc2, "🗓️", interviews, "#f472b6", "Interviews"), (sc3, "✅", offers, "#34d399", "Offers"), (sc4, "🎯", avg_score, "#c084fc", "Avg AI Match")]
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

    with st.expander("➕  Add New Application"):
        c1, c2 = st.columns(2)
        with c1: comp = st.text_input("Company Name")
        with c2: pos = st.text_input("Position Title")
        url_in = st.text_input("Job Posting URL")
        if st.button("✨ Auto-Fill from URL"):
            if url_in:
                with st.spinner("Scraping..."):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)
        final_desc = st.text_area("Job Description", value=st.session_state["formatted_desc"], height=220)
        up_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
        if up_file: st.session_state["resume_txt"] = extract_text_from_upload(up_file)
        applied_date = st.date_input("Date Applied", format="MM/DD/YYYY")

        if st.button("💾 Save Application"):
            resume_url = upload_resume(up_file, st.session_state["username"]) if up_file else None
            score = "N/A"
            if st.session_state.get("resume_txt") and final_desc:
                score = get_ai_match_feedback(final_desc, st.session_state["resume_txt"]).get("score", "N/A")
            if save_job(company=comp, position=pos, description=final_desc, job_url=url_in, resume_url=resume_url, match_score=score, applied_date=applied_date):
                st.success("Saved!")
                st.rerun()

    st.divider()

    if jobs_list:
        df = pd.DataFrame(jobs_list)
        for idx, row in df.iterrows():
            with st.container(border=True):
                cols = st.columns([2, 2, 1, 1, 1])
                cols[0].write(f"**{row['company']}**")
                cols[1].write(row['position'])
                cols[2].write(row['match_score'])
                if cols[4].button("🗑", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                    st.rerun()
    else:
        st.info("No applications yet.")
