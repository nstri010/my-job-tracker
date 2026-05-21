# STEP 4: VIEW & EDIT SAVED JOBS
    st.divider()
    st.header("📋 My Applied Jobs")

    jobs_list = load_jobs()

    if jobs_list:
        df = pd.DataFrame(jobs_list)
        
        # Time Formatting
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['created_at'] = df['created_at'].dt.tz_convert(None).dt.strftime('%m/%d/%Y, %I:%M %p')

        # We add a visual arrow (⌄) to the status options so it looks like a menu
        status_options = [
            "Active ⌄", 
            "Applied ⌄", 
            "Interview Scheduled ⌄", 
            "Interviewed ⌄", 
            "Moving On ⌄"
        ]

        # Use SelectboxColumn to turn the cell into a dropdown
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "created_at": st.column_config.TextColumn("Created At", disabled=True),
                "company": st.column_config.TextColumn("Company", disabled=True),
                "position": st.column_config.TextColumn("Position", disabled=True),
                "status": st.column_config.SelectboxColumn(
                    "Status", 
                    help="Click to open the menu",
                    width="medium",
                    options=status_options, 
                    required=True
                ),
                "match_score": st.column_config.TextColumn("Score", disabled=True),
                "pdf_url": st.column_config.LinkColumn("Job PDF"),
                "resume_link": st.column_config.LinkColumn("My Resume"),
                "job_url": st.column_config.LinkColumn("Original Link"),
                "id": None, "description": None
            },
            hide_index=True,
            key="jobs_editor"
        )

        # Update Logic
        if st.session_state.get("jobs_editor") and st.session_state["jobs_editor"]["edited_rows"]:
            updates = st.session_state["jobs_editor"]["edited_rows"]
            for index, changes in updates.items():
                if "status" in changes:
                    job_id = df.iloc[index]["id"]
                    new_status = changes["status"]
                    if update_job_status(job_id, new_status):
                        st.toast(f"Status updated to {new_status}!", icon="✅")
    else:
        st.write("No applications yet.")
