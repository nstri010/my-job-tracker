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


# LOGIN

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


# MAIN APP

if st.session_state["logged_in"]:

    t1, t2 = st.columns([5, 1])

    with t1:
        st.title("Job Tracker")

    with t2:
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
            applied_date = st.date_input("Date Applied")

        if st.button("🔍 Scan Resume"):
            if final_desc and st.session_state.get("resume_txt"):
                with st.spinne
