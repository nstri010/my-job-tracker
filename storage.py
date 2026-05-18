import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
# This pulls the keys you saved in the Streamlit "Secrets" vault
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Please check your Streamlit Cloud Settings.")
    st.stop()

# --- AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    """
    Matches the 3 arguments from your app.py line 96.
    Stores the username in the user's metadata.
    """
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": username
                }
            }
        })
        # If 'Confirm Email' is OFF in Supabase, this returns a user object immediately
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Error: {e}")
        return False

def login_user(email, password):
    """Logs the user in using Supabase Auth"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user is not None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return False

# --- JOB TRACKER DATABASE FUNCTIONS ---

def save_job(company, position, description):
    """Inserts a new job record into the 'jobs' table"""
    data = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    try:
        # Note: Ensure you created a table named 'jobs' in the Supabase Table Editor
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Save Error: {e}")
        return False

def load_jobs():
    """Fetches all jobs from the 'jobs' table"""
    try:
        # We order by created_at so the newest applications appear at the top
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        # Return empty list if there's an error or no jobs yet
        return []

def update_job_status(job_id, new_status):
    """Updates the status of a specific job (e.g., Active -> Interviewing)"""
    try:
        supabase.table("jobs").update({"status": new_status}).eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Update Error: {e}")
        return False

def delete_job(job_id):
    """Removes a job record from the database"""
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete Error: {e}")
        return False
