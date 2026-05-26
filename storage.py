import streamlit as st
from supabase import create_client, Client
import os
import time

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Secrets Error.")
    st.stop()

def sign_up_user(username, password, email):
    try:
        # Step 1: create auth user
        res = supabase.auth.sign_up({"email": email, "password": password})
        if not res.user:
            return False, "Signup failed — please try again"
    except Exception as e:
        return False, f"Auth error: {str(e)}"

    try:
        # Step 2: store username→email in profiles
        supabase.table("profiles").insert({"username": username, "email": email}).execute()
    except Exception as e:
        return False, f"Profile error: {str(e)}"

    return True, None

def login_user(username, password):
    try:
        # Look up real email from profiles table
        res = supabase.table("profiles").select("email").eq("username", username).execute()
        if not res.data:
            return False
        email = res.data[0]["email"]
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user is not None
    except: return False

def send_password_reset(username):
    try:
        res = supabase.table("profiles").select("email").eq("username", username).execute()
        if not res.data:
            return False
        email = res.data[0]["email"]
        supabase.auth.reset_password_email(email)
        return True
    except: return False

def upload_resume(file_obj, username):
    try:
        file_path = f"{username}/{file_obj.name}"
        supabase.storage.from_("resumes").upload(path=file_path, file=file_obj.getvalue(), file_options={"upsert": "true"})
        return supabase.storage.from_("resumes").get_public_url(file_path)
    except: return None

def save_job(company, position, description, job_url, resume_url, match_score, applied_date=None):
    pdf_url = None
    if job_url:
        from utils import generate_pdf_snapshot
        snap_name = f"JOB_{company}_{int(time.time())}.pdf".replace(" ", "_")
        try:
            if generate_pdf_snapshot(job_url, snap_name):
                with open(snap_name, "rb") as f:
                    supabase.storage.from_("job_previews").upload(
                        path=snap_name,
                        file=f,
                        file_options={"content-type": "application/pdf"}
                    )
                pdf_url = supabase.storage.from_("job_previews").get_public_url(snap_name)
                os.remove(snap_name)
        except Exception as e:
            import streamlit as st
            st.warning(f"⚠️ Snapshot failed: {e}")

    data = {
        "company": company, "position": position, "description": description,
        "job_url": job_url, "resume_link": resume_url, "pdf_url": pdf_url,
        "match_score": str(match_score), "status": "Active"
    }

    if applied_date:
        data["created_at"] = applied_date.isoformat()

    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Save failed: {e}")
        return False

def load_jobs():
    try:
        res = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def update_job_full(job_id, changes):
    try:
        supabase.table("jobs").update(changes).eq("id", job_id).execute()
        return True
    except: return False

def delete_job(job_id):
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except: return False

def send_password_reset(username):
    email = f"{username}@tracker.com"
    try:
        supabase.auth.reset_password_email(email)
        return True
    except: return False
