import json
import os
from fpdf import FPDF

# File locations
JOBS_FILE = "jobs.json"
USERS_FILE = "users.json"


# -----------------------------
# LOAD JOBS
# -----------------------------
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []

    with open(JOBS_FILE, "r") as file:
        try:
            return json.load(file)
        except:
            return []


# -----------------------------
# SAVE JOB
# -----------------------------
def save_job(company, position, description, job_url, resume_url, match_score):

    jobs = load_jobs()

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"{company} - {position}", ln=True)
    pdf.ln(10)

    clean_desc = description.encode("latin-1", "ignore").decode("latin-1")
    pdf.multi_cell(0, 10, clean_desc)

    pdf_filename = f"{company}_{position}.pdf".replace(" ", "_")
    pdf.output(pdf_filename)

    # Job data
    job_data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
        "pdf_url": pdf_filename,
        "match_score": match_score
    }

    jobs.append(job_data)

    with open(JOBS_FILE, "w") as file:
        json.dump(jobs, file, indent=4)

    return True


# -----------------------------
# DELETE JOB
# -----------------------------
def delete_job(index):

    jobs = load_jobs()

    if 0 <= index < len(jobs):
        jobs.pop(index)

    with open(JOBS_FILE, "w") as file:
        json.dump(jobs, file, indent=4)


# -----------------------------
# SIGN UP USER
# -----------------------------
def sign_up_user(username, password):

    users = {}

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as file:
            try:
                users = json.load(file)
            except:
                users = {}

    if username in users:
        return False

    users[username] = password

    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

    return True


# -----------------------------
# LOGIN USER
# -----------------------------
def login_user(username, password):

    if not os.path.exists(USERS_FILE):
        return False

    with open(USERS_FILE, "r") as file:
        try:
            users = json.load(file)
        except:
            users = {}

    return users.get(username) == password


# -----------------------------
# UPLOAD RESUME
# -----------------------------
def upload_resume(uploaded_file, username):

    if uploaded_file is None:
        return None

    folder = "resumes"

    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, uploaded_file.name)

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return file_path
