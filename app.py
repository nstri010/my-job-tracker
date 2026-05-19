import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
from utils import scrape_job_link, clean_description_with_ai, get_ai_match_feedback, extract_text_from_upload

st.set_page_config(page_title="Job Tracker", layout="wide")

# Session State Initialization
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'formatted_desc' not in st.session_state: st.session_state['formatted_desc'] = ""
if 'match_data' not in st.session_state: st.session_state['match_data'] = None

# --- [Login Logic remains here] ---

if st.session_state['logged_in']:
    st.title("📂 Job Tracker")
    st.caption("⚠️ This website uses AI results. Always make sure to verify information for accuracy.")
    
    with st.expander("➕ Add New Application", expanded=True):
        # First Row: Basic Info
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            comp = st.text_input("Company Name", placeholder="e.g. Google")
        with row1_col2:
            pos = st.text_input("Position Title", placeholder="e.g. Data Analyst")

        # Second Row: URL and Auto-Fill (Placed right under the first row)
        row2_col1, row2_col2 = st.columns([3, 1])
        with row2_col1:
            url_in = st.text_input("Job Posting URL", placeholder="Paste link here...")
        with row2_col2:
            # Added a little vertical padding with markdown to align button better
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("✨ Auto-Fill Job Description"):
                if url_in:
                    with st.spinner("Generating full listing..."):
                        raw = scrape_job_link(url_in)
                        st.session_state['formatted_desc'] = clean_description_with_ai(raw)
                else:
                    st.warning("Please enter a URL first.")

        # Display the formatted description
        final_desc = st.text_area("Job Description (click to edit text)", value=st.session_state['formatted_desc'], height=300)

        st.divider()

        # STEP 2: RESUME SCAN
        st.subheader("🎯 AI Resume Match Scan")
        up_file = st.file_uploader("Upload Resume for Feedback", type=['pdf', 'docx'])
        
        if st.button("🔍 Scan for Match & Feedback"):
            if final_desc and up_file:
                with st.spinner("Analyzing match..."):
                    resume_txt = extract_text_from_upload(up_file)
                    st.session_state['match_data'] = get_ai_match_feedback(final_desc, resume_txt)
            else:
                st.warning("Ensure description is filled and resume is uploaded.")

        # Show Analysis results
        if st.session_state['match_data']:
            m = st.session_state['match_data']
            st.info(f"**AI Match Score:** {m['score']}")
            for f in m['feedback']:
                st.write(f"✅ {f}")

        if st.button("💾 Save Application"):
            score_to_save = st.session_state['match_data']['score'] if st.session_state['match_data'] else "N/A"
            res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
            if save_job(comp, pos, final_desc, url_in, res_url, score_to_save):
                st.session_state['formatted_desc'] = ""
                st.session_state['match_data'] = None
                st.success("Saved!")
                st.rerun()

    # --- [Dashboard/Load Jobs section follows] ---
