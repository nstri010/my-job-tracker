# --- Add match_score to the data dictionary inside save_job ---
def save_job(company, position, description, job_url, resume_url, match_score="N/A"):
    data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
        "match_score": match_score, # New column
        "status": "Active" 
    }
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False
