import streamlit as st
from supabase import create_client, Client
import os
import time

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Check Streamlit Secrets.")
    st.stop()

def sign_up_user(username, password):
    email = f"{username}@tracker.com"
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        return True
    except: return False

def login_user(username, password):
    email = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user is not None
    except: return False

def upload_resume(file_obj, username):
    try:
        file_path = f"{username}/{file_obj.name}"
        supabase.storage.from_("resumes").upload(path=file_path, file=file_obj.getvalue(), file_options={"upsert": "true"})
        return supabase.storage.from_("resumes").get_public_url(file_path)
    except: return None

def save_job(company, position, description, job_url, resume_url, match_score):
    pdf_url = None
    
    # Trigger the browser snapshot if a URL is provided
    if job_url:
        ts = int(time.time())
        snap_name = f"LISTING_{company}_{ts}.pdf".replace(" ", "_")
        
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
                os.remove(snap_name) # Clean up local file after upload
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

def delete_job(job_id):
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except: return False
