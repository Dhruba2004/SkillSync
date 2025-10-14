import streamlit as st
from langchain.document_loaders import PyPDFLoader
import json
import tempfile
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
import os


def load_llm(temperature: 0.5, max_tokens: int = 1024):
    load_dotenv()
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    os.environ['GROQ_API_KEY'] = GROQ_API_KEY
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=temperature,
        max_tokens=max_tokens
    )

system_prompt = """
You are an **AI Career Advisor and Resume Analyzer** designed to give *precise, structured, and actionable* feedback.

🎯 **Objective:**
You will be provided two inputs:
1. **Job Description (JD)** – with role title, required skills, and responsibilities.
2. **Candidate Resume** – with education, skills, projects, certifications, and experience.

Your task is to:
- Parse both documents carefully.
- Compare the resume content against the JD requirements in detail.
- Output a structured JSON report with: match score, missing skills, partially covered skills, recommendations, and feedback.

---

📌 **Output Format (STRICT JSON ONLY, no explanations, no commentary, no markdown):**

{{
  "match_score": 72,
  "missing_skills": ["Kubernetes", "AWS Lambda"],
  "partially_covered_skills": ["Azure Functions"],
  "recommendations": [
    "Highlight cloud-native experience with AWS",
    "Add certification in Kubernetes or Docker",
    "Emphasize leadership experience in DevOps projects"
  ],
  "feedback": "Solid backend expertise but resume lacks emphasis on cloud-native and container orchestration."
}}

---

📌 **Detailed Instructions:**

1. **Match Score (0–100):**
   - Start at 100 and deduct based on gaps:
     - Each missing **critical technical skill**: -5 to -10 points.
     - Each missing **key responsibility / domain requirement**: -3 to -7 points.
     - Lack of alignment in experience vs. JD role level: -5 to -10 points.
   - Reward extra credit (+2–5) for additional highly relevant skills not in JD but useful.
   - Ensure scoring is **balanced and realistic** (not inflated).

2. **Missing Skills:**
   - List **critical hard skills explicitly mentioned in JD but absent in resume**.
   - Examples: Kubernetes, AWS Lambda, React, Terraform, Leadership, Stakeholder Management.
   - Only include skills that are truly absent.

3. **Partially Covered Skills:**
   - List skills that are **similar/related but not exact matches**.
   - Example: Resume has "Azure Functions" but JD asks "AWS Lambda".
   - Example: Resume has "CI/CD pipelines with GitHub Actions" but JD asks "Jenkins".
   - Helps candidate see near-misses they should emphasize or reframe.

4. **Recommendations (actionable):**
   - Always link directly to JD requirements.
   - Categories:
     - **Resume Edits:** Add missing keywords, rearrange sections, emphasize relevant projects.
     - **Skill Development:** Suggest specific certifications, training, or side projects.
     - **Experience Highlighting:** Recommend rephrasing existing experience to align with JD.
   - Keep them **specific, realistic, and measurable** (not vague).

5. **Feedback (short summary):**
   - 2–4 sentences max.
   - Tone: constructive + professional.
   - Highlight strengths + weaknesses.
   - Example: “Strong Java and Spring Boot background. Missing exposure to AWS cloud-native tools. Resume is detailed but lacks keywords from JD such as Kubernetes and Terraform.”

---

📌 **Additional Guidelines:**
- **STRICT JSON ONLY**: Do not include explanations, markdown, or commentary.
- **No hallucination**: Only extract from given JD and Resume.
- **Career Level Sensitivity**: If resume experience level does not align with JD seniority, mention in recommendations.
- **Soft Skills**: Include them only if JD explicitly lists them.
- **Consistency**: Keep field names lowercase with underscores.
- **Formatting**: Ensure valid JSON, no trailing commas, all strings double-quoted.

---

📌 **Context to Analyze:**
Job_Description:
{job_description}

Candidate_Resume:
{candidate_resume}
---
"""


def get_response(resume, jd, temperature, max_tokens):
    llm = load_llm(temperature, max_tokens)
    # prompt -> JD + Resume

    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["job_description", "candidate_resume"]
        )

    chain = prompt | llm | JsonOutputParser()

    return chain.invoke({
        "job_description": jd,
        "candidate_resume": resume
    })

# function to show in Proper Format

def convert_into_dict(result):
    if isinstance(result, str):
        return json.loads(result)
    return result


def render_report(result):
    report = convert_into_dict(result)
    

    # Match SScore Line
    st.subheader("Match Score")
    score = int(report.get("match_score", 0))
    st.metric("Match Score", f"{score}/100")
    st.progress(max(0, min(score, 100)))

    # Missing Skills
    st.subheader("Missing Skills")
    missing_skills = report.get("missing_skills", [])

    if missing_skills:
        for s in missing_skills:
            st.write(f"- {s}")


    # --- Partially covered skills
    st.subheader("Partially Covered Skills")
    partially_covered_skills = report.get("partially_covered_skills", [])

    if partially_covered_skills:
        for s in partially_covered_skills:
            st.write(f"- {s}")
    else:
        st.write("None")


    # Recommendation
    recommendations = report.get("recommendations", [])
    if recommendations:
        for r in recommendations:
            st.write(f"- {r}")

    
    st.subheader("Feedback")
    st.write(report.get("feedback", "No feedback provided."))


    # Json
    with st.expander("View Full JSON Report", expanded=False):
        st.json(report)

    # download as Json
    st.download_button("Download JSON Report", data=json.dumps(report), file_name="report.json", mime="application/json", use_container_width=True)

st.set_page_config(
    page_title="AI Career Advisor",
    page_icon=":guardsman:",
    layout="wide"
)


st.title("🧠 SkillSync")
st.caption("Compare a candidate's Resume against a Job Description and get a structured skill-gap JSON report.")




with st.sidebar:
    st.header("Settings")
    st.markdown("Adjust the parameters for the AI model.")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
    max_tokens = st.slider("Max Tokens", 100, 2000, 1024)
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf"])


if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_file_path = temp_file.name
    pdf_loader = PyPDFLoader(temp_file_path)
    resume = pdf_loader.load()

jd = st.text_area("Job Description", placeholder="Paste the job description here...", width=800, height=300)


if st.button('Analyze'):
    with st.spinner("Analyzing..."):
        if uploaded_file and jd:
            response = get_response(resume, jd, temperature, max_tokens)
            render_report(response)

        else:
            st.error("Please upload a resume and provide a job description.")