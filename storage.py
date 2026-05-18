import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
# Your unique keys from the Back4App dashboard
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
REST_KEY = 'OxKhu8kEcoTOlyN2JQ6bF8eghCcySfoVnbHSLEda'

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
    user_url = "https://parseapi.back4app.com/users"
    payload = {
        "username": username,
        "password": password,
        "email": email
    }
    # We use the same HEADERS because the App ID and REST Key are the same
    response = requests.post(user_url, json=payload, headers=HEADERS)
    return response.status_code == 201
