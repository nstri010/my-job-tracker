import streamlit as st
import pandas as pd
from datetime import datetime

from storage import (
    load_jobs, save_job, delete_job,
    sign_up_user, login_user, upload_resume,
    update_job_full, send_password_reset,
)
from utils import (
    scrape_job_link, clean_description_with_ai,
    get_ai_match_feedback, extract_text_from_upload,
)

import extra_streamlit_components as stx

st.set_page_config(page_title="JobTrack", layout="wide", initial_sidebar_state="collapsed")

# ── Cookie session ────────────────────────────────────────────────
cookie_manager = stx.CookieManager()
_saved_user = cookie_manager.get("jobtrack_user")

if "logged_in"      not in st.session_state: st.session_state["logged_in"]      = bool(_saved_user)
if "username"       not in st.session_state: st.session_state["username"]        = _saved_user or None
if "auth_tab"       not in st.session_state: st.session_state["auth_tab"]        = "login"
if "formatted_desc" not in st.session_state: st.session_state["formatted_desc"]  = ""
if "match_data"     not in st.session_state: st.session_state["match_data"]      = None
if "resume_txt"     not in st.session_state: st.session_state["resume_txt"]      = None
if "reset_sent"     not in st.session_state: st.session_state["reset_sent"]      = False

if not st.session_state["logged_in"] and _saved_user:
    st.session_state["logged_in"] = True
    st.session_state["username"]  = _saved_user

