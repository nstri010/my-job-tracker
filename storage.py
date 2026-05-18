import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
# Streamlit will look for these in your .streamlit/secrets.toml file or app settings
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Setup Error: Missing Supabase Secrets. Please check your config.")

# --- USER SIGN UP ---
def sign_up_user(email, password):
    """Registers a user. Email confirmation must be OFF in Supabase for this to work instantly."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        # If Confirm Email is OFF, this returns a session immediately
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Failed: {e}")
        return False

# --- JOB TRACKER FUNCTIONS ---
def save_job(company, position, description):
    """Inserts a new job record into the 'jobs' table"""
    data = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    try:
        # Note: You must create a table named 'jobs' in your Supabase Table Editor first
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def load_jobs():
    """Fetches all jobs from the 'jobs' table"""
    try:
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

def update_job_status(job_id, new_status):
    """Updates the status of a specific job"""
    try:
        supabase.table("jobs").update({"status": new_status}).eq("id", job_id).execute()
        return True
    except:
        return False
