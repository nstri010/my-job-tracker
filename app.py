import streamlit as st
import pandas as pd
import os
import subprocess

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

# --- PLAYWRIGHT INSTALLATION ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Browser install error: {e}")

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Job Tracker",
    page_icon="📂",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""

if "match_data" not in st.session_state:
    st.session_state["match_data"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None


# --- AUTHENTICATION UI ---
if not st.session_state["logged_in"]:
    st.title("🔐 Job Tracker Login")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

    with tab2:
        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")
        
        if st.button("Create Account"):
            if sign_up_user(new_user, new_pass):
                st.success("Account created! You can now log in.")
            else:
                st.error("Username already exists or error occurred.")


# --- MAIN APPLICATION UI ---
if st.session_state["logged_in"]:
    
    # Header Section
    top1, top2 = st.columns([5, 1])
    with top1:
        st.title(f"📂 {st.session_state['username']}'s Job Tracker")
    with top2:
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- ADD NEW APPLICATION SECTION ---
    with st.expander("➕ Add New Application", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            comp = st.text_input("Company Name", placeholder="e.g. Amazon")
        with c2:
            pos = st.text_input("Position Title", placeholder="e.g. Data Analyst")

        url_in = st.text_input("Job Posting URL", placeholder="Paste the link to the job here...")

        # Auto-Fill Logic
        if st.button("✨ Auto-Fill Description"):
            if url_in:
                with st.spinner("Filling out description... Just a few moments"):
                    raw_content = scrape_job_link(url_in)
                    st.session_state["formatted_desc"] = clean_description_with_ai(raw_content)
            else:
                st.warning("Please provide a URL first.")

        final_desc = st.text_area(
            "Job Description", 
            value=st.session_state["formatted_desc"], 
            height=250,
            help="The AI uses this text to match against your resume."
        )

        col1, col2 = st.columns(2)
        with col1:
            up_file = st.file_uploader("Upload Resume used for this role", type=["pdf", "docx"])
        with col2:
            applied_date = st.date_input("Date Applied")

        # --- RESUME SCANNER LOGIC ---
        if st.button("🔍 Scan Resume"):
            if final_desc and up_file:
                # This is the spinner you requested
                with st.spinner("Using AI to analyze and match resume..."):
                    resume_txt = extract_text_from_upload(up_file)
                    st.session_state["match_data"] = get_ai_match_feedback(final_desc, resume_txt)
            else:
                st.error("Please provide both a Job Description and a Resume to scan.")

        # Display AI Match Results
        if st.session_state["match_data"]:
            match = st.session_state["match_data"]
            
            # Show the Score next to the target emoji
            st.success(f"🎯 {match.get('score', 'N/A')}")
            
            # Display detailed feedback
            for item in match.get("feedback", []):
                # Filter out the 'Rating:' line so it doesn't repeat
                if not item.lower().startswith("rating:"):
                    st.write(item)

        # Save Button
        if st.button("💾 Save Application"):
            if comp and pos:
                res_url = None
                if up_file:
                    res_url = upload_resume(up_file, st.session_state["username"])
                
                score_val = st.session_state["match_data"]["score"] if st.session_state["match_data"] else "N/A"
                
                success = save_job(
                    company=comp,
                    position=pos,
                    description=final_desc,
                    job_url=url_in,
                    resume_url=res_url,
                    match_score=score_val,
                    applied_date=applied_date
                )
                
                if success:
                    st.toast("Application Saved!", icon="✅")
                    st.session_state["formatted_desc"] = ""
                    st.session_state["match_data"] = None
                    st.rerun()
                else:
                    st.error("Failed to save to database.")
            else:
                st.error("Company and Position are required.")

    st.divider()

    # --- DASHBOARD / APPLIED JOBS TABLE ---
    st.header("📋 My Applied Jobs")
    
    jobs_list = load_jobs()
    
    status_options = [
        "📝 Applied",
        "📨 Recruiter Contacted",
        "📅 Interview Scheduled",
        "🎤 Interviewed",
        "⏳ Waiting",
        "✅ Offer",
        "❌ Rejected",
        "🚫 Withdrawn"
    ]

    if jobs_list:
        df = pd.DataFrame(jobs_list)
        
        # Define layout ratios
        col_ratios = [2.0, 2.0, 0.6, 1.2, 0.5, 0.5, 0.5]
        h1, h2, h3, h4, h5, h6, h7 = st.columns(col_ratios)
        
        h1.markdown("**Company**")
        h2.markdown("**Position**")
        h3.markdown("**Match**")
        h4.markdown("**Status**")
        h5.markdown("**Resume**")
        h6.markdown("**Snapshot**")
        h7.markdown("**Delete**")
        
        st.divider()

        for idx, row in df.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns(col_ratios, vertical_alignment="center")
            
            with c1:
                st.write(f"**{row.get('company', '')}**")
            
            with c2:
                st.write(row.get("position", ""))
            
            with c3:
                # Displays the score (e.g. 8/10) saved in the DB
                st.write(row.get("match_score", "N/A"))
            
            with c4:
                current_status = row.get("status", "📝 Applied")
                if current_status not in status_options:
                    current_status = "📝 Applied"
                
                new_status = st.selectbox(
                    "Change Status",
                    status_options,
                    index=status_options.index(current_status),
                    key=f"stat_{row['id']}",
                    label_visibility="collapsed"
                )
                
                if new_status != current_status:
                    update_job_full(row["id"], {"status": new_status})
                    st.rerun()

            with c5:
                res_link = row.get("resume_link")
                if res_link:
                    st.link_button("📄", res_link, use_container_width=True, help="View Resume")
                else:
                    st.write("---")

            with c6:
                snap_pdf = row.get("pdf_url")
                if snap_pdf:
                    st.link_button("🔗", snap_pdf, use_container_width=True, help="View Job Snapshot")
                else:
                    st.write("---")

            with c7:
                if st.button("❌", key=f"del_{row['id']}", use_container_width=True):
                    delete_job(row["id"])
                    st.rerun()

            st.divider()
    else:
        st.info("No applications saved yet. Use the form above to get started!")
