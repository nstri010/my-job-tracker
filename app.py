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

# INSTALL PLAYWRIGHT
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


# PAGE
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

if "username" not in st.session_state:
    st.session_state["username"] = None


# LOGIN PAGE
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

    with tab1:

        u = st.text_input(
            "Username"
        )

        p = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login"
        ):

            if login_user(
                u,
                p
            ):

                st.session_state[
                    "logged_in"
                ] = True

                st.session_state[
                    "username"
                ] = u

                st.rerun()

            else:

                st.error(
                    "Invalid login"
                )

    with tab2:

        nu = st.text_input(
            "New Username"
        )

        np = st.text_input(
            "New Password",
            type="password"
        )

        if st.button(
            "Create Account"
        ):

            if sign_up_user(
                nu,
                np
            ):

                st.success(
                    "Account created"
                )

            else:

                st.error(
                    "Username exists"
                )


# MAIN APP
if st.session_state["logged_in"]:

    st.title(
        "📂 Job Tracker"
    )

    if st.button(
        "Sign Out"
    ):

        st.session_state.clear()
        st.rerun()

    # ADD JOB
    with st.expander(
        "➕ Add New Application"
    ):

        c1, c2 = st.columns(2)

        with c1:

            comp = st.text_input(
                "Company Name"
            )

        with c2:

            pos = st.text_input(
                "Position"
            )

        url_in = st.text_input(
            "Job URL"
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

            height=200

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
                "Date Applied",
                value=pd.Timestamp.today()
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

        if st.button(
            "💾 Save Application"
        ):

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

            resume_url = None

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
                "Application Saved"
            )

            st.rerun()

    # SAVED JOBS
    st.divider()

    st.header(
        "📋 My Applied Jobs"
    )

    jobs_list = load_jobs()

    if jobs_list:

        df = pd.DataFrame(
            jobs_list
        )

        df[
            "created_at"
        ] = pd.to_datetime(
            df[
                "created_at"
            ]
        )

        df[
            "created_at"
        ] = (

            df[
                "created_at"
            ]

            .dt.tz_convert(
                None
            )

            .dt.strftime(
                "%m/%d/%Y"
            )

        )

        status_options = [

            "▼ 📝 Applied",

            "▼ 📨 Recruiter Contacted",

            "▼ 📅 Interview Scheduled",

            "▼ 🎤 Interviewed",

            "▼ ⏳ Waiting",

            "▼ ✅ Offer",

            "▼ ❌ Rejected",

            "▼ 🚫 Withdrawn"

        ]

        st.info(
            "💡 Click any status with ▼ to update progress"
        )

        edited_df = st.data_editor(

            df,

            width="stretch",

            hide_index=True,

            key="jobs_editor",

            num_rows="dynamic",

            column_config={

                "created_at":

                st.column_config.TextColumn(
                    "Date Applied"
                ),

                "status":

                st.column_config.SelectboxColumn(

                    "Application Status",

                    options=
                    status_options,

                    help=
                    "Click ▼ to edit"

                ),

                "pdf_url":

                st.column_config.LinkColumn(
                    "Snapshot"
                ),

                "resume_link":

                st.column_config.LinkColumn(
                    "Resume"
                ),

                "job_url":

                st.column_config.LinkColumn(
                    "Posting"
                ),

                "id": None,

                "description": None

            }

        )

        # DELETE
        if st.session_state[
            "jobs_editor"
        ][
            "deleted_rows"
        ]:

            for row in st.session_state[
                "jobs_editor"
            ][
                "deleted_rows"
            ]:

                delete_job(
                    df.iloc[
                        row
                    ][
                        "id"
                    ]
                )

            st.rerun()

        # UPDATE
        if st.session_state[
            "jobs_editor"
        ][
            "edited_rows"
        ]:

            updates = st.session_state[
                "jobs_editor"
            ][
                "edited_rows"
            ]

            for row, changes in updates.items():

                update_job_full(

                    df.iloc[
                        row
                    ][
                        "id"
                    ],

                    changes

                )

            st.rerun()

    else:

        st.write(
            "No applications yet."
        )
