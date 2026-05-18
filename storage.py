import requests
import streamlit as st

# --- CONNECT TO BACK4APP ---
APP_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
REST_KEY = 'OxKhu8kEcoTOlyN2JQ6bF8eghCcySfoVnbHSLEda'

BASE_URL = "https://parseapi.back4app.com/classes/Job"

HEADERS = {
    "X-Parse-Application-Id": APP_ID,
    "X-Parse-REST-API-Key": REST_KEY,
    "Content-Type": "application/json"
}

def save_job(company, position, description):
    """Saves a job to the 'Job' class in Back4App"""
    payload = {
        "company": company,
        "position": position,
        "description": description,
        "status": "Active"
    }
    response = requests.post(BASE_URL, json=payload, headers=HEADERS)
    return response.status_code == 201

def load_jobs():
    """Fetches all jobs from Back4App"""
    response = requests.get(f"{BASE_URL}?order=-createdAt", headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def delete_job(object_id):
    """Deletes a job using its objectId"""
    url = f"{BASE_URL}/{object_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

def update_job_status(object_id, new_status):
    """Updates the status (like Archive/Hidden) for a specific job"""
    url = f"{BASE_URL}/{object_id}"
    payload = {"status": new_status}
    response = requests.put(url, json=payload, headers=HEADERS)
    return response.status_code == 200
