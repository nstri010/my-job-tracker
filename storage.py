import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'

# CRITICAL: Replace this string with your MASTER KEY from the dashboard
# (It's usually the one right below the REST API Key)
MASTER_KEY = 'PASTE_YOUR_MASTER_KEY_HERE' 

BASE_URL = "https://parseapi.back4app.com/classes/Job"

# This header tells Back4App "I am the owner, let me in"
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
    response = requests.post(BASE_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    response = requests.get(f"{BASE_URL}?order=-createdAt", headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def delete_job(object_id):
    url = f"{BASE_URL}/{object_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

def update_job_status(object_id, new_status):
    url = f"{BASE_URL}/{object_id}"
    payload = {"status": new_status}
    response = requests.put(url, json=payload, headers=HEADERS)
    return response.status_code == 200

# --- USER AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    # The specific endpoint for built-in User management
    user_url = "https://parseapi.back4app.com/users"
    
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    
    try:
        # Using the Master Key header here is what bypasses the "unauthorized" error
        response = requests.post(user_url, json=payload, headers=HEADERS)
        
        if response.status_code == 201:
            return True
        else:
            # This will print the actual error from the server to your app
            st.error(f"Server says: {response.json().get('error')}")
            return False
            
    except Exception as e:
        st.error(f"App Connection Error: {e}")
        return False
