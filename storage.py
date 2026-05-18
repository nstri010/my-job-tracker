import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Check Streamlit Secrets.")
    st.stop()

# --- AUTHENTICATION ---
def sign_up_user(username, password):
    email = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response.user is not None
    except: 
        return False

def login_user(username, password):
    email = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user is not None
    except: 
        return False

# --- FILE UPLOAD TO STORAGE ---
def upload_resume(file_obj, username):
    """Uploads file to Supabase Storage and returns the public URL."""
    try:
        # Create a unique path: username/filename
        file_path = f"{username}/{file_obj.name}"
        
        # Upload file to the 'resumes' bucket
        # Note: Ensure you created a bucket named 'resumes' in Supabase
        supabase.storage.from_("resumes").upload(
            path=file_path, 
            file=file_obj.getvalue(), 
            file_options={"upsert": "true"}
        )
        
        # Get the public URL to save in the database
        res = supabase.storage.from_("resumes").get_public_url(file_path)
        return res
    except Exception as e:
        st.error(f"Upload Error: {e}")
        return None

# --- DATABASE FUNCTIONS ---
def save_job(company, position, description, job_url, resume_url):
    data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
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
    except: 
        return []

def delete_job(job_id):
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except: 
        return False