# ── Global CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&family=DM+Serif+Display&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: #f5f4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Remove all Streamlit default padding/margins */
[data-testid="stHeader"]               { display: none !important; }
[data-testid="stMainBlockContainer"]   { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMain"]                 { padding: 0 !important; }
section[data-testid="stMain"] > div    { padding: 0 !important; }
.block-container                       { padding: 0 !important; max-width: 100% !important; }

/* Kill the default gap between Streamlit blocks */
div[data-testid="stVerticalBlock"]     { gap: 0rem !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { padding: 0 !important; }

/* Horizontal block (columns) */
div[data-testid="stHorizontalBlock"]   { gap: 12px !important; align-items: center !important; }

/* ── Typography ── */
h1, h2, h3, h4 {
    font-family: 'DM Serif Display', serif !important;
    color: #1a1a18 !important;
    margin: 0 !important;
}

/* ── Text inputs & textarea ── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stDateInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #dddbd3 !important;
    border-radius: 8px !important;
    color: #1a1a18 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 9px 12px !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: #639922 !important;
    box-shadow: 0 0 0 3px rgba(99,153,34,0.12) !important;
    outline: none !important;
}

/* ── Field labels ── */
.stTextInput  label,
.stTextArea   label,
.stDateInput  label,
.stFileUploader label,
.stSelectbox  label {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #888780 !important;
    margin-bottom: 4px !important;
}

/* ── Buttons — all white by default ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1px solid #dddbd3 !important;
    background: #ffffff !important;
    color: #1a1a18 !important;
    padding: 7px 16px !important;
    height: 36px !important;
    line-height: 1 !important;
    transition: background 0.15s, border-color 0.15s !important;
    white-space: nowrap !important;
}
.stButton > button:hover {
    background: #f0eeea !important;
    border-color: #c8c6be !important;
}

/* ── Selectbox ── */
.stSelectbox [data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #dddbd3 !important;
    border-radius: 8px !important;
    min-height: 36px !important;
}
.stSelectbox [data-baseweb="select"] span {
    font-size: 13px !important;
    color: #1a1a18 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── File uploader — compact ── */
[data-testid="stFileUploadDropzone"] {
    background: #fafaf8 !important;
    border: 1px dashed #dddbd3 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    min-height: 48px !important;
}
[data-testid="stFileUploadDropzone"] p {
    font-size: 13px !important;
    color: #888780 !important;
}

/* ── Expander — white card, visible label ── */
[data-testid="stExpander"] {
    border: 1px solid #dddbd3 !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] > details > summary {
    padding: 14px 20px !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] > details > summary p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #1a1a18 !important;
    opacity: 1 !important;
    visibility: visible !important;
}
[data-testid="stExpander"] > details[open] > summary {
    border-bottom: 1px solid #e8e6de !important;
}
[data-testid="stExpander"] > details > div {
    padding: 20px !important;
}

/* ── Checkbox ── */
.stCheckbox label span { font-size: 13px !important; color: #5a5a58 !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 13px !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid #e8e6de !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────
def password_strength(pw):
    if not pw: return None, None, None
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 12: score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pw): score += 1
    if score <= 1:   return "Weak",        "#ef4444", 20
    elif score == 2: return "Fair",        "#f97316", 40
    elif score == 3: return "Medium",      "#eab308", 65
    elif score == 4: return "Strong",      "#22c55e", 85
    else:            return "Very Strong", "#10b981", 100

def fmt_date(raw):
    try:    return datetime.fromisoformat(str(raw)).strftime("%b %d, %Y")
    except: return str(raw)[:10] if raw else "—"

STATUS_META = {
    "📝 Applied":   ("#E6F1FB", "#185FA5"),
    "📨 Contacted": ("#EEEDFE", "#534AB7"),
    "📅 Interview": ("#FAEEDA", "#854F0B"),
    "✅ Offer":     ("#EAF3DE", "#3B6D11"),
    "❌ Rejected":  ("#FCEBEB", "#A32D2D"),
}
STATUS_OPTIONS = list(STATUS_META.keys())


# ════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ════════════════════════════════════════════════════════════════════
if not st.session_state["logged_in"]:
    left, gap, right = st.columns([1.1, 0.08, 1])

    with left:
        st.markdown("""
        <div style="background:#1a1a18;border-radius:20px;padding:48px 44px;margin:40px 0 40px 40px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:48px;">
                <div style="width:10px;height:10px;border-radius:50%;background:#97C459;"></div>
                <span style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;color:#97C459;letter-spacing:0.05em;">JOBTRACK</span>
            </div>
            <div style="font-family:'DM Serif Display',serif;font-size:48px;font-weight:400;color:#f5f4f0;line-height:1.08;margin-bottom:20px;">
                Your career,<br><span style="color:#97C459;">organised.</span>
            </div>
            <div style="font-size:14px;color:#888780;line-height:1.7;margin-bottom:40px;">
                Track every application, scan your resume against job descriptions, and keep your job search on track — all in one clean workspace.
            </div>
            <div style="display:flex;flex-direction:column;gap:16px;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">🎯</div>
                    <div><div style="font-size:13px;font-weight:600;color:#e8e6de;">AI resume match score</div><div style="font-size:12px;color:#666664;margin-top:2px;">See how well your resume fits each role</div></div>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">⚡</div>
                    <div><div style="font-size:13px;font-weight:600;color:#e8e6de;">One-click auto-fill</div><div style="font-size:12px;color:#666664;margin-top:2px;">Paste a URL and we extract the job details</div></div>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">📋</div>
                    <div><div style="font-size:13px;font-weight:600;color:#e8e6de;">Full application vault</div><div style="font-size:12px;color:#666664;margin-top:2px;">Sort, filter and track every stage</div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        tab = st.session_state["auth_tab"]
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

        if tab == "login":
            st.markdown("<h2 style='font-size:34px;margin-bottom:6px;'>Welcome back</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#888780;font-size:14px;margin-bottom:24px;'>Sign in to your account</p>", unsafe_allow_html=True)
            u = st.text_input("Username", key="li_u", placeholder="Your username")
            p = st.text_input("Password", type="password", key="li_p", placeholder="Your password")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("Sign in →", use_container_width=True, key="do_login"):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    cookie_manager.set("jobtrack_user", u, max_age=30*24*3600)
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:13px;color:#aaa9a6;'>Don't have an account?</div>", unsafe_allow_html=True)
            if st.button("Create account", use_container_width=True, key="go_signup"):
                st.session_state["auth_tab"] = "signup"
                st.rerun()
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.session_state["reset_sent"]:
                st.success("Reset email sent — check your inbox.")
            else:
                forgot_u = st.text_input("Forgot password? Enter username", key="forgot_u", placeholder="Enter username to reset")
                if st.button("Send reset email", key="do_reset"):
                    if forgot_u and send_password_reset(forgot_u):
                        st.session_state["reset_sent"] = True
                        st.rerun()
                    else:
                        st.error("Username not found.")

        elif tab == "signup":
            st.markdown("<h2 style='font-size:34px;margin-bottom:6px;'>Create account</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#888780;font-size:14px;margin-bottom:20px;'>Start tracking your job search today</p>", unsafe_allow_html=True)
            new_u = st.text_input("Username", key="su_u", placeholder="Choose a username")
            new_e = st.text_input("Email", key="su_e", placeholder="your@email.com")
            new_p = st.text_input("Password", type="password", key="su_p", placeholder="At least 8 characters")
            if new_p:
                label, color, pct = password_strength(new_p)
                st.markdown(f"""<div style="margin-top:-4px;margin-bottom:10px;">
                    <div style="background:#e8e6de;border-radius:4px;height:4px;width:100%;overflow:hidden;">
                        <div style="background:{color};height:4px;width:{pct}%;border-radius:4px;"></div>
                    </div>
                    <div style="text-align:right;font-size:11px;color:{color};margin-top:3px;font-weight:600;">{label}</div>
                </div>""", unsafe_allow_html=True)
            conf_p = st.text_input("Confirm password", type="password", key="su_cp", placeholder="Re-enter password")
            if conf_p:
                if new_p == conf_p:
                    st.markdown("<div style='font-size:12px;color:#3B6D11;margin-top:-4px;margin-bottom:6px;'>✓ Passwords match</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-size:12px;color:#A32D2D;margin-top:-4px;margin-bottom:6px;'>✗ Passwords do not match</div>", unsafe_allow_html=True)
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            if st.button("Create account →", use_container_width=True, key="do_signup"):
                if not new_u or not new_e or not new_p:
                    st.error("Please fill in all fields.")
                elif "@" not in new_e or "." not in new_e:
                    st.error("Please enter a valid email address.")
                elif new_p != conf_p:
                    st.error("Passwords do not match.")
                elif not agree:
                    st.error("Please agree to the Terms of Service to continue.")
                elif password_strength(new_p)[0] == "Weak":
                    st.warning("Please choose a stronger password.")
                else:
                    ok, err = sign_up_user(new_u, new_p, new_e)
                    if ok:
                        st.success("Account created! Check your email to confirm, then sign in.")
                        st.session_state["auth_tab"] = "login"
                        st.rerun()
                    else:
                        st.error(f"Sign up failed: {err}")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:13px;color:#aaa9a6;'>Already have an account?</div>", unsafe_allow_html=True)
            if st.button("Sign in", use_container_width=True, key="go_login"):
                st.session_state["auth_tab"] = "login"
                st.rerun()

    st.stop()


# ════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════
jobs_list = load_jobs()

# ── Nav bar: pure HTML + sign-out button rendered in last column ──
st.markdown("""
<style>
/* Nav bar wrapper */
.nav-bar {
    background: #ffffff;
    border-bottom: 1px solid #e8e6de;
    height: 56px;
    display: flex;
    align-items: center;
    padding: 0 24px;
    position: relative;
}
.nav-logo {
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #639922;
    display: inline-block;
}
.nav-brand {
    font-size: 14px;
    font-weight: 600;
    color: #3B6D11;
    letter-spacing: 0.06em;
}
.nav-user {
    margin-left: auto;
    font-size: 13px;
    color: #888780;
    margin-right: 12px;
}
.nav-user strong { color: #1a1a18; }

/* Make the sign-out button sit flush in the nav */
div[data-testid="stHorizontalBlock"].nav-row {
    margin: 0 !important;
    padding: 0 !important;
    height: 56px !important;
    align-items: center !important;
    background: #ffffff !important;
    border-bottom: 1px solid #e8e6de !important;
    padding: 0 24px !important;
    gap: 0 !important;
}
</style>
""", unsafe_allow_html=True)

nav_logo_col, nav_user_col, nav_btn_col = st.columns([3, 6, 1])
with nav_logo_col:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;height:56px;background:#ffffff;padding-left:8px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#639922;flex-shrink:0;"></div>
        <span style="font-size:14px;font-weight:600;color:#3B6D11;letter-spacing:0.06em;">JOBTRACK</span>
    </div>""", unsafe_allow_html=True)
with nav_user_col:
    st.markdown(f"""
    <div style="height:56px;background:#ffffff;display:flex;align-items:center;justify-content:flex-end;padding-right:16px;">
        <span style="font-size:13px;color:#888780;">Signed in as <strong style="color:#1a1a18;">{st.session_state['username']}</strong></span>
    </div>""", unsafe_allow_html=True)
with nav_btn_col:
    st.markdown("""<div style="height:56px;background:#ffffff;display:flex;align-items:center;padding-right:8px;">""", unsafe_allow_html=True)
    if st.button("Sign out", key="signout"):
        cookie_manager.delete("jobtrack_user")
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Thin white line under nav to cover any gap
st.markdown("<div style='background:#ffffff;height:2px;border-bottom:1px solid #e8e6de;'></div>", unsafe_allow_html=True)

# ── Page content wrapper ──────────────────────────────────────────
st.markdown("<div style='padding:32px 32px 0 32px;'>", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────
st.markdown("""
<h1 style='font-size:34px;margin-bottom:4px;'>My Applications</h1>
<p style='font-size:14px;color:#888780;margin:0 0 24px 0;'>Track, match, and manage your job search in one place.</p>
""", unsafe_allow_html=True)

# ── Stat cards ────────────────────────────────────────────────────
if jobs_list:
    df_stats = pd.DataFrame(jobs_list)
    total      = len(df_stats)
    interviews = len(df_stats[df_stats.get("status", pd.Series(dtype=str)).str.contains("Interview", na=False)]) if "status" in df_stats else 0
    offers     = len(df_stats[df_stats.get("status", pd.Series(dtype=str)).str.contains("Offer",     na=False)]) if "status" in df_stats else 0
    def parse_score(s):
        try:
            parts = str(s).split("/")
            n = float(parts[0])
            return (n / float(parts[1])) * 100 if len(parts) > 1 and float(parts[1]) != 0 else n
        except: return None
    scores    = df_stats["match_score"].apply(parse_score).dropna() if "match_score" in df_stats else pd.Series()
    avg_score = f"{scores.mean():.0f}%" if len(scores) > 0 else "—"
else:
    total = interviews = offers = 0
    avg_score = "—"

sc1, sc2, sc3, sc4 = st.columns(4)
def stat_card(col, label, value, accent="#1a1a18"):
    with col:
        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e8e6de;border-radius:12px;padding:18px 20px;margin-bottom:0;">
            <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#aaa9a6;margin-bottom:8px;">{label}</div>
            <div style="font-size:28px;font-weight:600;font-family:'DM Sans',sans-serif;color:{accent};line-height:1;">{value}</div>
        </div>""", unsafe_allow_html=True)

stat_card(sc1, "Total applied",   total,      "#1a1a18")
stat_card(sc2, "Interviews",      interviews, "#854F0B")
stat_card(sc3, "Offers",          offers,     "#3B6D11")
stat_card(sc4, "Avg match score", avg_score,  "#185FA5")

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Add new application (expander) ───────────────────────────────
with st.expander("➕  Add new application", expanded=not bool(jobs_list)):
    c1, c2 = st.columns(2)
    with c1:
        comp = st.text_input("Company name", placeholder="e.g. Stripe")
    with c2:
        pos = st.text_input("Position title", placeholder="e.g. Product Designer")

    url_in = st.text_input("Job posting URL", placeholder="Paste a URL — we'll auto-fill the description")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    af_col, _ = st.columns([1, 5])
    with af_col:
        if st.button("⚡ Auto-fill from URL", key="autofill"):
            if url_in:
                with st.spinner("Fetching and formatting job description…"):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)
            else:
                st.warning("Please enter a URL first.")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    final_desc = st.text_area(
        "Job description",
        value=st.session_state["formatted_desc"],
        height=180,
        placeholder="Auto-filled from URL, or paste manually…",
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    # Resume and date — 1:1 columns so they're the same width
    col_resume, col_date = st.columns([1, 1])
    with col_resume:
        up_file = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
        if up_file is not None:
            st.session_state["resume_txt"] = extract_text_from_upload(up_file)
    with col_date:
        applied_date = st.date_input("Date applied", format="MM/DD/YYYY")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    btn_c1, btn_c2, _ = st.columns([1, 1, 4])
    with btn_c1:
        if st.button("🔍 Scan resume", key="scan"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Analysing your resume against the job description…"):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
            else:
                st.warning("Please add a job description and upload a resume first.")
    with btn_c2:
        if st.button("💾 Save application", key="save"):
            resume_url = None
            score = "—"
            if up_file is not None:
                resume_url = upload_resume(up_file, st.session_state["username"])
            if st.session_state.get("resume_txt") and final_desc:
                with st.spinner("Saving application…"):
                    match_result = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
                    st.session_state["match_data"] = match_result
                    score = match_result.get("score", "—")
            elif st.session_state.get("match_data"):
                score = st.session_state["match_data"].get("score", "—")
            success = save_job(
                company=comp, position=pos, description=final_desc,
                job_url=url_in, resume_url=resume_url,
                match_score=score, applied_date=applied_date,
            )
            if success:
                st.session_state["resume_txt"]     = None
                st.session_state["match_data"]     = None
                st.session_state["formatted_desc"] = ""
                st.success("Application saved!")
                st.rerun()
            else:
                st.error("Failed to save — please try again.")

    if st.session_state["match_data"]:
        match = st.session_state["match_data"]
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#EAF3DE;border:1px solid #C0DD97;border-radius:10px;padding:14px 18px;">
            <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#3B6D11;margin-bottom:4px;">AI Match Result</div>
            <div style="font-size:24px;font-weight:600;color:#3B6D11;">{match.get('score', '—')}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for item in match.get("feedback", []):
            if not item.upper().startswith("SCORE:"):
                st.markdown(f"<div style='font-size:13px;color:#444441;padding:2px 0;'>{item}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close page wrapper

# ── Career Vault ──────────────────────────────────────────────────
st.markdown("<div style='padding:24px 32px 0 32px;'>", unsafe_allow_html=True)

jobs_list = load_jobs()

# Handle URL param actions
params = st.query_params
if "delete_id" in params:
    delete_job(params["delete_id"])
    st.query_params.clear()
    st.rerun()
if "set_status_id" in params and "set_status_val" in params:
    update_job_full(params["set_status_id"], {"status": params["set_status_val"]})
    st.query_params.clear()
    st.rerun()

# Vault header + sort controls
v_title_col, v_sort_col = st.columns([2, 3])
with v_title_col:
    st.markdown("<h2 style='font-size:22px;padding-top:4px;'>Career vault</h2>", unsafe_allow_html=True)
with v_sort_col:
    sv_col, sd_col = st.columns(2)
    with sv_col:
        sort_by = st.selectbox("Sort by", ["Date Applied", "Company", "Position", "Match Score", "Status"], label_visibility="collapsed")
    with sd_col:
        sort_dir = st.selectbox("Order", ["Newest First", "Oldest First", "A → Z", "Z → A", "Highest First", "Lowest First"], label_visibility="collapsed")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

if jobs_list:
    df = pd.DataFrame(jobs_list)

    if sort_by == "Company":
        df = df.sort_values("company",    ascending=(sort_dir == "A → Z"))
    elif sort_by == "Position":
        df = df.sort_values("position",   ascending=(sort_dir == "A → Z"))
    elif sort_by == "Match Score":
        def sv(s):
            try: return int(str(s).split("/")[0])
            except: return 0
        df["_sn"] = df["match_score"].apply(sv)
        df = df.sort_values("_sn", ascending=(sort_dir == "Lowest First"))
    elif sort_by == "Status":
        df = df.sort_values("status", ascending=(sort_dir == "A → Z"))
    else:
        df = df.sort_values("created_at", ascending=(sort_dir == "Oldest First"))

    def score_color(raw):
        try:
            n = float(str(raw).split("/")[0])
            return "#3B6D11" if n >= 7 else "#854F0B" if n >= 4 else "#A32D2D"
        except: return "#888780"

    cols = "1.8fr 1.8fr 0.7fr 1.5fr 1fr 0.8fr 0.4fr"

    header = f"""
    <div style="display:grid;grid-template-columns:{cols};gap:8px;padding:0 14px 8px 14px;margin-top:2px;">
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Company</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Position</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Match</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Status</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Date applied</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Files</span>
        <span></span>
    </div>"""

    rows_html = ""
    for _, row in df.iterrows():
        job_id   = str(row["id"])
        company  = str(row.get("company",     "—"))
        position = str(row.get("position",    "—"))
        score    = str(row.get("match_score", "—"))
        status   = str(row.get("status",      STATUS_OPTIONS[0]))
        date_str = fmt_date(row.get("created_at", ""))
        resume   = str(row.get("resume_link") or "")
        snapshot = str(row.get("pdf_url")     or "")
        sc_col   = score_color(score)
        bg, fg   = STATUS_META.get(status, ("#F1EFE8", "#5F5E5A"))

        opts = "".join(
            '<option value="{v}" {sel}>{v}</option>'.format(v=o, sel="selected" if o == status else "")
            for o in STATUS_OPTIONS
        )
        onchange = "window.location.href='?set_status_id={id}&set_status_val='+encodeURIComponent(this.value)".format(id=job_id)
        del_url  = "?delete_id={id}".format(id=job_id)
        on_del   = "return confirm('Delete this application?')"

        ibtn = "display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;border:1px solid #e8e6de;background:#fff;font-size:13px;text-decoration:none;color:#888780;cursor:pointer;"
        idim = "display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:6px;border:1px solid #f0eeea;background:#fafaf8;font-size:13px;color:#ccc;opacity:0.5;"

        res_cell  = f'<a href="{resume}"   target="_blank" style="{ibtn}">📄</a>' if resume   else f'<span style="{idim}">📄</span>'
        snap_cell = f'<a href="{snapshot}" target="_blank" style="{ibtn}">📸</a>' if snapshot else f'<span style="{idim}">📸</span>'
        del_cell  = f'<a href="{del_url}" onclick="{on_del}" style="{ibtn};color:#A32D2D;">✕</a>'

        rows_html += f"""
        <div style="display:grid;grid-template-columns:{cols};gap:8px;align-items:center;
                    background:#ffffff;border:1px solid #e8e6de;border-radius:10px;
                    padding:11px 14px;margin-bottom:5px;">
            <span style="font-size:13px;font-weight:500;color:#1a1a18;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{company}</span>
            <span style="font-size:13px;color:#5a5a58;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{position}</span>
            <span style="font-size:13px;font-weight:600;color:{sc_col};">{score}</span>
            <span>
                <select onchange="{onchange}" style="background:{bg};color:{fg};border:1px solid {fg}44;
                    border-radius:999px;padding:3px 10px;font-size:11px;font-weight:600;
                    cursor:pointer;outline:none;appearance:none;-webkit-appearance:none;
                    font-family:'DM Sans',sans-serif;max-width:130px;display:inline-block;">
                    {opts}
                </select>
            </span>
            <span style="font-size:12px;color:#aaa9a6;">{date_str}</span>
            <span style="display:flex;gap:5px;align-items:center;">{res_cell}{snap_cell}</span>
            <span>{del_cell}</span>
        </div>"""

    st.markdown(header + rows_html, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background:#ffffff;border:1px dashed #dddbd3;border-radius:12px;padding:56px 20px;text-align:center;margin-top:4px;">
        <div style="font-size:34px;margin-bottom:10px;">📭</div>
        <div style="font-size:15px;font-weight:500;color:#444441;margin-bottom:6px;">No applications yet</div>
        <div style="font-size:13px;color:#aaa9a6;">Add your first one above to get started.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="border-top:1px solid #e8e6de;padding:18px 32px;display:flex;align-items:center;justify-content:space-between;">
    <span style="font-size:12px;color:#aaa9a6;">JobTrack — AI-powered job search tracker</span>
    <span style="font-size:11px;color:#d4d2ca;">Results may vary. Always verify AI suggestions.</span>
</div>
""", unsafe_allow_html=True)
