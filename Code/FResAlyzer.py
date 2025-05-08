import tkinter as tk
from tkinter import messagebox
import subprocess
import os

def run_script(script_key):
    script_paths = {
        "quick_check": r"Path to Quick_Check.exe",
        "candidate_mode": r"Path to Candidate_Mode.exe",
        "recruiter_mode": r"Path to Recruiter_Mode.exe",
    }

    exe_file = script_paths.get(script_key)
    if exe_file and os.path.exists(exe_file):
        try:
            subprocess.Popen(exe_file, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {exe_file}:\n{str(e)}")
    else:
        messagebox.showerror("File Not Found", f"Executable not found:\n{exe_file}")

def main_ui():
    root = tk.Tk()
    root.title("FrResAlyzer - Mode Selector")
    root.geometry("400x300")
    root.configure(bg="#f0f0f0")

    tk.Label(root, text="FrResAlyzer", font=("Helvetica", 16, "bold"), bg="#f0f0f0").pack(pady=20)

    tk.Button(root, text="Quick Check", width=20, height=2,
              command=lambda: run_script("quick_check")).pack(pady=10)

    tk.Button(root, text="Candidate Mode", width=20, height=2,
              command=lambda: run_script("candidate_mode")).pack(pady=10)

    tk.Button(root, text="Recruiter Mode", width=20, height=2,
              command=lambda: run_script("recruiter_mode")).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main_ui()
