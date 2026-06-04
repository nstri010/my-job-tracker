import streamlit as st
import pandas as pd
from datetime import datetime

from storage import (
    load_jobs,
    save_job,
    delete_job,
    sign_up_user,
    login_user,
    upload_resume,
    update_job_full,
    send_password_reset,
)
from utils import (
    scrape_job_link,
    clean_description_with_ai,
    get_ai_match_feedback,
    extract_text_from_upload,
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: #f5f4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"]          { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMain"]            { padding: 0 !important; }
section[data-testid="stMain"] > div { padding: 0 !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* ── Typography ── */
h1,h2,h3,h4 { font-family: 'DM Serif Display', serif !important; color: #1a1a18 !important; }
p, label, span, div { font-family: 'DM Sans', sans-serif !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #e2e0d8 !important;
    border-radius: 8px !important;
    color: #1a1a18 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 12px !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #639922 !important;
    box-shadow: 0 0 0 3px rgba(99,153,34,0.1) !important;
    outline: none !important;
}

/* ── Labels ── */
.stTextInput label, .stTextArea label, .stDateInput label,
.stFileUploader label, .stSelectbox label {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #888780 !important;
    margin-bottom: 4px !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1px solid #d4d2ca !important;
    background: #ffffff !important;
    color: #1a1a18 !important;
    padding: 8px 16px !important;
    height: auto !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #f0eeea !important;
    border-color: #c8c6be !important;
}
/* Primary button via key pattern — use class override */
button[kind="primary"], .btn-primary > button {
    background: #3B6D11 !important;
    color: #ffffff !important;
    border-color: #3B6D11 !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #e2e0d8 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploadDropzone"] {
    background: #fafaf8 !important;
    border: 1px dashed #d4d2ca !important;
    border-radius: 8px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #e2e0d8 !important;
    border-radius: 12px !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] summary {
    padding: 14px 18px !important;
}

/* ── Divider ── */
hr { border-color: #e8e6de !important; margin: 0 !important; }

/* ── Checkbox ── */
.stCheckbox span { font-size: 13px !important; color: #5a5a58 !important; }

/* ── Alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 8px !important;
    font-size: 13px !important;
}
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
    st.markdown("""
    <div style="min-height:100vh;background:#f5f4f0;display:flex;align-items:center;justify-content:center;padding:40px 20px;">
    """, unsafe_allow_html=True)

    left, gap, right = st.columns([1.1, 0.1, 1])

    with left:
        st.markdown("""
        <div style="background:#1a1a18;border-radius:20px;padding:48px 44px;height:100%;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:48px;">
                <div style="width:10px;height:10px;border-radius:50%;background:#97C459;"></div>
                <span style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;color:#97C459;letter-spacing:0.05em;">JOBTRACK</span>
            </div>
            <div style="font-family:'DM Serif Display',serif;font-size:52px;font-weight:400;color:#f5f4f0;line-height:1.05;margin-bottom:20px;">
                Your career,<br><span style="color:#97C459;">organised.</span>
            </div>
            <div style="font-family:'DM Sans',sans-serif;font-size:14px;color:#888780;line-height:1.7;margin-bottom:40px;">
                Track every application, scan your resume against job descriptions, and keep your job search on track — all in one clean workspace.
            </div>
            <div style="display:flex;flex-direction:column;gap:16px;">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">🎯</div>
                    <div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;color:#e8e6de;">AI resume match score</div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:#666664;margin-top:2px;">See how well your resume fits each role</div>
                    </div>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">⚡</div>
                    <div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;color:#e8e6de;">One-click auto-fill</div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:#666664;margin-top:2px;">Paste a URL and we extract the job details</div>
                    </div>
                </div>
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:rgba(151,196,89,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:15px;">📋</div>
                    <div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;color:#e8e6de;">Full application vault</div>
                        <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:#666664;margin-top:2px;">Sort, filter and track every stage</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        tab = st.session_state["auth_tab"]

        if tab == "login":
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-size:36px;margin-bottom:6px;'>Welcome back</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#888780;font-size:14px;margin-bottom:32px;'>Sign in to your account</p>", unsafe_allow_html=True)

            u = st.text_input("Username", key="li_u", placeholder="Your username")
            p = st.text_input("Password", type="password", key="li_p", placeholder="Your password")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if st.button("Sign in →", use_container_width=True, key="do_login"):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    cookie_manager.set("jobtrack_user", u, max_age=30*24*3600)
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
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
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            st.markdown("<h2 style='font-size:36px;margin-bottom:6px;'>Create account</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color:#888780;font-size:14px;margin-bottom:28px;'>Start tracking your job search today</p>", unsafe_allow_html=True)

            new_u = st.text_input("Username", key="su_u", placeholder="Choose a username")
            new_e = st.text_input("Email", key="su_e", placeholder="your@email.com")
            new_p = st.text_input("Password", type="password", key="su_p", placeholder="At least 8 characters")

            if new_p:
                label, color, pct = password_strength(new_p)
                st.markdown(f"""
                <div style="margin-top:-6px;margin-bottom:10px;">
                    <div style="background:#e8e6de;border-radius:4px;height:4px;width:100%;overflow:hidden;">
                        <div style="background:{color};height:4px;width:{pct}%;border-radius:4px;"></div>
                    </div>
                    <div style="text-align:right;font-size:11px;color:{color};margin-top:3px;font-weight:600;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

            conf_p = st.text_input("Confirm password", type="password", key="su_cp", placeholder="Re-enter password")
            if conf_p:
                if new_p == conf_p:
                    st.markdown("<div style='font-size:12px;color:#3B6D11;margin-top:-6px;margin-bottom:8px;'>✓ Passwords match</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-size:12px;color:#A32D2D;margin-top:-6px;margin-bottom:8px;'>✗ Passwords do not match</div>", unsafe_allow_html=True)

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

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:13px;color:#aaa9a6;'>Already have an account?</div>", unsafe_allow_html=True)
            if st.button("Sign in", use_container_width=True, key="go_login"):
                st.session_state["auth_tab"] = "login"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════
jobs_list = load_jobs()

# ── Top nav ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#ffffff;border-bottom:1px solid #e8e6de;padding:0 32px;height:56px;display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#639922;"></div>
        <span style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;color:#3B6D11;letter-spacing:0.05em;">JOBTRACK</span>
    </div>
    <div style="display:flex;align-items:center;gap:16px;">
        <span style="font-size:13px;color:#888780;font-family:'DM Sans',sans-serif;">Signed in as <strong style="color:#1a1a18;">{st.session_state['username']}</strong></span>
    </div>
</div>
""", unsafe_allow_html=True)

nav_c, sign_out_c = st.columns([10, 1])
with sign_out_c:
    if st.button("Sign out", key="signout"):
        cookie_manager.delete("jobtrack_user")
        st.session_state.clear()
        st.rerun()

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────
st.markdown("""
<div style="padding:0 32px;margin-bottom:24px;">
    <h1 style="font-size:36px;margin-bottom:4px;">My Applications</h1>
    <p style="font-size:14px;color:#888780;margin:0;">Track, match, and manage your job search in one place.</p>
</div>
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

st.markdown("<div style='padding:0 32px;'>", unsafe_allow_html=True)
sc1, sc2, sc3, sc4 = st.columns(4)

def stat_card(col, label, value, accent="#1a1a18"):
    with col:
        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e8e6de;border-radius:12px;padding:18px 20px;">
            <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#aaa9a6;margin-bottom:8px;">{label}</div>
            <div style="font-size:28px;font-weight:600;font-family:'DM Sans',sans-serif;color:{accent};line-height:1;">{value}</div>
        </div>
        """, unsafe_allow_html=True)

stat_card(sc1, "Total applied",    total,      "#1a1a18")
stat_card(sc2, "Interviews",       interviews, "#854F0B")
stat_card(sc3, "Offers",           offers,     "#3B6D11")
stat_card(sc4, "Avg match score",  avg_score,  "#185FA5")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Add new application ───────────────────────────────────────────
st.markdown("<div style='padding:0 32px;'>", unsafe_allow_html=True)

with st.expander("➕  Add new application", expanded=not bool(jobs_list)):
    c1, c2 = st.columns(2)
    with c1:
        comp = st.text_input("Company name", placeholder="e.g. Stripe")
    with c2:
        pos  = st.text_input("Position title", placeholder="e.g. Product Designer")

    url_in = st.text_input("Job posting URL", placeholder="Paste a URL — we'll auto-fill the description")

    autofill_col, _ = st.columns([1, 4])
    with autofill_col:
        if st.button("⚡ Auto-fill from URL", key="autofill"):
            if url_in:
                with st.spinner("Fetching and formatting job description…"):
                    raw = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw)
            else:
                st.warning("Please enter a URL first.")

    final_desc = st.text_area(
        "Job description",
        value=st.session_state["formatted_desc"],
        height=200,
        placeholder="Auto-filled from URL, or paste manually…",
    )

    col_resume, col_date = st.columns(2)
    with col_resume:
        up_file = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"], label_visibility="visible")
        if up_file is not None:
            st.session_state["resume_txt"] = extract_text_from_upload(up_file)

    with col_date:
        applied_date = st.date_input("Date applied", format="MM/DD/YYYY")

    scan_col, save_col, _ = st.columns([1, 1, 3])

    with scan_col:
        if st.button("🔍 Scan resume", key="scan"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinner("Analysing your resume against the job description…"):
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
            else:
                st.warning("Please add a job description and upload a resume first.")

    with save_col:
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

    # Match results
    if st.session_state["match_data"]:
        match = st.session_state["match_data"]
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#EAF3DE;border:1px solid #C0DD97;border-radius:10px;padding:16px 20px;">
            <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#3B6D11;margin-bottom:6px;">AI Match Result</div>
            <div style="font-size:26px;font-weight:600;color:#3B6D11;font-family:'DM Sans',sans-serif;">{match.get('score', '—')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        for item in match.get("feedback", []):
            if not item.upper().startswith("SCORE:"):
                st.markdown(f"<div style='font-size:13px;color:#444441;padding:2px 0;'>{item}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Career Vault ──────────────────────────────────────────────────
st.markdown("<div style='padding:0 32px;'>", unsafe_allow_html=True)

# Refresh job list after potential save
jobs_list = load_jobs()

vault_header, sort_area = st.columns([2, 3])
with vault_header:
    st.markdown("""
    <div style="padding-top:6px;">
        <h2 style="font-size:24px;margin:0;">Career vault</h2>
    </div>
    """, unsafe_allow_html=True)

with sort_area:
    sc, sd = st.columns(2)
    with sc:
        sort_by = st.selectbox("Sort by", ["Date Applied", "Company", "Position", "Match Score", "Status"], label_visibility="collapsed")
    with sd:
        sort_dir = st.selectbox("Order", ["Newest First", "Oldest First", "A → Z", "Z → A", "Highest First", "Lowest First"], label_visibility="collapsed")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Handle URL param actions (status change / delete)
params = st.query_params
if "delete_id" in params:
    delete_job(params["delete_id"])
    st.query_params.clear()
    st.rerun()
if "set_status_id" in params and "set_status_val" in params:
    update_job_full(params["set_status_id"], {"status": params["set_status_val"]})
    st.query_params.clear()
    st.rerun()

if jobs_list:
    df = pd.DataFrame(jobs_list)

    # Sorting
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
        df = df.sort_values("status",     ascending=(sort_dir == "A → Z"))
    else:
        df = df.sort_values("created_at", ascending=(sort_dir == "Oldest First"))

    def score_color(raw):
        try:
            n = float(str(raw).split("/")[0])
            return "#3B6D11" if n >= 7 else "#854F0B" if n >= 4 else "#A32D2D"
        except: return "#888780"

    # Table header
    st.markdown("""
    <div style="display:grid;grid-template-columns:2fr 2fr 0.8fr 1.4fr 1.1fr 0.9fr 0.5fr;gap:10px;padding:0 16px 8px 16px;">
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Company</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Position</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Match</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Status</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Date applied</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;">Files</span>
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.09em;color:#aaa9a6;"></span>
    </div>
    """, unsafe_allow_html=True)

    rows_html = ""
    for _, row in df.iterrows():
        job_id   = str(row["id"])
        company  = str(row.get("company",  "—"))
        position = str(row.get("position", "—"))
        score    = str(row.get("match_score", "—"))
        status   = str(row.get("status", STATUS_OPTIONS[0]))
        date_str = fmt_date(row.get("created_at", ""))
        resume   = str(row.get("resume_link") or "")
        snapshot = str(row.get("pdf_url") or "")
        sc_col   = score_color(score)
        bg, fg   = STATUS_META.get(status, ("#F1EFE8", "#5F5E5A"))

        opts = "".join(
            '<option value="{v}" {sel}>{v}</option>'.format(
                v=o, sel="selected" if o == status else ""
            ) for o in STATUS_OPTIONS
        )
        onchange = "window.location.href='?set_status_id={id}&set_status_val='+encodeURIComponent(this.value)".format(id=job_id)
        on_del   = "return confirm('Delete this application?')"
        del_url  = "?delete_id={id}".format(id=job_id)

        icon_btn = "display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;border:1px solid #e8e6de;background:#fff;font-size:14px;text-decoration:none;color:#888780;cursor:pointer;"
        icon_dim = "display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:6px;border:1px solid #f0eeea;background:#fafaf8;font-size:14px;color:#ccc;opacity:0.6;"

        resume_cell   = f'<a href="{resume}"   target="_blank" style="{icon_btn}" title="View resume">📄</a>'   if resume   else f'<span style="{icon_dim}" title="No resume">📄</span>'
        snapshot_cell = f'<a href="{snapshot}" target="_blank" style="{icon_btn}" title="View snapshot">📸</a>' if snapshot else f'<span style="{icon_dim}" title="No snapshot">📸</span>'
        delete_cell   = f'<a href="{del_url}" onclick="{on_del}" style="{icon_btn};color:#A32D2D;" title="Delete">✕</a>'

        rows_html += f"""
        <div style="display:grid;grid-template-columns:2fr 2fr 0.8fr 1.4fr 1.1fr 0.9fr 0.5fr;gap:10px;align-items:center;
                    background:#ffffff;border:1px solid #e8e6de;border-radius:10px;padding:12px 16px;margin-bottom:6px;
                    transition:border-color 0.15s;">
            <span style="font-size:13px;font-weight:500;color:#1a1a18;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{company}</span>
            <span style="font-size:13px;color:#5a5a58;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{position}</span>
            <span style="font-size:13px;font-weight:600;color:{sc_col};">{score}</span>
            <select onchange="{onchange}"
                style="background:{bg};color:{fg};border:1px solid {fg}55;border-radius:999px;
                       padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;
                       outline:none;appearance:none;-webkit-appearance:none;font-family:'DM Sans',sans-serif;
                       text-align:center;">
                {opts}
            </select>
            <span style="font-size:12px;color:#aaa9a6;">{date_str}</span>
            <span style="display:flex;gap:6px;">{resume_cell}{snapshot_cell}</span>
            <span>{delete_cell}</span>
        </div>
        """

    st.markdown(rows_html, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background:#ffffff;border:1px dashed #d4d2ca;border-radius:12px;padding:60px 20px;text-align:center;">
        <div style="font-size:36px;margin-bottom:12px;">📭</div>
        <div style="font-size:15px;font-weight:500;color:#444441;margin-bottom:6px;">No applications yet</div>
        <div style="font-size:13px;color:#aaa9a6;">Add your first one above to get started.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="border-top:1px solid #e8e6de;padding:20px 32px;display:flex;align-items:center;justify-content:space-between;">
    <span style="font-size:12px;color:#aaa9a6;font-family:'DM Sans',sans-serif;">JobTrack — AI-powered job search tracker</span>
    <span style="font-size:11px;color:#d4d2ca;font-family:'DM Sans',sans-serif;">Results may vary. Always verify AI suggestions.</span>
</div>
""", unsafe_allow_html=True)
