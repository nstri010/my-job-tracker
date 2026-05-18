import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
MASTER_KEY = 'MC7MUvY03Gm7TsVBYaTgKBvU1VmpdFWrh7d1pxzz'

MEMBER_URL = "https://parseapi.back4app.com/classes/Member"
JOB_URL = "https://parseapi.back4app.com/classes/Job"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-Master-Key": MASTER_KEY,
    "Content-Type": "application/json"
}

# --- JOB DATABASE FUNCTIONS ---

def save_job(company, position, description):
    payload = {"company": company, "position": position, "description": description, "status": "Active"}
    response = requests.post(JOB_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    response = requests.get(f"{JOB_URL}?order=-createdAt", headers=HEADERS)
    return response.json().get("results", []) if response.status_code == 200 else []

def delete_job(object_id):
    url = f"{JOB_URL}/{object_id}"
    return requests.delete(url, headers=HEADERS).status_code == 200

def update_job_status(object_id, new_status):
    url = f"{JOB_URL}/{object_id}"
    payload = {"status": new_status}
    return requests.put(url, json=payload, headers=HEADERS).status_code == 200

# --- USER AUTHENTICATION FUNCTIONS ---

def sign_up_user(username, password, email):
    payload = {"username": username, "password": password, "email": email}
    try:
        response = requests.post(MEMBER_URL, json=payload, headers=HEADERS)
        if response.status_code == 201:
            return True
        else:
            st.error(f"Database Error: {response.json().get('error')}")
            return False
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False
