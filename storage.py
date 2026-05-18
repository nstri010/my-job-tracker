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

# --- THE FIXED SIGN UP FUNCTION ---
def sign_up_user(username, password, email):
    """
    Expects 3 arguments to match your app.py line 96.
    We store the 'username' as user_metadata in Supabase.
    """
    try:
        # Supabase uses Email/Password for login, but we can save the 
        # username inside 'options' so it isn't lost!
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": username
                }
            }
        })
        return response.user is not None
    except Exception as e:
        st.error(f"Sign Up Error: {e}")
        return False

# --- KEEP YOUR OTHER FUNCTIONS BELOW (save_job, load_jobs, etc.) ---
