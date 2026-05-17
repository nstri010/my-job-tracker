import json
import os
from datetime import datetime

FILE_NAME = "job_tracker.json"
RESUME_FOLDER = "resumes"

if not os.path.exists(RESUME_FOLDER):
    os.makedirs(RESUME_FOLDER)


def load_jobs():
    if not os.path.exists(FILE_NAME):
        return []
    try:
        with open(FILE_NAME, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_job(new_job):
    jobs = load_jobs()
    if any(j['company'].lower() == new_job['company'].lower() and
           j['position'].lower() == new_job['position'].lower() for j in jobs):
        return False

    jobs.append(new_job)
    with open(FILE_NAME, "w") as f:
        json.dump(jobs, f, indent=4)
    return True


def update_job_status(job_id, new_status):
    jobs = load_jobs()
    for job in jobs:
        if str(job['id']) == str(job_id):
            job['status'] = new_status
            break
    with open(FILE_NAME, "w") as f:
        json.dump(jobs, f, indent=4)


def update_job_details(job_id, updated_company, updated_position, updated_description):
    jobs = load_jobs()
    for job in jobs:
        if str(job['id']) == str(job_id):
            job['company'] = updated_company
            job['position'] = updated_position
            job['description'] = updated_description
            break
    with open(FILE_NAME, "w") as f:
        json.dump(jobs, f, indent=4)


def build_job_record(company, position, description, applied_date, resume_name=None, snapshot_name=None):
    return {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "date_applied": applied_date.strftime("%Y-%m-%d"),
        "company": company,
        "position": position,
        "description": description,
        "resume_filename": resume_name,
        "snapshot_filename": snapshot_name,
        "status": "Applied"
    }