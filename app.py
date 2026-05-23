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

# PLAYWRIGHT INSTALL
if not os.path.exists(
    "/home/appuser/.cache/ms-playwright"
):

    try:

        subprocess.run(
            [
                "playwright",
                "install",
                "chromium"
            ],
            check=True
        )

    except Exception as e:

        st.error(
            f"Browser install error: {e}"
        )

# PAGE CONFIG
st.set_page_config(
    page_title="Job Tracker",
    layout="wide"
)

# SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "formatted_desc" not in st.session_state:
    st.session_state["formatted_desc"] = ""

if "match_data" not in st.session_state:
    st.session_state["match_data"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None


# LOGIN
if not st.session_state["logged_in"]:

    st.title(
        "🔐 Job Tracker Login"
    )

    tab1, tab2 = st.tabs(
        [
            "Login",
            "Sign Up"
        ]
    )

    # LOGIN TAB
    with tab1:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login"
        ):

            if login_user(
                username,
                password
            ):

                st.session_state[
                    "logged_in"
                ] = True

                st.session_state[
                    "username"
                ] = username

                st.rerun()

            else:

                st.error(
                    "Invalid login"
                )

    # SIGNUP TAB
    with tab2:

        new_user = st.text_input(
            "Create Username"
        )

        new_pass = st.text_input(
            "Create Password",
            type="password"
        )

        if st.button(
            "Create Account"
        ):

            if sign_up_user(
                new_user,
                new_pass
            ):

                st.success(
                    "Account created"
                )

            else:

                st.error(
                    "Username already exists"
                )


# MAIN APP
if st.session_state["logged_in"]:

    top1, top2 = st.columns(
        [5,1]
    )

    with top1:

        st.title(
            "📂 Job Tracker"
        )

    with top2:

        if st.button(
            "Sign Out"
        ):

            st.session_state.clear()

            st.rerun()

    # ADD JOB
    with st.expander(
        "➕ Add New Application"
    ):

        c1, c2 = st.columns(
            2
        )

        with c1:

            comp = st.text_input(
                "Company Name"
            )

        with c2:

            pos = st.text_input(
                "Position Title"
            )

        url_in = st.text_input(
            "Job Posting URL"
        )

        if st.button(
            "✨ Auto-Fill"
        ):

            if url_in:

                with st.spinner(
                    "Filling out description... Just a few moments"
                ):

                    raw = scrape_job_link(
                        url_in
                    )

                    st.session_state[
                        "formatted_desc"
                    ] = clean_description_with_ai(
                        raw
                    )

        final_desc = st.text_area(

            "Job Description",

            value=
            st.session_state[
                "formatted_desc"
            ],

            height=220

        )

        st.subheader(
            "🎯 Resume Match"
        )

        col1, col2 = st.columns(
            2
        )

        with col1:

            up_file = st.file_uploader(
                "Upload Resume",
                type=[
                    "pdf",
                    "docx"
                ]
            )

        with col2:

            applied_date = st.date_input(
                "Date Applied"
            )

        if st.button(
            "🔍 Scan Resume"
        ):

            if final_desc and up_file:

                resume_txt = (
                    extract_text_from_upload(
                        up_file
                    )
                )

                st.session_state[
                    "match_data"
                ] = get_ai_match_feedback(
                    final_desc,
                    resume_txt
                )

        # RESULTS
        if st.session_state[
            "match_data"
        ]:

            m = st.session_state[
                "match_data"
            ]

            st.success(
                f"🎯 Resume Match: {m.get('score','N/A')}"
            )

            st.subheader(
                "AI Feedback"
            )

            for item in m.get(
                "feedback",
                []
            ):

                st.write(
                    item
                )

        # SAVE
        if st.button(
            "💾 Save Application"
        ):

            resume_url = None

            score = "N/A"

            if st.session_state[
                "match_data"
            ]:

                score = (
                    st.session_state[
                        "match_data"
                    ].get(
                        "score",
                        "N/A"
                    )
                )

            if up_file:

                resume_url = upload_resume(
                    up_file,
                    st.session_state[
                        "username"
                    ]
                )

            save_job(

                comp,

                pos,

                final_desc,

                url_in,

                resume_url,

                score,

                applied_date=
                applied_date

            )

            st.success(
                "Application saved"
            )

            st.rerun()

    # SAVED JOBS
    st.divider()

    st.header(
        "📋 My Applied Jobs"
    )

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

        df = pd.DataFrame(
            jobs_list
        )

        st.info(
            "💡 Use the dropdown beside status to update progress"
        )

        # HEADER
        h1,h2,h3,h4,h5,h6 = st.columns(
            [2,2,2,2,1,1]
        )

        h1.markdown(
            "**Company**"
        )

        h2.markdown(
            "**Position**"
        )

        h3.markdown(
            "**Match**"
        )

        h4.markdown(
            "**Status**"
        )

        h5.markdown(
            "**Resume**"
        )

        h6.markdown(
            "**Delete**"
        )

        st.divider()

        for idx,row in df.iterrows():

            c1,c2,c3,c4,c5,c6 = st.columns(
                [2,2,2,2,1,1]
            )

            with c1:

    st.markdown(
        "<div style='padding-top:14px'>"
        + str(
            row.get(
                "company",
                ""
            )
        )
        + "</div>",

        unsafe_allow_html=True
    )

with c2:

    st.markdown(
        "<div style='padding-top:14px'>"
        + str(
            row.get(
                "position",
                ""
            )
        )
        + "</div>",

        unsafe_allow_html=True
    )

with c3:

    st.markdown(
        "<div style='padding-top:14px'>"
        + str(
            row.get(
                "score",
                "N/A"
            )
        )
        + "</div>",

        unsafe_allow_html=True
    )

with c4:

    current = row.get(
        "status",
        "📝 Applied"
    )
                if current not in status_options:

                    current = (
                        "📝 Applied"
                    )

                new_status = st.selectbox(

                    "",

                    status_options,

                    index=
                    status_options.index(
                        current
                    ),

                    key=
                    f"status_{row['id']}"

                )

                if new_status != current:

                    update_job_full(

                        row["id"],

                        {
                            "status":
                            new_status
                        }

                    )

                    st.rerun()

            with c5:

                resume = row.get(
                    "resume_link"
                )

                if resume:

                    st.link_button(
                        "📄",
                        resume
                    )

            with c6:

                if st.button(

                    "🗑️",

                    key=
                    f"delete_{row['id']}"

                ):

                    delete_job(
                        row["id"]
                    )

                    st.rerun()

            st.divider()

    else:

        st.write(
            "No applications saved yet."
        )
