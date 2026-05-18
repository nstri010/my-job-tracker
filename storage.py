from parse_rest.connection import register
from parse_rest.datatypes import Object
import streamlit as st

# --- CONNECT TO BACK4APP ---
# These are your unique keys from your JobTracker dashboard
APPLICATION_ID = 'qloRSo1QY0KMANAydrd3kIRJw2d3JyigbBeyn5tC'
CLIENT_KEY = 'OxKhu8kEcoTOlyN2JQ6bF8eghCcySfoVnbHSLEda'

# This starts the connection
register(APPLICATION_ID, CLIENT_KEY)

# --- DEFINE THE JOB OBJECT ---
class Job(Object):
    pass

# --- DATABASE FUNCTIONS ---

def save_job(company, position, description):
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
        st.error(f"Error saving: {e}")
        return False

def load_jobs():
    try:
        # Fetches all records from your Back4App dashboard
        return Job.Query.all().order_by("-createdAt")
    except Exception as e:
        st.error(f"Error loading: {e}")
        return []

def delete_job(job_id):
    try:
        job_to_del = Job.Query.get(objectId=job_id)
        job_to_del.delete()
        return True
    except Exception as e:
        st.error(f"Error deleting: {e}")
        return False
