# --- Inside the Dashboard portion of app.py ---

with st.expander("➕ Add New Application", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        comp = st.text_input("Company Name", placeholder="e.g. Google")
        pos = st.text_input("Position Title", placeholder="e.g. Data Analyst")
    with col2:
        url_input = st.text_input("Job Posting URL", placeholder="e.g. https://linkedin.com...")

    uploaded_resume = st.file_uploader("Upload Resume for AI Match", type=["pdf", "docx"])
    
    if st.button("✨ AI Auto-fill & Score"):
        if url_input:
            with st.spinner("AI is analyzing the role and your resume..."):
                raw_text = scrape_job_link(url_input)
                resume_text = ""
                if uploaded_resume:
                    resume_text = extract_text_from_upload(uploaded_resume)
                
                # Call AI
                ai_result = analyze_job_with_ai(raw_text, resume_text)
                # Store in session state to display in the text area
                st.session_state['ai_analysis'] = ai_result 
        else:
            st.warning("Please paste a link first.")

    # UI for showing results
    ai_data = st.session_state.get('ai_analysis', "")
    desc = st.text_area("Formatted Job Description", value=ai_data, height=300)
    
    if st.button("Save Application"):
        # Logic to extract score and text from ai_data would go here
        res_url = upload_resume(uploaded_resume, st.session_state['username']) if uploaded_resume else None
        save_job(comp, pos, desc, url_input, res_url)
        st.rerun()
