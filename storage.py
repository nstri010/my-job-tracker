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
    fake_email = f"{username}@app.com"
    try:
        response = supabase.auth.sign_up({
            "email": fake_email,
            "password": password,
            "options": {"data": {"display_name": username}}
        })
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Error: {e}")
        return False

def login_user(username, password):
    fake_email = f"{username}@app.com"
    try:
        response = supabase.auth.sign_in_with_password({
            "email": fake_email, 
            "password": password
        })
        return response.user is not None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return False

# --- DATABASE FUNCTIONS (Now with Status) ---
def save_job(company, position, description, status):
    """Saves the job with the specific status selected by the user"""
    data = {
        "company": company,
        "position": position,
        "description": description,
        "status": status  # Now dynamic!
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

def update_job_status(job_id, new_status):
    try:
        supabase.table("jobs").update({"status": new_status}).eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
        return False
