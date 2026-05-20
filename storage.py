import streamlit as st
from supabase import create_client, Client
from fpdf import FPDF
import io

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets Error: Check Streamlit Secrets.")
    st.stop()

def sign_up_user(username, password):
    email = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response.user is not None
    except: return False

def login_user(username, password):
    email = f"{username}@tracker.com"
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user is not None
    except: return False

def upload_resume(file_obj, username):
    try:
        file_path = f"{username}/{file_obj.name}"
        supabase.storage.from_("resumes").upload(path=file_path, file=file_obj.getvalue(), file_options={"upsert": "true"})
        res = supabase.storage.from_("resumes").get_public_url(file_path)
        return res
    except Exception as e:
        st.error(f"Upload Error: {e}")
        return None

def save_job(company, position, description, job_url, resume_url, match_score):
    # 1. Create PDF in memory
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Job Record: {company} - {position}", ln=1, align='C')
    pdf.ln(10)
    
    # Handle special characters for FPDF
    clean_desc = description.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_desc)
    pdf_output = pdf.output(dest='S') 

    # 2. Upload PDF to Supabase
    pdf_path = f"previews/{company}_{position}.pdf"
    pdf_url = None
    try:
        supabase.storage.from_("job_previews").upload(
            path=pdf_path, 
            file=pdf_output, 
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        pdf_url = supabase.storage.from_("job_previews").get_public_url(pdf_path)
    except Exception as e:
        st.warning(f"PDF Preview Failed: {e}")

    # 3. Save to Database
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
        st.error(f"Save Error: {e}")
        return False

def load_jobs():
    try:
        response = supabase.table("jobs").select("*").order("created_at", desc=True).execute()
        return response.data
    except: return []

def delete_job(job_id):
    try:
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return True
    except: return False
