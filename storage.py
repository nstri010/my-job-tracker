import streamlit as st
from supabase import create_client, Client
from fpdf import FPDF
import io

# Initialize Supabase using secrets
# Ensure these are set in your Streamlit Cloud "Secrets" settings
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def login_user(username, password):
    """Checks if user exists with the given password."""
    try:
        res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        return len(res.data) > 0
    except Exception as e:
        st.error(f"Login Error: {e}")
        return False

def sign_up_user(username, password):
    """Creates a new user entry in the 'users' table."""
    try:
        supabase.table("users").insert({"username": username, "password": password}).execute()
        return True
    except Exception as e:
        # Usually fails if username (primary key) already exists
        return False

def load_jobs():
    """Fetches all applications from the 'jobs' table."""
    try:
        res = supabase.table("jobs").select("*").execute()
        return res.data
    except Exception as e:
        st.error(f"Error loading jobs: {e}")
        return []

def delete_job(job_id):
    """Deletes a specific job record."""
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False

def upload_resume(uploaded_file, username):
    """Uploads a resume file to Supabase Storage and returns the public URL."""
    try:
        path = f"resumes/{username}_{uploaded_file.name}"
        supabase.storage.from_("resumes").upload(
            path=path,
            file=uploaded_file.getvalue(),
            file_options={"content-type": uploaded_file.type, "upsert": "true"}
        )
        return supabase.storage.from_("resumes").get_public_url(path)
    except Exception as e:
        st.warning(f"Resume Upload Failed: {e}")
        return None

def save_job(company, position, description, job_url, resume_url, match_score):
    """Generates a PDF of the job description and saves the record to the database."""
    # 1. Create a PDF in memory
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Job Record: {company} - {position}", ln=1, align='C')
    pdf.ln(10)
    
    # Clean description for FPDF (strips non-latin-1 characters)
    clean_desc = description.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_desc)
    pdf_output = pdf.output(dest='S')
    
    # 2. Upload PDF to Supabase storage
    safe_score = str(match_score).replace('/', '-')
    pdf_path = f"previews/{company}_{position}_{safe_score}.pdf"
    pdf_url = None
    try:
        supabase.storage.from_("job_previews").upload(
            path=pdf_path, 
            file=pdf_output, 
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        pdf_url = supabase.storage.from_("job_previews").get_public_url(pdf_path)
    except Exception as e:
        st.warning(f"PDF Preview Upload Failed: {e}")

    # 3. Insert into Database
    data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
        "pdf_url": pdf_url,
        "match_score": match_score,
        "status": "Active" 
    }
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Save Error: {e}")
        return False
