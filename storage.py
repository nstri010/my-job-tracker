import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
try:
    # These must match exactly what you typed in the Streamlit Secrets box
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Please check your Streamlit Cloud Settings.")
    st.stop()

# --- AUTH FUNCTIONS ---
def sign_up_user(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Error: {e}")
        return False

# --- JOB DATABASE FUNCTIONS ---
def save_job(company, position, description):
    data = {"company": company, "position": position, "description": description, "status": "Active"}
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def load_jobs():
    try:
        # Note: 'jobs' table must be created in your Supabase dashboard
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

def update_job_status(job_id, new_status):
    try:
        supabase.table("jobs").update({"status": new_status}).eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
        return False

def delete_job(job_id):
    """This was the missing piece causing your error!"""
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete Error: {e}")
        return False
