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

# SESSION
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

            # COMPANY
            with c1:

                st.write(
                    row.get(
                        "company",
                        ""
                    )
                )

            # POSITION
            with c2:

                st.write(
                    row.get(
                        "position",
                        ""
                    )
                )

            # MATCH
            with c3:

                st.write(
                    row.get(
                        "score",
                        "N/A"
                    )
                )

            # STATUS
            with c4:

                st.markdown(
                    "<div style='margin-top:10px'></div>",
                    unsafe_allow_html=True
                )

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

            # RESUME
            with c5:

                st.markdown(
                    "<div style='margin-top:10px'></div>",
                    unsafe_allow_html=True
                )

                resume = row.get(
                    "resume_link"
                )

                if resume:

                    st.link_button(

                        "📄",

                        resume,

                        width="stretch"

                    )

            # DELETE
            with c6:

                st.markdown(
                    "<div style='margin-top:10px'></div>",
                    unsafe_allow_html=True
                )

                if st.button(

                    "🗑️",

                    key=
                    f"delete_{row['id']}",

                    width="stretch"

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
