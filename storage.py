import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
# This is your Master Key (MC7MU...)
MASTER_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

# We use a custom 'Member' class to avoid the 401 Unauthorized plan lock
MEMBER_URL = "https://parseapi.back4app.com/classes/Member"
JOB_URL = "https://parseapi.back4app.com/classes/Job"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

# --- JOB DATABASE FUNCTIONS ---

def save_job(company, position, description):
    payload = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    response = requests.post(JOB_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    response = requests.get(f"{JOB_URL}?order=-createdAt", headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def delete_job(object_id):
    url = f"{JOB_URL}/{object_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

def update_job_status(object_id, new_status):
    url = f"{JOB_URL}/{object_id}"
    payload = {"status": new_status}
    response = requests.put(url, json=payload, headers=HEADERS)
    return response.status_code == 200

# --- USER AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    """Creates a record in the 'Member' class to bypass restricted User settings"""
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        # Notice we are hitting MEMBER_URL now
        response = requests.post(MEMBER_URL, json=payload, headers=HEADERS)
        
        if response.status_code == 201:
            return True
        else:
            # This will now tell us if a field is missing or if permissions are wrong
            error_data = response.json()
            st.error(f"Database Error: {error_data.get('error', 'Unknown Error')}")
            return False
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
