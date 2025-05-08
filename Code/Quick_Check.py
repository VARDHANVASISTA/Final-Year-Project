import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import fitz  # PyMuPDF
import docx
import os
import pyperclip
import google.generativeai as genai
from PIL import Image
import pytesseract
import webbrowser  

# Extract functions
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_file(file_path):
    if not os.path.exists(file_path):
        return f"Error: File not found at '{file_path}'. Please check the path."

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == ".pdf":
            return extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return extract_text_from_docx(file_path)
        elif ext == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"Error: Unsupported file format '{ext}'. Please use PDF/DOCX/TXT format only"
    except UnicodeDecodeError:
        return "Error: Unable to decode the text. Please ensure the file is encoded in UTF-8."
    except Exception as e:
        return f"An unexpected error occurred while reading the file: {str(e)}"

def analyze_resume_with_google_ai(resume_text, job_desc_text, api_key, code_type, pages):
    genai.configure(api_key=api_key)

    prompt = f"""
    Analyze the provided resume and job description thoroughly. Perform the following tasks:  

    **Match Analysis:**  
    - Calculate the **match percentage** between the resume and job description.  
    - List the **missing skills**, technologies, and experience that are relevant but not present in the resume in detail.
    - If the Job description states that the job requires an experience > 0 years, then give an output similar to "This (Job Title) Job from (Company Name) is not suitable for you as it requires an experience of (years of experience as mentioned in Job description) years" and terminate don't give any other output.  

    **Resume Improvement Suggestions:**  
    - Give in detail, suggestions on improvements to make the resume align better with the job description.  
    - Provide a **modern, industry-standard resume template** that is trending in the tech industry (Give only name and in which website it is found. Do not give direct link.).

    **Generate an Optimized Resume in {code_type}:**  
    - Create a **{pages}-page A4-sized resume** in **{code_type}** that achieves the **highest possible match percentage** with the given job description.  
    - Use a **clean, ATS-friendly, and professional format** that you have recommended as a template.  
    - Ensure the formatting includes:
      - A clear **header** with name, contact details, and LinkedIn/GitHub (if applicable).
      - An **education section** with degree details.
      - A **skills section** highlighting the most relevant skills.
      - A **projects section** that best matches the job role.
    - The {code_type} code should be **fully formatted and ready for compilation**.  

    ### **Input Data**
    **Resume:**  
    {resume_text}  

    **Job Description:**  
    {job_desc_text}  

    Provide the results in the following format:  
    **Match Percentage**: (e.g., 85%)  
    **Missing Skills**: (List)  
    **Suggested Resume Template**: Direct Link 
    **Generated Resume Code**: (Fully formatted and ready to use)
    """
    #     - Include a 100 % accurate **direct link** to a recommended resume template.  

    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    return response.text

# Tkinter UI
def main():
    def upload_resume():
        path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt *.jpg *.jpeg *.png")])
        resume_entry.delete(0, tk.END)
        resume_entry.insert(0, path)

    def upload_job_desc():
        path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt *.jpg *.jpeg *.png")])
        job_desc_entry.delete(0, tk.END)
        job_desc_entry.insert(0, path)

    def display_result(text):
        result_window = tk.Toplevel(root)
        result_window.title("Analysis Result")
        result_window.geometry("800x600")

        text_box = scrolledtext.ScrolledText(result_window, wrap=tk.WORD, font=("Arial", 10))
        text_box.insert(tk.END, text)
        text_box.pack(expand=True, fill="both")

        def show_code():
            code_window = tk.Toplevel(result_window)
            code_window.title("Generated Resume Code")
            code_window.geometry("800x600")
            code_box = scrolledtext.ScrolledText(code_window, wrap=tk.WORD, font=("Courier", 10))

            start = text.lower().find("generated resume code")
            if start != -1:
                code = text[start:].split("\n", 1)[-1].strip()
            else:
                code = "No code found"
            code_box.insert(tk.END, code)
            code_box.pack(expand=True, fill="both")

            def copy_code():
                pyperclip.copy(code)
                messagebox.showinfo("Copied", "Code copied to clipboard!")

            copy_btn = tk.Button(code_window, text="Copy Code", command=copy_code)
            copy_btn.pack(pady=5)

        show_code_btn = tk.Button(result_window, text="Show Resume Code", command=show_code)
        show_code_btn.pack(pady=5)

    def analyze():
        api_key = api_entry.get()
        resume_path = resume_entry.get()
        job_desc_path = job_desc_entry.get()
        code_type = code_type_var.get()
        pages = pages_var.get()

        if not all([api_key, resume_path, job_desc_path, code_type, pages]):
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        resume_text = extract_text_from_file(resume_path)
        job_desc_text = extract_text_from_file(job_desc_path)

        try:
            result = analyze_resume_with_google_ai(resume_text, job_desc_text, api_key, code_type, pages)
            display_result(result)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    root = tk.Tk()
    root.title("FrResAlyzer - Quick Check")
    root.geometry("600x400")

    tk.Label(root, text="Google API Key:").pack()
    api_entry = tk.Entry(root, width=60, show='*')
    api_entry.pack()

    tk.Label(root, text="Upload Resume:").pack()
    resume_entry = tk.Entry(root, width=60)
    resume_entry.pack()
    tk.Button(root, text="Browse", command=upload_resume).pack()

    tk.Label(root, text="Upload Job Description:").pack()
    job_desc_entry = tk.Entry(root, width=60)
    job_desc_entry.pack()
    tk.Button(root, text="Browse", command=upload_job_desc).pack()

    tk.Label(root, text="Select Resume Code Type:").pack()
    code_type_var = ttk.Combobox(root, values=["LaTex", "HTML and CSS"])
    code_type_var.pack()

    tk.Label(root, text="Select Resume Length:").pack()
    pages_var = ttk.Combobox(root, values=["one", "multi"])
    pages_var.pack()

    tk.Button(root, text="Analyze", command=analyze, bg="green", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
