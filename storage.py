import streamlit as st
from supabase import create_client, Client
import os

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Check Streamlit Secrets.")
    st.stop()

# ... (keep sign_up_user, login_user, and upload_resume as they are)

def save_job(company, position, description, job_url, resume_url, match_score):
    pdf_url = None
    
    if job_url and job_url.startswith("http"):
        # Clean filename for local storage
        safe_name = f"{company}_{position}".replace(" ", "_").replace("/", "-")
        snap_name = f"{safe_name}.pdf"
        
        from utils import generate_pdf_snapshot
        if generate_pdf_snapshot(job_url, snap_name):
            try:
                with open(snap_name, "rb") as f:
                    supabase.storage.from_("job_previews").upload(
                        path=snap_name, 
                        file=f, 
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )
                pdf_url = supabase.storage.from_("job_previews").get_public_url(snap_name)
                if os.path.exists(snap_name):
                    os.remove(snap_name)
            except Exception as e:
                st.warning(f"Snapshot upload failed: {e}")

    data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
        "pdf_url": pdf_url,
        "match_score": match_score,
        "status": "Active" 
    }
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def load_jobs():
    try:
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except: return []
