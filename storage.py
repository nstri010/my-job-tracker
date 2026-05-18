from parse_rest.connection import register
from parse_rest.datatypes import Object
import streamlit as st

# --- CONNECT TO BACK4APP ---
# These keys are from your JobTracker dashboard screenshot
APPLICATION_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
CLIENT_KEY = 'OxKhu8kEcoTOlyN2JQ6bF8eghCcySfoVnbHSLEda'

# This registers the connection so Python can talk to Back4App
register(APPLICATION_ID, CLIENT_KEY)

# --- DEFINE THE JOB OBJECT ---
# This acts as the blueprint for the 'Job' class you created in Step 1
class Job(Object):
    pass

# --- DATABASE FUNCTIONS ---

def save_job(company, position, description):
    """
    Saves a new job application to your Back4App database.
    This replaces the old 'append_row' logic from Google Sheets.
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
    Fetches all jobs stored in Back4App to display them on your site.
    Equivalent to a 'Query' in your BeReal Swift project.
    """
    try:
        # Fetching all records and sorting by the date they were created
        return Job.Query.all().order_by("-createdAt")
    except Exception as e:
        st.error(f"Error loading from Back4App: {e}")
        return []

def delete_job(job_id):
    """
    Deletes a specific job application using its unique Back4App objectId.
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
    Updates the status of a job (e.g., changing it to 'Hidden' or 'Applied').
    """
    try:
        job_to_update = Job.Query.get(objectId=job_id)
        job_to_update.status = new_status
        job_to_update.save()
        return True
    except Exception as e:
        st.error(f"Error updating status: {e}")
        return False
