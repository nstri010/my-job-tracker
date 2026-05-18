import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
# Using the keys you provided!
SUPABASE_URL = "https://degewjwksbqrysyicotl.supabase.co"
SUPABASE_KEY = "sb_publishable_nYbCYmqThqWt6tMMJwVcTg_877OxIko"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- USER SIGN UP ---
def sign_up_user(email, password):
    """Creates a user in Supabase Auth"""
    try:
        # Supabase Auth handles the security and unauthorized blocks for you
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        return True
    except Exception as e:
        # This will show you exactly what's wrong if it fails
        st.error(f"Backend Error: {e}")
        return False

# --- JOB DATABASE FUNCTIONS ---
def save_job(company, position, description):
    """Inserts a job into the 'jobs' table"""
    data = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    try:
        # Ensure you created a table named 'jobs' in your Supabase dashboard first
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
