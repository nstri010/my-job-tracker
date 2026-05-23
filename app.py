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

# Install Playwright browser if needed
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

# PAGE SETTINGS
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

    with tab1:

        u = st.text_input(
            "Username",
            key="login_user"
        )

        p = st.text_input(
            "Password",
            type="password",
            key="login_pass"
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
                    "Invalid credentials"
                )

    with tab2:

        new_u = st.text_input(
            "Choose Username",
            key="reg_user"
        )

        new_p = st.text_input(
            "Choose Password",
            type="password",
            key="reg_pass"
        )

        if st.button(
            "Create Account"
        ):

            if sign_up_user(
                new_u,
                new_p
            ):

                st.success(
                    "Account created!"
                )

            else:

                st.error(
                    "Username already exists"
                )


# MAIN APP
if st.session_state["logged_in"]:

    col_title, col_user, col_logout = st.columns(
        [4, 1.5, 1]
    )

    with col_title:

        st.title(
            "📂 Job Tracker"
        )

    with col_user:

        st.markdown(
            "<div style='margin-top:25px'></div>",
            unsafe_allow_html=True
        )

        st.write(
            f"👤 **{st.session_state['username']}**"
        )

    with col_logout:

        st.markdown(
            "<div style='margin-top:18px'></div>",
            unsafe_allow_html=True
        )

        if st.button(
            "Sign Out",
            type="secondary",
            width="stretch"
        ):

            st.session_state.clear()
            st.rerun()

    # ADD JOB
    with st.expander(
        "➕ Add New Application",
        expanded=False
    ):

        c1, c2 = st.columns(2)

        with c1:

            comp = st.text_input(
                "Company Name"
            )

        with c2:

            pos = st.text_input(
                "Position Title"
            )

        row1, row2 = st.columns(
            [3, 1]
        )

        with row1:

            url_in = st.text_input(
                "Job Posting URL"
            )

        with row2:

            st.markdown(
                "<div style='margin-top:28px'></div>",
                unsafe_allow_html=True
            )

            if st.button(
                "✨ Auto-Fill"
            ):

                if url_in:

                    with st.spinner(
                        "Scraping..."
                    ):

                        raw = scrape_job_link(
                            url_in
                        )

                        st.session_state[
                            "formatted_desc"
                        ] = clean_description_with_ai(
                            raw
                        )

                else:

                    st.warning(
                        "Enter URL first"
                    )

        final_desc = st.text_area(
            "Job Description",
            value=st.session_state[
                "formatted_desc"
            ],
            height=200
        )

        st.subheader(
            "🎯 AI Match & Timeline"
        )

        col_file, col_date = st.columns(
            2
        )

        with col_file:

            up_file = st.file_uploader(
                "Upload Resume",
                type=[
                    "pdf",
                    "docx"
                ]
            )

        with col_date:

            applied_date = st.date_input(
                "Date Applied",
                value=pd.Timestamp.today()
            )

        # SCAN
        if st.button(
            "🔍 Scan Resume"
        ):

            if final_desc and up_file:

                with st.spinner(
                    "Analyzing Resume..."
                ):

                    try:

                        resume_txt = (
                            extract_text_from_upload(
                                up_file
                            )
                        )

                        st.session_state[
                            "match_data"
                        ] = (
                            get_ai_match_feedback(
                                final_desc,
                                resume_txt
                            )
                        )

                    except Exception as e:

                        st.session_state[
                            "match_data"
                        ] = {

                            "score":
                            "Error",

                            "feedback":
                            [
                                str(e)
                            ]
                        }

            else:

                st.warning(
                    "Upload resume and job description first"
                )

        # RESULTS
        if st.session_state[
            "match_data"
        ]:

            m = st.session_state[
                "match_data"
            ]

            st.success(
                f"🎯 Match Score: {m.get('score','N/A')}"
            )

            st.subheader(
                "AI Feedback"
            )

            for item in m.get(
                "feedback",
                []
            ):

                if item.strip():

                    st.write(
                        item
                    )

        # SAVE
        if st.button(
            "💾 Save Application"
        ):

            if comp and pos:

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

                    resume_url = (
                        upload_resume(
                            up_file,
                            st.session_state[
                                "username"
                            ]
                        )
                    )

                success = save_job(
                    comp,
                    pos,
                    final_desc,
                    url_in,
                    resume_url,
                    score,
                    applied_date=applied_date
                )

                if success:

                    st.success(
                        "Application saved!"
                    )

                    st.session_state[
                        "formatted_desc"
                    ] = ""

                    st.session_state[
                        "match_data"
                    ] = None

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
            df["created_at"]
        )

        df[
            "created_at"
        ] = (
            df[
                "created_at"
            ]
            .dt.tz_convert(None)
            .dt.strftime(
                "%m/%d/%Y"
            )
        )

        status_options = [
            "Active",
            "Applied",
            "Interview Scheduled",
            "Interviewed",
            "Moving On"
        ]

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
                    "Status",
                    options=status_options
                ),

                "pdf_url":
                st.column_config.LinkColumn(
                    "Job Snapshot",
                    display_text="View"
                ),

                "resume_link":
                st.column_config.LinkColumn(
                    "My Resume",
                    display_text="Download"
                ),

                "job_url":
                st.column_config.LinkColumn(
                    "Original Posting",
                    display_text="Open Link"
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
                    df.iloc[row]["id"]
                )

            st.rerun()

        # EDIT
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
                    df.iloc[row]["id"],
                    changes
                )

            st.rerun()

    else:

        st.write(
            "No applications yet."
        )
