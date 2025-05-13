import tkinter as tk
import subprocess
import sys

def run_script(script_key):
    script_paths = {
        "quick_check": r"Path to Quick_Check.py",
        "candidate_mode": r"Path to Candidate_Mode.py",
        "recruiter_mode": r"Path to Recruiter_Mode.py",
        "model_performance": r"Path to Model_Analyzer.py"
    }

    exe_file = script_paths.get(script_key)
    if exe_file and os.path.exists(exe_file):
        try:
            subprocess.Popen(exe_file, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {exe_file}:\n{str(e)}")
    else:
        messagebox.showerror("File Not Found", f"Executable not found:\n{exe_file}")
    
    # python_exec = sys.executable
    # subprocess.Popen([python_exec, script_paths[script_key]])

def main_ui():
    root = tk.Tk()
    root.title("FrResAlyzer - Mode Selector")
    root.geometry("400x400")
    root.configure(bg="#f0f0f0")

    tk.Label(root, text="FrResAlyzer", font=("Helvetica", 16, "bold"), bg="#f0f0f0").pack(pady=20)

    tk.Button(root, text="Quick Check", width=20, height=2,
              command=lambda: run_script("quick_check")).pack(pady=10)

    tk.Button(root, text="Candidate Mode", width=20, height=2,
              command=lambda: run_script("candidate_mode")).pack(pady=10)

    tk.Button(root, text="Recruiter Mode", width=20, height=2,
              command=lambda: run_script("recruiter_mode")).pack(pady=10)
    
    tk.Button(root, text="Model Analyzer", width=20, height=2,
              command=lambda: run_script("model_performance")).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main_ui()
