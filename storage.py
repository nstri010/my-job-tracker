import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
# Your unique keys from the Back4App dashboard
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
REST_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

# The base URL for your Job class
BASE_URL = "https://parseapi.back4app.com/classes/Job"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-REST-API-Key": REST_KEY,
    "Content-Type": "application/json"
}

# --- JOB DATABASE FUNCTIONS ---

def save_job(company, position, description):
    """Saves a new job application to Back4App"""
    payload = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    response = requests.post(BASE_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    """Fetches all jobs to display in the UI"""
    response = requests.get(f"{BASE_URL}?order=-createdAt", headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def delete_job(object_id):
    """Permanently deletes a job using its objectId"""
    url = f"{BASE_URL}/{object_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

def update_job_status(object_id, new_status):
    """Changes the status of a job (e.g., to 'Hidden')"""
    url = f"{BASE_URL}/{object_id}"
    payload = {"status": new_status}
    response = requests.put(url, json=payload, headers=HEADERS)
    return response.status_code == 200

# --- USER AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    """Creates a new user record in Back4App's built-in User system"""
    # Try the explicit Parse API URL
    user_url = "https://parseapi.back4app.com/users"
    
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        response = requests.post(user_url, json=payload, headers=HEADERS)
        
        # If it fails, this will print the reason to your Streamlit screen
        if response.status_code != 201:
            st.error(f"Backend Error: {response.json().get('error', 'Unknown Error')}")
            return False
            
        return True
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
