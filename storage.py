import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Please check your Streamlit Cloud Settings.")
    st.stop()

# --- AUTHENTICATION FUNCTIONS ---
def sign_up_user(username, password):
    email_format = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_up({"email": email_format, "password": password})
        return response.user is not None
    except Exception:
        # Removed the st.error here so it doesn't double up
        return False

def login_user(username, password):
    email_format = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_in_with_password({"email": email_format, "password": password})
        return response.user is not None
    except Exception:
        # Removed the st.error here so it doesn't double up
        return False

# --- DATABASE FUNCTIONS ---
def save_job(company, position, description):
    data = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active" 
    }
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Save Error: {e}")
        return False

def load_jobs():
    try:
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

def delete_job(job_id):
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete Error: {e}")
        return False
