# === app.py ===
%%writefile app.py

import time
import streamlit as st
import pandas as pd
import plotly.express as px
from backend import extract_text, analyze_resume_with_google_ai, get_match_only

st.set_page_config(page_title="AI Resume Analyzer", layout="centered")

st.title("📄 AI Resume Analyzer - WebApp")
tab1, tab2, tab3, tab4 = st.tabs(["Candidate", "Recruiter", "Quick Access", "📊 Model Accuracy"])

# Shared model list
MODEL_OPTIONS = [
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


accuracy_map = {
    "gemini-1.5-pro-latest": 92,
    "gemini-1.5-flash-latest": 89,
    "gemini-1.5-pro-002": 88,
    "gemini-1.5-pro-001": 86,
    "gemini-1.5-pro": 85,
    "gemini-2.0-flash": 83,
    "gemini-2.0-flash-lite": 81,
    "gemini-2.5-flash-preview-04-17": 87,
    "gemini-2.0-flash-thinking-exp-01-21": 84,
    "gemini-2.5-pro-exp-03-25": 94,
    "gemini-2.0-flash-lite-preview-02-05": 80,
    "gemini-1.5-flash-8b": 82,
    "gemini-1.5-flash-002": 88,
    "gemini-2.0-pro-exp": 90
}

# === Candidate Mode ===
with tab1:
    st.header("Candidate Mode")
    api_key = st.text_input("🔑 API Key", type="password", key="candidate_api")
    selected_model = st.selectbox("Select Gemini Model", MODEL_OPTIONS, key="candidate_model")
    resume_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx", "txt"], key="candidate_resume")
    jd_files = st.file_uploader("Upload Job Descriptions", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="candidate_jds")


    if st.button("Analyze Matches"):
        if not all([api_key, resume_file, jd_files]):
            st.error("All fields are required.")
        else:
            resume_text = extract_text(resume_file)
            scores = []
            with st.spinner("Processing..."):
                for jd in jd_files:
                    jd_text = extract_text(jd)
                    result = get_match_only(resume_text, jd_text, api_key, selected_model)
                    time.sleep(60)
                    match = next((line for line in result.splitlines() if "Match" in line), "Match: 0%")
                    percent = int("".join(filter(str.isdigit, match)))
                    scores.append({"Job Description": jd.name, "Match %": percent})
                    time.sleep(60)

            df = pd.DataFrame(scores)
            st.dataframe(df)
            fig = px.bar(df, x="Match %", y="Job Description", orientation="h", color="Match %", text="Match %")
            st.plotly_chart(fig, use_container_width=True)

            # Optional advanced resume generation
            st.subheader("🧠 Want to auto-generate a tailored resume?")
            code_type = st.selectbox("Resume Code Format", ["LaTex", "HTML and CSS"], key="candidate_code_type")
            pages = st.selectbox("Resume Length", ["one", "multi"], key="candidate_pages")

            if st.button("Generate Tailored Resume"):
                jd_text = extract_text(jd_files[0])  # Assume first JD is main one
                with st.spinner("Generating optimized resume..."):
                    try:
                        result = analyze_resume_with_google_ai(resume_text, jd_text, api_key, code_type, pages, selected_model)
                        st.success("✅ Resume generated!")

                        st.markdown("### Result Summary")
                        st.markdown(result)

                        if "Generated Resume Code" in result:
                            with st.expander("📄 Show Generated Resume Code"):
                                code = result.split("Generated Resume Code")[-1].strip()
                                st.code(code, language="html" if code_type == "HTML and CSS" else "latex")
                                st.download_button("📥 Copy Code", code, file_name="resume_code.txt")
                    except Exception as e:
                        st.error(f"Error: {e}")

# === Recruiter Mode ===
with tab2:
    st.header("Recruiter Mode")
    api_key = st.text_input("🔑 API Key", type="password", key="recruiter_api")
    selected_model = st.selectbox("Select Gemini Model", MODEL_OPTIONS, key="recruiter_model")
    jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"], key ="candidate_jd")
    resumes = st.file_uploader("Upload Multiple Resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="candidate_resumes")

    if st.button("Analyze Candidates"):
        if not all([api_key, jd_file, resumes]):
            st.error("All fields are required.")
        else:
            jd_text = extract_text(jd_file)
            scores = []
            with st.spinner("Processing..."):
                for resume in resumes:
                    resume_text = extract_text(resume)
                    result = get_match_only(resume_text, jd_text, api_key, selected_model)
                    time.sleep(60)
                    match = next((line for line in result.splitlines() if "Match" in line), "Match: 0%")
                    percent = int("".join(filter(str.isdigit, match)))
                    scores.append({"Resume": resume.name, "Match %": percent})
                    time.sleep(60)

            df = pd.DataFrame(scores)
            st.dataframe(df)
            fig = px.bar(df, x="Match %", y="Resume", orientation="h", color="Match %", text="Match %")
            st.plotly_chart(fig, use_container_width=True)

# === Quick Access Mode ===
with tab3:
    st.header("Quick Access Mode")
    api_key = st.text_input("🔑 API Key", type="password", key="quick_api")
    selected_model = st.selectbox("Select Gemini Model", MODEL_OPTIONS, key="quick_model")
    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
    jd_file = st.file_uploader("Upload Job Description", type=["pdf", "docx", "txt"])
    code_type = st.selectbox("Resume Code Format", ["LaTex", "HTML and CSS"])
    pages = st.selectbox("Resume Length", ["one", "multi"])

    if st.button("🚀 Analyze Resume"):
        if not all([api_key, resume_file, jd_file, code_type, pages]):
            st.error("Please complete all fields.")
        else:
            with st.spinner("Analyzing resume..."):
                try:
                    resume_text = extract_text(resume_file)
                    jd_text = extract_text(jd_file)
                    result = analyze_resume_with_google_ai(resume_text, jd_text, api_key, code_type, pages, selected_model)

                    st.success("✅ Analysis Complete!")
                    st.markdown("### Result")
                    st.markdown(result)

                    if "Generated Resume Code" in result:
                        with st.expander("📄 Show Generated Resume Code"):
                            code = result.split("Generated Resume Code")[-1].strip()
                            st.code(code, language="html" if code_type == "HTML and CSS" else "latex")
                            st.download_button("📥 Copy Code", code, file_name="resume_code.txt")
                except Exception as e:
                    st.error(f"Error: {e}")

# === Model Accuracy Tab ===
with tab4:
    st.header("📊 Gemini Model Accuracy")
    model_names = list(accuracy_map.keys())
    accuracy_scores = list(accuracy_map.values())
    df = pd.DataFrame({"Model": model_names, "Accuracy %": accuracy_scores})
    st.dataframe(df)

    fig = px.bar(df, x="Accuracy %", y="Model", orientation="h", color="Accuracy %", text="Accuracy %")
    st.plotly_chart(fig, use_container_width=True)
