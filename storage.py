import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
# Your unique keys from the Back4App dashboard
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
# Using the Master Key here is our "Skeleton Key" for the database
MASTER_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

# URLs for your classes
# We use 'Member' instead of the restricted 'User' to bypass Free Plan limits
MEMBER_URL = "https://parseapi.back4app.com/classes/Member"
JOB_URL = "https://parseapi.back4app.com/classes/Job"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

# --- JOB DATABASE FUNCTIONS ---

def save_job(company, position, description):
    """Saves a new job application to the Job class"""
    payload = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    response = requests.post(JOB_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    """Fetches all jobs to display in the UI"""
    response = requests.get(f"{JOB_URL}?order=-createdAt", headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def delete_job(object_id):
    """Permanently deletes a job using its objectId"""
    url = f"{JOB_URL}/{object_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

def update_job_status(object_id, new_status):
    """Changes the status of a job (e.g., to 'Hidden')"""
    url = f"{JOB_URL}/{object_id}"
    payload = {"status": new_status}
    response = requests.put(url, json=payload, headers=HEADERS)
    return response.status_code == 200

# --- USER AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    """Creates a new record in our custom Member class"""
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        # Posting to MEMBER_URL instead of the restricted /users endpoint
        response = requests.post(MEMBER_URL, json=payload, headers=HEADERS)
        
        if response.status_code == 201:
            return True
        else:
            # If it still fails, this will show the exact reason from the server
            error_data = response.json()
            st.error(f"Database Error: {error_data.get('error', 'Unknown Error')}")
            return False
            
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
