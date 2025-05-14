import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import fitz  # PyMuPDF
import docx
import os
import pyperclip
import google.generativeai as genai
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

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
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        else:
            return f"Error: Unsupported file format '{ext}'. Please use PDF/DOCX/TXT format only"
    except UnicodeDecodeError:
        return "Error: Unable to decode the text. Please ensure the file is encoded in UTF-8."
    except Exception as e:
        return f"An unexpected error occurred while reading the file: {str(e)}"

def extract_texts_from_files(file_paths):
    return [(os.path.basename(path), extract_text_from_file(path)) for path in file_paths]

def analyze_resume_with_google_ai(resume_text, job_desc_text, api_key, code_type, pages, job_name, model_name):
    genai.configure(api_key=api_key)

    prompt = f"""
    Analyze the provided resume and job description thoroughly. Perform the following tasks:  

    **Match Analysis:**  
    - Calculate the **match percentage** between the resume and job description.
    - If the match percentage is uncertain or obtained as a range (e.g., Match Percentage: 10 - 15%), then do not give output range. Instead give an average number of the range (e.g., Match percentage(obtained): 10 - 15%, then Match Percentage(output): 12.5%).
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

    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text

def display_result(job_name, text, model_used):
    result_window = tk.Toplevel(root)
    result_window.title(f"Analysis Result - {job_name}")
    result_window.geometry("800x600")

    model_note = tk.Label(result_window, text=f"Result generated using Gemini Model: {model_used}", fg="blue", font=("Arial", 10, "italic"))
    model_note.pack(pady=(5, 0))

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

def show_comparison_chart(match_results):
    import matplotlib.pyplot as plt

    jobs = [item[0] for item in match_results]
    scores = [item[1] for item in match_results]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(jobs, scores, color='skyblue')
    plt.xlabel("Job Description")
    plt.ylabel("Match Percentage")
    plt.title("Resume Match Percentage with Each Job Description")
    plt.ylim(0, 100)

    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width()/2.0, bar.get_height(), f"{score}%", ha='center', va='bottom')

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def show_efficiency_chart():
    try:
        image_path = "C:/Users/user/Desktop/FYP Backup/RP/Figure_1.png"  # Change to your image path
        img = Image.open(image_path)
        img = img.resize((600, 400), Image.Resampling.LANCZOS)

        img_window = tk.Toplevel(root)
        img_window.title("Model Efficiency Chart")

        tk_img = ImageTk.PhotoImage(img)
        label = tk.Label(img_window, image=tk_img)
        label.image = tk_img
        label.pack()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")

def main():
    def upload_resume():
        path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.pdf *.docx *.txt")])
        resume_entry.delete(0, tk.END)
        resume_entry.insert(0, path)

    def upload_job_desc():
        nonlocal job_desc_paths
        paths = filedialog.askopenfilenames(filetypes=[("Supported Files", "*.pdf *.docx *.txt")])
        job_desc_paths = paths
        job_desc_label.config(text=f"{len(paths)} Job Description(s) Selected")

    def analyze():
        api_key = api_entry.get()
        resume_path = resume_entry.get()
        code_type = code_type_var.get()
        pages = pages_var.get()
        selected_model = "models/" + model_var.get()

        if not all([api_key, resume_path, job_desc_paths, code_type, pages, selected_model]):
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        resume_text = extract_text_from_file(resume_path)
        job_desc_texts = extract_texts_from_files(job_desc_paths)

        best_match = {"percentage": 0, "job": None}
        match_results = []

        for job_file, jd_text in job_desc_texts:
            try:
                result = analyze_resume_with_google_ai(resume_text, jd_text, api_key, code_type, pages, job_file, selected_model)
                display_result(job_file, result, selected_model)

                match_line = next((line for line in result.splitlines() if "match percentage" in line.lower()), None)
                if match_line:
                    perc = int(''.join(filter(str.isdigit, match_line)))
                    match_results.append((job_file, perc))
                    if perc > best_match["percentage"]:
                        best_match = {"percentage": perc, "job": job_file}
            except Exception as e:
                messagebox.showerror("Error", f"Error analyzing {job_file}: {str(e)}")

        if best_match["job"]:
            messagebox.showinfo("Best Match Result", f"Most Suitable Job: {best_match['job']}\nMatch: {best_match['percentage']}%")

        if match_results:
            show_comparison_chart(match_results)

    global root
    job_desc_paths = []

    root = tk.Tk()
    root.title("FrResAlyzer - Candidate Mode")
    root.geometry("600x600")

    tk.Label(root, text="Google API Key:").pack()
    api_entry = tk.Entry(root, width=60, show='*')
    api_entry.pack()

    tk.Label(root, text="Upload Resume:").pack()
    resume_entry = tk.Entry(root, width=60)
    resume_entry.pack()
    tk.Button(root, text="Browse", command=upload_resume).pack()

    tk.Label(root, text="Upload Job Descriptions:").pack()
    job_desc_label = tk.Label(root, text="No Job Descriptions Selected")
    job_desc_label.pack()
    tk.Button(root, text="Browse", command=upload_job_desc).pack()

    tk.Label(root, text="Select Resume Code Type:").pack()
    code_type_var = ttk.Combobox(root, values=["LaTex", "HTML and CSS"])
    code_type_var.pack()

    tk.Label(root, text="Select Resume Length:").pack()
    pages_var = ttk.Combobox(root, values=["one", "multi"])
    pages_var.pack()

    tk.Label(root, text="Note: If you get error 429 / invalid API / expired key, please try a different model.",
             fg="red", font=("Arial", 9, "bold")).pack(pady=(10, 2))

    model_frame = tk.Frame(root)
    model_frame.pack()

    model_names = [
        "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-1.5-pro-002", "gemini-1.5-pro-001",
        "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash-preview-04-17",
        "gemini-2.0-flash-thinking-exp-01-21", "gemini-2.5-pro-exp-03-25", "gemini-2.0-flash-lite-preview-02-05",
        "gemini-1.5-flash-8b", "gemini-1.5-flash-002", "gemini-2.0-pro-exp"
    ]

    model_var = ttk.Combobox(model_frame, values=model_names, width=45)
    model_var.pack(side="left", padx=5)

    tk.Button(model_frame, text="Show Model's Efficiencies", command=show_efficiency_chart).pack(side="left")

    tk.Button(root, text="Analyze", command=analyze, bg="green", fg="white").pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()