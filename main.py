import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
import json
import tempfile
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import os
import requests
import re

# --------------------- LLM Loader ---------------------
def load_llm(temperature: float = 0.5, max_tokens: int = 1024):
    load_dotenv()
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    os.environ['GROQ_API_KEY'] = GROQ_API_KEY
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=temperature,
        max_tokens=max_tokens
    )

# --------------------- AI Analysis ---------------------
system_prompt = """
You are an **AI Career Advisor and Resume Analyzer** designed to give *precise, structured, and actionable* feedback.

🎯 **Objective:**
You will be provided two inputs:
1. **Job Description (JD)** – with role title, required skills, and responsibilities.
2. **Candidate Resume** – with education, skills, projects, certifications, and experience.

Your task is to:
- Parse both documents carefully.
- Compare the resume content against the JD requirements in detail.
- Output a structured JSON report with: match score, missing skills, partially covered skills, recommendations, feedback, recommended courses, and recommended jobs.

---

📌 **Output Format (STRICT JSON ONLY):**

{{
  "match_score": 72,
  "missing_skills": ["Kubernetes", "AWS Lambda"],
  "partially_covered_skills": ["Azure Functions"],
  "recommendations": [
    "Highlight cloud-native experience with AWS",
    "Add certification in Kubernetes or Docker",
    "Emphasize leadership experience in DevOps projects"
  ],
  "feedback": "Solid backend expertise but resume lacks emphasis on cloud-native and container orchestration.",
  "recommended_courses": [
    {{"title": "AWS Developer Associate", "platform": "Coursera", "link": "https://www.coursera.org/learn/aws-developer"}},
    {{"title": "Kubernetes for Beginners", "platform": "Udemy", "link": "https://www.udemy.com/course/learn-kubernetes/"}}
  ],
  "recommended_jobs": [
    {{"title": "Cloud Engineer", "company": "Infosys", "relevance": "High"}},
    {{"title": "DevOps Associate", "company": "TCS", "relevance": "Medium"}}
  ]
}}
---

📌 **Instructions:**
1. **Match Score (0–100)** – deduct based on missing or partial skills.
2. **Missing Skills** – skills explicitly in JD but absent in resume.
3. **Partially Covered Skills** – related but not exact matches.
4. **Recommendations** – actionable edits, skill improvements, certifications.
5. **Feedback** – concise 2–4 sentence summary.
6. **Recommended Courses** – realistic titles, platforms, and links (Coursera, Udemy, edX).
7. **Recommended Jobs** – job titles + companies relevant to skill gaps.
---

📌 **Context to Analyze:**
Job_Description:
{job_description}

Candidate_Resume:
{candidate_resume}
"""

def get_response(resume, jd, temperature, max_tokens):
    llm = load_llm(temperature, max_tokens)
    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["job_description", "candidate_resume"]
    )
    chain = prompt | llm
    raw_response = chain.invoke({"job_description": jd, "candidate_resume": resume})

    # --- Manual JSON extraction ---
    match = re.search(r'\{.*\}', raw_response.content, re.DOTALL)
    if match:
        try:
            response = json.loads(match.group())
        except Exception:
            response = {}
    else:
        response = {}
    return response

# --------------------- Course Recommendations ---------------------
# --------------------- LLM-based Course Recommendations ---------------------
def get_course_recommendations_llm(missing_skills, temperature=0.5, max_tokens=512):
    if not missing_skills:
        return []

    llm = load_llm(temperature, max_tokens)
    skills_text = ", ".join(missing_skills[:5])  # Top 5 skills

    prompt = f"""
You are an AI Career Advisor. Based on the following skill set: {skills_text}, search and provide up to 5 real, currently available online courses from Coursera and Udemy that best match these skills. 

Each course must:
- Be relevant to the given skills.
- Exist on Coursera or Udemy (only include valid, working links).
- Be unique (no duplicates or expired courses).

Output strictly in JSON format like this:
[
  {"title": "Machine Learning by Andrew Ng", "platform": "Coursera", "link": "https://www.coursera.org/learn/machine-learning"},
  {"title": "Python for Data Science and Machine Learning Bootcamp", "platform": "Udemy", "link": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"}
]

Do not include any text outside the JSON array.
"""

    # Call LLM directly without PromptTemplate
    raw_response = llm.invoke(prompt)

    # --- Extract JSON safely ---
    import re, json
    match = re.search(r'\[.*\]', raw_response.content, re.DOTALL)
    if match:
        try:
            courses = json.loads(match.group())
        except Exception:
            courses = []
    else:
        courses = []

    return courses



