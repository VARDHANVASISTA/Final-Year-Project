import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import fitz  # PyMuPDF
import docx
import os
import re
import google.generativeai as genai
import matplotlib.pyplot as plt
from google.api_core.exceptions import ResourceExhausted, InvalidArgument

models = [
    "models/gemini-1.5-pro-latest",
    "models/gemini-1.5-flash-latest",
    "models/gemini-1.5-pro-002",
    "models/gemini-1.5-pro-001",
    "models/gemini-1.5-pro",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.5-flash-preview-04-17",
    "models/gemini-2.0-flash-thinking-exp-01-21",
    "models/gemini-2.5-pro-exp-03-25",
    "models/gemini-2.0-flash-lite-preview-02-05",
    "models/gemini-1.5-flash-8b",
    "models/gemini-1.5-flash-002",
    "models/gemini-2.0-pro-exp"
]

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_file(file_path):
    _, ext = os.path.splitext(file_path.lower())
    try:
        if ext == ".pdf":
            return extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return extract_text_from_docx(file_path)
        elif ext == ".txt":
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        else:
            return f"Unsupported file format: {ext}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def extract_match_percentage(text):
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    return float(match.group(1)) if match else 0.0

def analyze_resume_with_all_models(resume_text, job_desc_text, api_key):
    genai.configure(api_key=api_key)
    prompt = f"""
    Analyze the resume and job description. Return only the match percentage as a single number in this format:
    Match Percentage: 85%

    Resume:
    {resume_text}

    Job Description:
    {job_desc_text}
    """
    results = {}
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            score = extract_match_percentage(response.text)
            results[model_name] = {"score": score, "error": None}
        except ResourceExhausted:
            results[model_name] = {"score": 0.0, "error": "Quota Exceeded"}
        except InvalidArgument:
            results[model_name] = {"score": 0.0, "error": "Invalid API Key"}
        except Exception as e:
            err = str(e)
            if "API key" in err.lower():
                results[model_name] = {"score": 0.0, "error": "API Key Error"}
            else:
                results[model_name] = {"score": 0.0, "error": err[:30] + ('...' if len(err) > 30 else '')}
    return results

def plot_match_percentages(results):
    plt.figure(figsize=(14, 7))
    names = list(results.keys())
    scores = [results[m]['score'] for m in names]
    errors = [results[m]['error'] for m in names]
    colors = ['red' if err else 'skyblue' for err in errors]

    bars = plt.bar(names, scores, color=colors)
    plt.ylabel("Match Percentage")
    plt.title("Match Percentage vs Models")
    plt.ylim(0, 100)
    plt.xticks(rotation=30, ha='right', fontsize=9)

    for bar, score, err in zip(bars, scores, errors):
        label = err if err else f"{score:.1f}%"
        y = bar.get_height() + 1
        plt.text(bar.get_x() + bar.get_width()/2.0, y, label, ha='center', va='bottom', fontsize=8, rotation=90 if err else 0)

    plt.tight_layout()
    plt.show()

def main():
    def upload_resume():
        path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt")])
        resume_entry.delete(0, tk.END)
        resume_entry.insert(0, path)

    def upload_job_desc():
        path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt")])
        job_desc_entry.delete(0, tk.END)
        job_desc_entry.insert(0, path)

    def analyze():
        api_key = api_entry.get()
        resume_path = resume_entry.get()
        job_path = job_desc_entry.get()

        if not all([api_key, resume_path, job_path]):
            messagebox.showerror("Input Error", "All fields are required.")
            return

        resume_text = extract_text_from_file(resume_path)
        job_text = extract_text_from_file(job_path)

        try:
            results = analyze_resume_with_all_models(resume_text, job_text, api_key)
            result_text = "\n".join([f"{model}: {res['score']:.1f}%" if not res['error'] else f"{model}: ERROR - {res['error']}" for model, res in results.items()])
            result_window = tk.Toplevel(root)
            result_window.title("Match Percentages")
            result_window.geometry("800x400")
            text_box = scrolledtext.ScrolledText(result_window, wrap=tk.WORD)
            text_box.insert(tk.END, result_text)
            text_box.pack(expand=True, fill="both")
            plot_match_percentages(results)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    root = tk.Tk()
    root.title("FrResAlyzer - Model Analyzer")
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

    tk.Button(root, text="Analyze", command=analyze, bg="green", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()