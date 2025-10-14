import streamlit as st

from langchain.document_loaders import PyPDFLoader
from main_logic import get_response
import json
import tempfile


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