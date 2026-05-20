from fpdf import FPDF
import io

def save_job(company, position, description, job_url, resume_url, match_score):
    # 1. Create a PDF in memory from the job description
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Job Record: {company} - {position}", ln=1, align='C')
    pdf.ln(10)
    # Clean description for PDF (FPDF doesn't like some special characters)
    clean_desc = description.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_desc)
    
    pdf_output = pdf.output(dest='S') # Get PDF as string/bytes
    
    # 2. Upload PDF to Supabase storage
    pdf_path = f"previews/{company}_{position}_{match_score.replace('/', '-')}.pdf"
    pdf_url = None
    try:
        supabase.storage.from_("job_previews").upload(
            path=pdf_path, 
            file=pdf_output, 
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        pdf_url = supabase.storage.from_("job_previews").get_public_url(pdf_path)
    except Exception as e:
        st.warning(f"PDF Upload Failed: {e}")

    # 3. Insert everything into the database
    data = {
        "company": company,
        "position": position,
        "description": description,
        "job_url": job_url,
        "resume_link": resume_url,
        "pdf_url": pdf_url, # Now we are saving the link!
        "match_score": match_score,
        "status": "Active" 
    }
    try:
        supabase.table("jobs").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False
