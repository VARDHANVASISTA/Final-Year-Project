import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import os
import fitz  # PyMuPDF
import docx
import google.generativeai as genai
import re
import time
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from google.api_core.exceptions import ResourceExhausted

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
    name_match = re.search(r'(?i)\*\*Candidate Name\*\*\s*[:\-\u2013]?\s*(.+)', text)
    if name_match:
        return name_match.group(1).strip().split('\n')[0]
    return "Unknown"

def analyze_with_google_ai(resume_text, job_desc_text, api_key, model_name, max_retries=3):
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

    model = genai.GenerativeModel(f"models/{model_name}")

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

def display_shortlisted_only(results, top_n, selected_model_name):
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    top_results = sorted_results[:top_n]

    shortlist_win = tk.Toplevel()
    shortlist_win.title(f"Shortlisted Candidates - Gemini Model: {selected_model_name}")
    shortlist_win.geometry("800x500")

    text_box = scrolledtext.ScrolledText(shortlist_win, wrap=tk.WORD)
    summary_text = f"Results generated using Gemini Model: {selected_model_name}\n\n"
    text_box.insert(tk.END, summary_text)
    for name, percent, _ in top_results:
        line = f"{name}: {percent}%\n"
        text_box.insert(tk.END, line)
        summary_text += line
    text_box.pack(expand=True, fill="both")

    def copy_to_clipboard():
        shortlist_win.clipboard_clear()
        shortlist_win.clipboard_append(summary_text)
        shortlist_win.update()
        messagebox.showinfo("Copied", "Shortlist copied to clipboard!")

    def export_results():
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if export_path:
            try:
                df = pd.DataFrame([(name, percent) for name, percent, _ in top_results],
                                  columns=["Candidate Name", "Match Percentage"])
                if export_path.endswith(".csv"):
                    df.to_csv(export_path, index=False)
                elif export_path.endswith(".xlsx"):
                    df.to_excel(export_path, index=False)
                else:
                    messagebox.showwarning("File Type", "Unsupported file type selected.")
                    return
                messagebox.showinfo("Exported", f"Shortlist exported to:\n{export_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"An error occurred:\n{str(e)}")

    def show_bar_graph():
        names = [name for name, _, _ in results]
        percentages = [percent for _, percent, _ in results]
        plt.figure(figsize=(10, 6))
        plt.bar(names, percentages, color='skyblue')
        plt.xlabel("Candidates")
        plt.ylabel("Match Percentage")
        plt.title("Candidate Match Percentages")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    button_frame = tk.Frame(shortlist_win)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Export to CSV/Excel", command=export_results).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Show Bar Graph", command=show_bar_graph).pack(side=tk.LEFT, padx=5)

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

    def show_efficiency_image():
        img_path = "./model_efficiency_graph.png"  # Replace with your actual image path
        if os.path.exists(img_path):
            img_win = tk.Toplevel()
            img_win.title("Model Efficiency Graph")
            img = Image.open(img_path)
            img = img.resize((800, 500), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(img_win, image=photo)
            label.image = photo
            label.pack()
        else:
            messagebox.showerror("File Not Found", f"Image not found at: {img_path}")

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

        selected_model_name = model_var.get()
        job_text = extract_text_from_file(job_path)
        match_results = []

        for res_path in resume_paths:
            res_text = extract_text_from_file(res_path)
            response_text = analyze_with_google_ai(res_text, job_text, api_key, selected_model_name)
            rt = list(response_text)
            pct = rt[-4] + rt[-3]
            if rt[-5].isnumeric():
                pct = rt[-5] + pct
            percentage = float(pct)
            candidate_name = extract_candidate_name(response_text)
            match_results.append((candidate_name, percentage, response_text))
            time.sleep(5)

        display_shortlisted_only(match_results, top_n, selected_model_name)

    root = tk.Tk()
    root.title("FrResAlyzer - Recruiter Mode")
    root.geometry("800x600")

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

    note_frame = tk.Frame(root)
    note_frame.pack(fill='x', padx=10, pady=(10, 5))
    tk.Label(note_frame, text="Note: Please use different models if you face error-429 or API key expired or invalid.", fg="red", anchor="center", justify="center", wraplength=700).pack()

    model_frame = tk.Frame(root)
    model_frame.pack(pady=10)

    tk.Label(model_frame, text="Select Gemini Model:").pack(side=tk.LEFT, padx=5)

    model_var = tk.StringVar()
    model_choices = [
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-002",
        "gemini-1.5-pro-001",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-preview-04-17",
        "gemini-2.0-flash-thinking-exp-01-21",
        "gemini-2.5-pro-exp-03-25",
        "gemini-2.0-flash-lite-preview-02-05",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash-002",
        "gemini-2.0-pro-exp"
    ]
    model_var.set(model_choices[0])
    model_dropdown = ttk.Combobox(model_frame, textvariable=model_var, values=model_choices, width=40)
    model_dropdown.pack(side=tk.LEFT, padx=5)

    tk.Button(model_frame, text="Show Model's Efficiencies", command=show_efficiency_image).pack(side=tk.LEFT, padx=5)

    tk.Button(root, text="Analyze", command=analyze, bg="green", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()