import streamlit as st
import os
import datetime
from storage import load_jobs, save_job, build_job_record, update_job_status, update_job_details, RESUME_FOLDER
from utils import scrape_job_link, generate_pdf_snapshot

st.set_page_config(page_title="Job Tracker", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .stApp { background: #0b0f19; color: white; }
    .job-header { background: #1a1f2b; padding: 12px 18px; border-radius: 8px 8px 0 0; border-left: 5px solid #ff4b4b; border-bottom: 1px solid #2e3440; display: flex; justify-content: space-between; align-items: center; }
    .button-tray { background: #161b22; padding: 10px; border-radius: 0 0 8px 8px; border: 1px solid #2e3440; border-top: none; margin-bottom: 20px; }
    .stButton > button { border: 1px solid #3d4452 !important; background-color: #1a1f2b !important; color: #e5e7eb !important; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 Job Application Tracker")

# --- ADD NEW JOB SECTION ---
with st.expander("➕ Add New Application"):
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("Company Name")
    with c2:
        position = st.text_input("Position")
    job_link = st.text_input("Job Listing URL")

    if st.button("🔍 Auto-Fill Description"):
        if job_link:
            st.session_state['fetched_text'] = scrape_job_link(job_link)
        else:
            st.warning("Please paste a link first.")

    description = st.text_area("Job Description", value=st.session_state.get('fetched_text', ""), height=150)
    applied_on = st.date_input("Date Applied", datetime.date.today())
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

    if st.button("💾 Save to Tracker"):
        if company and position:
            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            res_name, snap_name = None, None
            if uploaded_file:
                ext = os.path.splitext(uploaded_file.name)[1]
                res_name = f"RESUME_{company}_{ts}{ext}".replace(" ", "_")
                with open(os.path.join(RESUME_FOLDER, res_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
            if job_link:
                snap_name = f"LISTING_{company}_{ts}.pdf".replace(" ", "_")
                generate_pdf_snapshot(job_link, snap_name)

            if save_job(build_job_record(company, position, description, applied_on, res_name, snap_name)):
                st.success("Saved!");
                st.rerun()
            else:
                st.error("Job already exists!")

# --- DISPLAY SECTION ---
st.header("📋 Your Applications")
all_jobs = load_jobs()
active_jobs = [j for j in all_jobs if j.get('status') != "Hidden"]

for job in reversed(active_jobs):
    job_date = job.get('date_applied', job.get('date', 'N/A'))
    st.markdown(
        f'<div class="job-header"><div><b>{job["company"]}</b> | {job["position"]}</div><div style="color: gray;">📅 {job_date}</div></div>',
        unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="button-tray">', unsafe_allow_html=True)

        # We use 4 columns: Description/Edit, Listing, Resume, Archive
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

        with c1:
            # FIXED: Moved Edit into the expander so it closes on st.rerun()
            with st.expander("📝 View / Edit Details"):
                st.write("**Current Description:**")
                st.write(job['description'])
                st.divider()
                st.subheader("✏️ Quick Edit")
                n_c = st.text_input("Company", value=job['company'], key=f"ec_{job['id']}")
                n_p = st.text_input("Position", value=job['position'], key=f"ep_{job['id']}")
                n_d = st.text_area("Description", value=job['description'], key=f"ed_{job['id']}", height=200)

                if st.button("💾 Save Changes", key=f"up_{job['id']}"):
                    update_job_details(job['id'], n_c, n_p, n_d)
                    st.toast(f"Updated {n_c}")
                    st.rerun()  # This forces the page to reload and the expander to close

        with c2:
            if job.get('snapshot_filename') and os.path.exists(os.path.join(RESUME_FOLDER, job['snapshot_filename'])):
                with open(os.path.join(RESUME_FOLDER, job['snapshot_filename']), "rb") as f:
                    st.download_button("📄 Job PDF", f, file_name=job['snapshot_filename'], key=f"s_{job['id']}")
            else:
                st.button("🚫 No Listing", disabled=True, key=f"s_{job['id']}")

        with c3:
            if job.get('resume_filename') and os.path.exists(os.path.join(RESUME_FOLDER, job['resume_filename'])):
                with open(os.path.join(RESUME_FOLDER, job['resume_filename']), "rb") as f:
                    st.download_button("📥 Resume", f, file_name=job['resume_filename'], key=f"r_{job['id']}")
            else:
                st.button("🚫 No Resume", disabled=True, key=f"r_{job['id']}")

        with c4:
            if st.button("🗑️ Archive", key=f"h_{job['id']}"):
                update_job_status(job['id'], "Hidden")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)