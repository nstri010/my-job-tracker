from supabase import create_client
import streamlit as st

# Supabase setup
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# SIGN UP USER
# -----------------------------
def sign_up_user(username, password):

    existing_user = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if existing_user.data:
        return False

    supabase.table("users").insert({
        "username": username,
        "password": password
    }).execute()

    return True


# -----------------------------
# LOGIN USER
# -----------------------------
def login_user(username, password):

    response = (
        supabase.table("users")
        .select("*")
        .eq("username", username)
        .eq("password", password)
        .execute()
    )

    return len(response.data) > 0
