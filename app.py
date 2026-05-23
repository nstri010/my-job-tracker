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

        new_u = st.text_input(
            "Create Username"
        )

        new_p = st.text_input(
            "Create Password",
            type="password"
        )

        if st.button(
            "Create Account"
        ):

            if sign_up_user(
                new_u,
                new_p
            ):

                st.success(
                    "Account created"
                )

            else:

                st.error(
                    "Username exists"
                )


# MAIN APP

if st.session_state[
    "logged_in"
]:

    t1, t2 = st.columns(
        [5, 1]
    )

    with t1:
        st.title(
            "📂 Job Tracker"
        )

    with t2:

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
                    "Fetching description..."
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
            value=st.session_state[
                "formatted_desc"
            ],
            height=220
        )

        col1, col2 = st.columns(
            2
        )

        with col1:

            up_file = st.file_uploader(
                "Upload Resume",
                type=[
                    "pdf",
                    "docx",
                    "txt"
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

                with st.spinner(
                    "Analyzing match..."
                ):

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

            match = st.session_state[
                "match_data"
            ]

            st.success(
                f"🎯 Resume Match: {match.get('score','N/A')}"
            )

            for item in match.get(
                "feedback",
                []
            ):

                st.write(
                    item
                )

        # SAVE BUTTON
        if st.button(
            "💾 Save Application"
        ):

            resume_url = None

            if up_file:

                resume_url = upload_resume(
                    up_file,
                    st.session_state[
                        "username"
                    ]
                )

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

            success = save_job(
                company=comp,
                position=pos,
                description=final_desc,
                job_url=url_in,
                resume_url=resume_url,
                match_score=score,
                applied_date=applied_date
            )

            if success:

                st.success(
                    "Application saved"
                )

                st.rerun()

            else:

                st.error(
                    "Save failed"
                )

    st.divider()

    st.header(
        "📋 My Applied Jobs"
    )

    jobs_list = load_jobs()

    status_options = [
        "📝 Applied",
        "📨 Contacted",
        "📅 Interview",
        "✅ Offer",
        "❌ Rejected"
    ]

    if jobs_list:

        df = pd.DataFrame(
            jobs_list
        )

        ratios = [
            2,
            2,
            0.8,
            1.5,
            0.5,
            0.5,
            0.5
        ]

        headers = [
            "Company",
            "Position",
            "Match",
            "Status",
            "Resume",
            "Snapshot",
            "Delete"
        ]

        cols = st.columns(
            ratios
        )

        for c, h in zip(
            cols,
            headers
        ):

            c.markdown(
                f"**{h}**"
            )

        st.divider()

        for idx, row in df.iterrows():

            c1, c2, c3, c4, c5, c6, c7 = st.columns(
                ratios,
                vertical_alignment="center"
            )

            c1.write(
                row.get(
                    "company",
                    ""
                )
            )

            c2.write(
                row.get(
                    "position",
                    ""
                )
            )

            c3.write(
                row.get(
                    "match_score",
                    "N/A"
                )
            )

            curr = row.get(
                "status",
                "📝 Applied"
            )

            with c4:

                new_stat = st.selectbox(
                    "Status",
                    status_options,
                    index=(
                        status_options.index(curr)
                        if curr in status_options
                        else 0
                    ),
                    key=f"s_{row['id']}",
                    label_visibility="collapsed"
                )

                if new_stat != curr:

                    update_job_full(
                        row["id"],
                        {
                            "status": new_stat
                        }
                    )

                    st.rerun()

            # RESUME BUTTON

            resume_link = row.get("resume_link")

            with c5:
                if resume_link:
                    st.link_button("📄", resume_link)
                else:
                    st.button(
                        "📄",
                        key=f"r_{row['id']}",
                        disabled=True
                    )

            # SNAPSHOT BUTTON

            pdf_url = row.get("pdf_url")

            with c6:
                if pdf_url:
                    st.link_button("📸", pdf_url)
                else:
                    st.button(
                        "📸",
                        key=f"p_{row['id']}",
                        disabled=True
                    )

            # DELETE

            if c7.button(
                "❌",
                key=f"d_{row['id']}"
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
