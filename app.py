import streamlit as st
from storage import load_jobs, save_job, delete_job, sign_up_user, login_user, upload_resume
from utils import scrape_job_link, analyze_job_with_ai, extract_text_from_upload

st.set_page_config(page_title="Job Tracker", layout="wide")

# Initialize Session States
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = ""
if 'ai_desc' not in st.session_state: st.session_state['ai_desc'] = ""
if 'ai_score' not in st.session_state: st.session_state['ai_score'] = "N/A"

st.markdown("""
    <style>
    .stApp { background-color: #0f1117; font-family: 'Inter', sans-serif; }
    .job-card { background: #1a1f2e; padding: 20px; border-radius: 10px; border-left: 4px solid #7d2ae8; margin-bottom: 15px; }
    .score-badge { background: #7d2ae8; color: white; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if not st.session_state['logged_in']:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.title("Welcome")
        t1, t2 = st.tabs(["Login", "Sign Up"])
        with t1:
            u = st.text_input("Username", placeholder="Username")
            p = st.text_input("Password", type="password", placeholder="Password")
            if st.button("Log In"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.rerun()
        with t2:
            nu = st.text_input("New Username", placeholder="New Username")
            np = st.text_input("New Password", type="password", placeholder="New Password")
            if st.button("Register"):
                if sign_up_user(nu, np): st.success("Created!")

else:
    st.title("📂 Job Tracker")
    
    with st.expander("➕ Add New Application", expanded=True):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company", placeholder="e.g. Google")
        pos = c1.text_input("Position", placeholder="e.g. Software Engineer")
        url_in = c2.text_input("Job URL", placeholder="e.g. https://linkedin.com/...")
        
        up_file = st.file_uploader("Upload Resume (PDF/DOCX) for AI Match", type=['pdf', 'docx'])
        
        if st.button("✨ AI Auto-Fill & Match Score"):
            if url_in:
                with st.spinner("AI is cleaning text and matching resume..."):
                    raw = scrape_job_link(url_in)
                    resume_txt = extract_text_from_upload(up_file) if up_file else None
                    result = analyze_job_with_ai(raw, resume_txt)
                    st.session_state['ai_desc'] = result['formatted_desc']
                    st.session_state['ai_score'] = result['match_score']
            else: st.error("Add a URL first!")

        final_desc = st.text_area("Job Description", value=st.session_state['ai_desc'], height=250)
        st.write(f"**AI Match Score:** {st.session_state['ai_score']}")

        if st.button("Save to Tracker"):
            res_url = upload_resume(up_file, st.session_state['username']) if up_file else None
            if save_job(comp, pos, final_desc, url_in, res_url, st.session_state['ai_score']):
                st.session_state['ai_desc'] = ""
                st.success("Saved!")
                st.rerun()

    st.divider()
    jobs = load_jobs()
    
    if not jobs:
        st.info("No applications yet. Your first one will appear here.")
    else:
        for j in jobs:
            st.markdown(f"""
                <div class="job-card">
                    <span class="score-badge">Match: {j.get('match_score', 'N/A')}</span>
                    <h4 style="margin:5px 0; color: white;">{j['position']}</h4>
                    <p style="color:#7d2ae8; margin:0; font-weight: bold;">{j['company']}</p>
                    <p style="color:#94a3b8; font-size: 0.85rem; margin-top: 10px;">{j['description'][:200]}...</p>
                </div>
            """, unsafe_allow_html=True)
            
            bc1, bc2, bc3 = st.columns([1, 1, 4])
            if j.get('job_url'): bc1.link_button("View Job", j['job_url'])
            if j.get('resume_link'): bc2.link_button("View Resume", j['resume_link'])
            if bc3.button("Delete", key=f"del_{j['id']}"):
                delete_job(j['id'])
                st.rerun()
