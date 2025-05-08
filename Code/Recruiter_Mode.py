import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import os
import fitz  # PyMuPDF
import docx
import google.generativeai as genai
import re
import time
from google.api_core.exceptions import ResourceExhausted

# ---------- Utility Functions ----------
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_file(file_path):
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
            return f"Error: Unsupported file format '{ext}'."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def extract_candidate_name(text):
    name_match = re.search(r'(?i)\*\*Candidate Name\*\*\s*[:\-–]?\s*(.+)', text)
    if name_match:
        return name_match.group(1).strip().split('\n')[0]
    return "Unknown"

def analyze_with_google_ai(resume_text, job_desc_text, api_key, max_retries=3):
    genai.configure(api_key=api_key)

    prompt = f"""
    Compare the following resume with the given job description and perform:
    - Calculate **Match Percentage** between resume and job description.
    - Extract **Candidate Name**.

    Provide response in this format:
    **Candidate Name**: John Doe
    **Match Percentage**: 85%
    Give only the above information. Don't give any details.
    Resume:
    {resume_text}

    Job Description:
    {job_desc_text}
    """

    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except ResourceExhausted as e:
            wait_time = 60 if attempt == max_retries else 15 * attempt
            print(f"[Retry {attempt}] Quota exhausted. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            if "API key expired" in str(e) or "API_KEY_INVALID" in str(e):
                messagebox.showerror("API Key Error", "Your Google API key is invalid or expired. Please renew it.")
                return "Error: Invalid API key."
            print(f"Error during AI analysis: {e}")
            return "Error during AI analysis."
    return "Quota exhausted after retries."

# ---------- GUI Code ----------
def main():
    resume_paths = []

    def upload_job_desc():
        path = filedialog.askopenfilename(filetypes=[["Supported Files", "*.pdf *.docx *.txt"]])
        job_desc_entry.delete(0, tk.END)
        job_desc_entry.insert(0, path)

    def upload_resumes():
        nonlocal resume_paths
        paths = filedialog.askopenfilenames(filetypes=[["Supported Files", "*.pdf *.docx *.txt"]])
        resume_paths = paths
        resume_label.config(text=f"{len(paths)} Resume(s) Selected")

    def display_shortlisted_only(results, top_n):
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        top_results = sorted_results[:top_n]

        shortlist_win = tk.Toplevel()
        shortlist_win.title("Shortlisted Candidates")
        shortlist_win.geometry("600x400")

        text_box = scrolledtext.ScrolledText(shortlist_win, wrap=tk.WORD)
        summary_text = ""
        for name, percent, _ in top_results:
            line = f"{name}: {percent}%\n"
            text_box.insert(tk.END, line)
            summary_text += line
        text_box.pack(expand=True, fill="both")

        def copy_to_clipboard():
            root.clipboard_clear()
            root.clipboard_append(summary_text)
            root.update()
            messagebox.showinfo("Copied", "Shortlist copied to clipboard!")

        copy_button = tk.Button(shortlist_win, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_button.pack(pady=10)

        shortlist_win.protocol("WM_DELETE_WINDOW", lambda: shortlist_win.destroy())

    def analyze():
        api_key = api_entry.get()
        job_path = job_desc_entry.get()
        try:
            top_n = int(top_n_entry.get())
        except:
            messagebox.showerror("Input Error", "Please enter a valid number for top N candidates.")
            return

        if not all([api_key, job_path, resume_paths]):
            messagebox.showerror("Input Error", "Please fill all fields and upload necessary files.")
            return

        job_text = extract_text_from_file(job_path)
        match_results = []

        for res_path in resume_paths:
            res_text = extract_text_from_file(res_path)
            response_text = analyze_with_google_ai(res_text, job_text, api_key)
            rt = list(response_text)
            pct = rt[-4] + rt[-3]
            if rt[-5].isnumeric():
                pct = rt[-5] + pct
            percentage = float(pct)
            candidate_name = extract_candidate_name(response_text)
            match_results.append((candidate_name, percentage, response_text))
            time.sleep(5)

        display_shortlisted_only(match_results, top_n)

    root = tk.Tk()
    root.title("FrResAlyzer - Recruiter Mode")
    root.geometry("700x500")

    tk.Label(root, text="Google API Key:").pack()
    api_entry = tk.Entry(root, width=60, show='*')
    api_entry.pack()

    tk.Label(root, text="Upload Job Description:").pack()
    job_desc_entry = tk.Entry(root, width=60)
    job_desc_entry.pack()
    tk.Button(root, text="Browse", command=upload_job_desc).pack()

    tk.Label(root, text="Upload Resumes (Multiple):").pack()
    resume_label = tk.Label(root, text="No Resumes Selected")
    resume_label.pack()
    tk.Button(root, text="Browse", command=upload_resumes).pack()

    tk.Label(root, text="Number of Candidates to Shortlist:").pack()
    top_n_entry = tk.Entry(root, width=10)
    top_n_entry.pack()

    tk.Button(root, text="Analyze", command=analyze, bg="green", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