# --------------------- Job Recommendations (India Only) ---------------------
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
os.environ["RAPIDAPI_KEY"] = RAPIDAPI_KEY

def get_job_recommendations(missing_skills):
    jobs = []
    if not missing_skills:
        return jobs
    try:
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": " ".join(missing_skills[:3]),
            "page": "1",
            "num_pages": "1",
            "country": "IN",
            "date_posted": "all"
        }
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        res = requests.get(url, headers=headers, params=querystring)
        data = res.json()

        for job in data.get("data", []):
            jobs.append({
                "title": job.get("job_title", "Unknown Role"),
                "company": job.get("employer_name", "Unknown Company"),
                "link": job.get("job_apply_link", "")
            })

    except Exception as e:
        print("Job API error:", e)
    return jobs

# --------------------- AI Career Chatbot ---------------------
def career_chatbot(message):
    llm = load_llm(temperature=0.7, max_tokens=1024)
    prompt = PromptTemplate(
        input_variables=["message"],
        template="""
        You are an experienced AI Career Mentor.
        Give concise, friendly advice in 3–5 sentences.
        User: {message}
        """
    )
    chain = prompt | llm
    response = chain.invoke({"message": message})
    return response.content

# --------------------- Helper Functions ---------------------
def convert_into_dict(result):
    if isinstance(result, str):
        return json.loads(result)
    return result

def render_report(result):
    report = convert_into_dict(result)

    st.subheader("Match Score")
    score = int(report.get("match_score", 0))
    st.metric("Match Score", f"{score}/100")
    st.progress(max(0, min(score, 100)))

    st.subheader("Missing Skills")
    missing_skills = report.get("missing_skills", [])
    if missing_skills:
        for s in missing_skills:
            st.write(f"- {s}")

    st.subheader("Partially Covered Skills")
    partially_covered_skills = report.get("partially_covered_skills", [])
    if partially_covered_skills:
        for s in partially_covered_skills:
            st.write(f"- {s}")
    else:
        st.write("None")

    st.subheader("Recommendations")
    recommendations = report.get("recommendations", [])
    if recommendations:
        for r in recommendations:
            st.write(f"- {r}")

    st.subheader("Feedback")
    st.write(report.get("feedback", "No feedback provided."))

    # Course Recommendations
    st.subheader("📚 Course Recommendations")
    courses = get_course_recommendations_llm(missing_skills, temperature=0.5, max_tokens=512)
    if courses:
        for c in courses:
            st.write(f"- [{c['title']}]({c['link']}) on {c['platform']}")
    else:
        st.write("No course recommendations available.")

    # Job Recommendations
    st.subheader("💼 Job Recommendations")
    jobs = get_job_recommendations(missing_skills)
    if jobs:
        for j in jobs:
            st.write(f"- [{j['title']}]({j['link']}) at {j['company']}")
    else:
        st.write("No job recommendations available.")

    with st.expander("View Full JSON Report", expanded=False):
        st.json(report)

    st.download_button(
        "Download JSON Report",
        data=json.dumps(report),
        file_name="report.json",
        mime="application/json",
        use_container_width=True
    )

# --------------------- Streamlit UI ---------------------
st.set_page_config(page_title="AI Career Advisor", page_icon=":guardsman:", layout="wide")
st.title("🧠 SkillSync")
st.caption("Compare a candidate's Resume against a Job Description and get a structured skill-gap JSON report.")

with st.sidebar:
    st.header("Settings")
    st.markdown("Adjust the parameters for the AI model.")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.5)
    max_tokens = st.slider("Max Tokens", 100, 2000, 1024)
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

jd = st.text_area("Job Description", placeholder="Paste the job description here...", width=800, height=300)

tab1, tab2 = st.tabs(["📊 Resume Analyzer", "💬 Career Chatbot"])

with tab1:
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            pdf_loader = PyPDFLoader(temp_file.name)
            pages = pdf_loader.load()
            resume = "\n".join([p.page_content for p in pages])
    else:
        resume = ""

    if st.button('Analyze'):
        with st.spinner("Analyzing..."):
            if resume and jd:
                response = get_response(resume, jd, temperature, max_tokens)
                render_report(response)
            else:
                st.error("Please upload a resume and provide a job description.")

with tab2:
    st.subheader("💬 AI Career Chatbot")
    user_input = st.text_input("Ask your career or skill question here...")
    if st.button("Send Message"):
        if user_input:
            with st.spinner("AI thinking..."):
                answer = career_chatbot(user_input)
                st.markdown(f"**🤖 Career Mentor:** {answer}")
        else:
            st.info("Type a question and click 'Send Message'.")
