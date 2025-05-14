# === backend.py ===
%%writefile backend.py

import fitz  # PyMuPDF
import docx
import os
import google.generativeai as genai

def extract_text(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext == ".pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    elif ext == ".docx":
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == ".txt":
        return uploaded_file.read().decode("utf-8")
    else:
        return "Unsupported file format."

def analyze_resume_with_google_ai(resume_text, jd_text, api_key, code_type, pages, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Analyze the provided resume and job description thoroughly. Perform the following tasks:

    **Match Analysis:**
    - Calculate the **match percentage** between the resume and job description.
    - List the **missing skills**, technologies, and experience.
    - If the JD requires > 0 years experience and resume lacks it, terminate with explanation.

    **Resume Suggestions:**
    - Suggest detailed improvements to align resume to JD.
    - Recommend a trending resume template (name + site, no direct link).

    **Optimized Resume in {code_type}:**
    - A {pages}-page A4 resume in {code_type}, formatted and ready to compile.

    ### Input Data
    **Resume:**
    {resume_text}

    **Job Description:**
    {jd_text}

    ### Format Output
    **Match Percentage**: (e.g., 85%)
    **Missing Skills**: (List)
    **Suggested Resume Template**: Name and Website
    **Generated Resume Code**: (Formatted code)
    """
    response = model.generate_content(prompt)
    return response.text

def get_match_only(resume_text, jd_text, api_key, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = f"""
    Compare the resume with the job description. Just output the match percentage.

    Resume:
    {resume_text}

    Job Description:
    {jd_text}

    Format:
    Match: NN%
    """
    response = model.generate_content(prompt)
    return response.text.strip()
