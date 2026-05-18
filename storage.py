import streamlit as st
from supabase import create_client, Client

# --- CONNECT TO SUPABASE ---
# Use the URL from your screenshot!
SUPABASE_URL = "https://degewjwksbqrysyicotl.supabase.co"
# Use the 'anon' key starting with 'sb_publishable'
SUPABASE_KEY = st.secrets["SUPABASE_KEY"] 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def sign_up_user(email, password):
    """Creates a user record in Supabase Auth"""
    try:
        # This will now work instantly since we turned off 'Confirm Email'
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Error: {e}")
        return False

def save_job(company, position, description):
    """Saves a job to your 'jobs' table"""
    try:
        data = {"company": company, "position": position, "description": description}
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False
