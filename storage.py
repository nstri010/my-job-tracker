from parse_rest.connection import register
from parse_rest.datatypes import Object
import streamlit as st

# --- CONNECT TO BACK4APP ---
# Your specific credentials from the Back4App dashboard screenshot
APPLICATION_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
CLIENT_KEY = 'OxKhu8kEcoTOlyN2JQ6bF8eghCcySfoVnbHSLEda'

# Initialize the connection to your Back4App backend
register(APPLICATION_ID, CLIENT_KEY)

# --- DEFINE THE JOB OBJECT ---
# This matches the 'Job' class you created in the Back4App database
class Job(Object):
    pass

# --- DATABASE FUNCTIONS ---

def save_job(company, position, description):
    """
    Saves a new job application to Back4App.
    """
    try:
        new_job = Job(
            company=company,
            position=position,
            description=description,
            status="Active"
        )
        new_job.save()
        return True
    except Exception as e:
        st.error(f"Error saving to Back4App: {e}")
        return False

def load_jobs():
    """
    Fetches all jobs from Back4App. 
    Equivalent to the Query logic in your Swift BeReal project.
    """
    try:
        # Fetches all records and sorts by newest first
        return Job.Query.all().order_by("-createdAt")
    except Exception as e:
        st.error(f"Error loading from Back4App: {e}")
        return []

def delete_job(job_id):
    """
    Deletes a job using its unique objectId.
    """
    try:
        job_to_del = Job.Query.get(objectId=job_id)
        job_to_del.delete()
        return True
    except Exception as e:
        st.error(f"Error deleting job: {e}")
        return False

def update_job_status(job_id, new_status):
    """
    Updates the status column (e.g., changing 'Active' to 'Hidden').
    """
    try:
        job_to_update = Job.Query.get(objectId=job_id)
        job_to_update.status = new_status
        job_to_update.save()
        return True
    except Exception as e:
        st.error(f"Error updating status: {e}")
        return False
