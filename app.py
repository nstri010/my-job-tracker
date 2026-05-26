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
    update_job_full,
    send_password_reset
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

# ── SESSION INITIALIZATION ───────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "login_tab" not in st.session_state:
    st.session_state["login_tab"] = "login"

if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""

if "match_data" not in st.session_state:
    st.session_state["match_data"] = None

if "resume_txt" not in st.session_state:
    st.session_state["resume_txt"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None

if "reset_sent" not in st.session_state:
    st.session_state["reset_sent"] = False


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

# ── LOGIN & AUTHENTICATION PAGE ───────────────────────────────────────────────

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

            # CUSTOM CSS FOR HYPERLINK EFFECT
            st.markdown("""
                <style>
                .forgot-link { text-align: right; margin-top: -15px; }
                .forgot-link button {
                    background-color: transparent !important;
                    border: none !important;
                    color: #f472b6 !important;
                    padding: 0 !important;
                    font-size: 14px !important;
                    text-decoration: none !important;
                    transition: color 0.3s ease;
                }
                .forgot-link button:hover {
                    color: #fb923c !important;
                    text-decoration: underline !important;
                }
                </style>
            """, unsafe_allow_html=True)

            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.checkbox("Remember me", key="remember_me")
            with col_right:
                st.markdown('<div class="forgot-link">', unsafe_allow_html=True)
                if st.button("Forgot password?", key="link_forgot"):
                    st.session_state["login_tab"] = "forgot"
                    st.session_state["reset_sent"] = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            if st.button("Sign In", key="do_login", use_container_width=True):
                if login_user(u, p):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = u
                    st.rerun()
                else:
                    st.error("Invalid username or password")

            st.markdown("<div style='text-align:center;margin-top:24px;font-size:14px;color:#6a4868;'>Don't have an account?</div>", unsafe_allow_html=True)
            if st.button("Create a free account →", key="go_signup", use_container_width=True):
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
                    <div style="font-size:13px;color:#8a9888;">Check your inbox to reset your password.</div>
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
            new_e = st.text_input("Email", key="signup_email", placeholder="Enter your email")
            new_p = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a password")

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

            confirm_p = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter password")
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy", key="agree_terms")
            
            if st.button("Create Account", key="do_signup", use_container_width=True):
                if not new_u or not new_e or not new_p:
                    st.error("Please fill in all fields")
                elif new_p != confirm_p:
                    st.error("Passwords do not match")
                elif not agree:
                    st.error("Please agree to the Terms of Service")
                else:
                    ok, err = sign_up_user(new_u, new_p, new_e)
                    if ok:
                        st.success("Account created! Sign in to continue.")
                        st.session_state["login_tab"] = "login"
                        st.rerun()
                    else:
                        st.error(f"Sign up failed: {err}")

            if st.button("Sign in →", key="go_login", use_container_width=True):
                st.session_state["login_tab"] = "login"
                st.rerun()


# ── MAIN APPLICATION CONTENT ──────────────────────────────────────────────────

if st.session_state["logged_in"]:

    t1, t2 = st.columns([5, 1])

    with t1:
        st.title("Job Tracker")
    st.caption("⚠️ This website uses AI which may make errors. Make sure to double-check all results.")

    with t2:
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()

    # ADD JOB SECTION
    with st.expander("➕ Add New Application"):
        c1, c2 = st.columns(2)
        with c1:
            comp = st.text_input("Company Name")
        with c2:
            pos = st.text_input("Position Title")

        url_in = st.text_input("Job Posting URL")

        if st.button("✨ Auto-Fill Details"):
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
            applied_date = st.date_input("Date Applied")

        if st.button("🔍 Scan Resume"):
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

        if st.button("💾 Save"):
            resume_url = None
            score = "N/A"
            if up_file is not None:
                resume_url = upload_resume(up_file, st.session_state["username"])
            if st.session_state.get("resume_txt") and final_desc:
                match_result = get_ai_match_feedback(final_desc, st.session_state["resume_txt"])
                score = match_result.get("score", "N/A")
            
            success = save_job(
                company=comp, position=pos, description=final_desc,
                job_url=url_in, resume_url=resume_url, match_score=score,
                applied_date=applied_date
            )
            if success:
                st.session_state["resume_txt"] = None
                st.session_state["match_data"] = None
                st.session_state["formatted_desc"] = ""
                st.success("Application saved")
                st.rerun()

    st.divider()
    st.header("📋 My Applied Jobs")
    jobs_list = load_jobs()
    status_options = ["📝 Applied", "📨 Contacted", "📅 Interview", "✅ Offer", "❌ Rejected"]

    if jobs_list:
        df = pd.DataFrame(jobs_list)
        
        # Simple Sorting
        df = df.sort_values("created_at", ascending=False)

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
                new_stat = st.selectbox("Status", status_options, index=(status_options.index(curr) if curr in status_options else 0), key=f"s_{row['id']}", label_visibility="collapsed")
                if new_stat != curr:
                    update_job_full(row["id"], {"status": new_stat})
                    st.rerun()

            c5.write(str(row.get("created_at", ""))[:10])
            
            with c6:
                if row.get("resume_link"): st.link_button("📄", row["resume_link"])
                else: st.button("📄", key=f"r_{row['id']}", disabled=True)
            with c7:
                if row.get("pdf_url"): st.link_button("📸", row["pdf_url"])
                else: st.button("📸", key=f"p_{row['id']}", disabled=True)
            if c8.button("❌", key=f"d_{row['id']}"):
                delete_job(row["id"])
                st.rerun()
            st.divider()
    else:
        st.write("No applications found.")
