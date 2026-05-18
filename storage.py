import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
# ENSURE THIS IS THE MASTER KEY (The longest one in your settings)
MASTER_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

# Using the generic users endpoint
USER_URL = "https://parseapi.back4app.com/users"

# We are strictly using the Master Key header here
HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

# --- JOB DATABASE FUNCTIONS ---
# (Keeping these the same so your tracker doesn't break)
BASE_URL = "https://parseapi.back4app.com/classes/Job"

def save_job(company, position, description):
    payload = {"company": company, "position": position, "description": description, "status": "Active"}
    return requests.post(BASE_URL, json=payload, headers=HEADERS).status_code == 201

def load_jobs():
    response = requests.get(f"{BASE_URL}?order=-createdAt", headers=HEADERS)
    return response.json().get("results", []) if response.status_code == 200 else []

def update_job_status(object_id, new_status):
    url = f"{BASE_URL}/{object_id}"
    return requests.put(url, json={"status": new_status}, headers=HEADERS).status_code == 200

def delete_job(object_id):
    return requests.delete(f"{BASE_URL}/{object_id}", headers=HEADERS).status_code == 200

# --- THE NEW USER SIGN UP FUNCTION ---

def sign_up_user(username, password, email):
    """Attempting a direct POST to the users table"""
    data = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        # We are forcing the request to ignore cached sessions
        response = requests.post(USER_URL, json=data, headers=HEADERS)
        
        if response.status_code == 201:
            return True
        else:
            # This will show the RAW error from the server so we can see the 'Real' problem
            raw_error = response.json()
            st.error(f"Server Error {response.status_code}: {raw_error}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
