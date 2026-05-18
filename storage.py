import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
# Ensure this is your actual Master Key string
MASTER_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

# Target our brand new custom class
MEMBER_URL = "https://parseapi.back4app.com/classes/Member"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

def sign_up_user(username, password, email):
    """Saves user data to the custom Member class"""
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        response = requests.post(MEMBER_URL, json=payload, headers=HEADERS)
        
        if response.status_code == 201:
            return True
        else:
            # This will show us the REAL error if one exists
            error_msg = response.json().get('error', 'Unknown Error')
            st.error(f"Database Error: {error_msg}")
            return False
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
