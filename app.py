import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

API_URL = os.getenv("API_URL", "https://nbws-lingopath.hf.space/")

st.set_page_config(page_title="Learning Path Generator", layout="wide")

st.title("Multilingual Learning Path Generator")

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("Backend URL", value=API_URL)
    lang = st.selectbox("Preferred Language", ["en", "es", "fr", "de", "ar", "zh"], index=0)
    user_id = st.text_input("User ID", value="demo-user")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Search Courses")
    query = st.text_input("Query", value="python")
    if st.button("Search"):
        try:
            resp = requests.get(f"{api_url}/api/courses", params={"query": query, "language": lang, "limit": 6}, timeout=20)
            if resp.ok:
                data = resp.json()
                for item in data:
                    st.write(f"- [{item['title']}]({item['url']}) ({item['platform']})")
            else:
                st.error(resp.text)
        except Exception as exc:
            st.exception(exc)

with col2:
    st.subheader("Generate Plan")
    goals = st.text_area("Goals (comma-separated)", value="python fundamentals, data analysis").split(",")
    goals = [g.strip() for g in goals if g.strip()]
    weeks = st.slider("Duration (weeks)", 1, 24, 4)
    if st.button("Build Plan"):
        payload = {"goals": goals, "level": "beginner", "preferred_languages": [lang], "duration_weeks": weeks}
        try:
            resp = requests.post(f"{api_url}/api/plan", json=payload, timeout=60)
            if resp.ok:
                plan = resp.json()
                st.session_state["last_plan"] = plan
                st.success(plan.get("summary"))
                for m in plan.get("modules", []):
                    st.markdown(f"**{m['title']}**")
                    for r in m.get("resources", []):
                        st.write(f"- [{r['title']}]({r['url']}) ({r['platform']})")
            else:
                st.error(resp.text)
        except Exception as exc:
            st.exception(exc)

st.subheader("Quiz Generator")
quiz_topic = st.text_input("Topic", value="python basics")
num_q = st.slider("Number of Questions", 1, 10, 5)
if st.button("Generate Quiz"):
    payload = {"topic": quiz_topic, "num_questions": num_q, "language": lang}
    try:
        resp = requests.post(f"{api_url}/api/quiz", json=payload, timeout=60)
        if resp.ok:
            qz = resp.json()
            for i, q in enumerate(qz.get("questions", []), start=1):
                st.markdown(f"{i}. {q['question']}")
                for choice in q.get("choices", []):
                    st.write(f"- {choice['text']} {'(correct)' if choice.get('is_correct') else ''}")
        else:
            st.error(resp.text)
    except Exception as exc:
        st.exception(exc)

st.subheader("Progress")
item_id = st.text_input("Item ID", value="module-1")
status = st.selectbox("Status", ["not_started", "in_progress", "completed"], index=0)
if st.button("Update Progress"):
    updates = [{"item_id": item_id, "status": status, "metadata": {"notes": "via UI"}}]
    try:
        resp = requests.post(f"{api_url}/api/progress/{user_id}", json=updates, timeout=20)
        if resp.ok:
            st.success("Progress updated")
            st.json(resp.json())
        else:
            st.error(resp.text)
    except Exception as exc:
        st.exception(exc)

if st.button("Get Progress"):
    try:
        resp = requests.get(f"{api_url}/api/progress/{user_id}", timeout=20)
        if resp.ok:
            st.json(resp.json())
        else:
            st.error(resp.text)
    except Exception as exc:
        st.exception(exc)

st.subheader("Google Classroom")
course_name = st.text_input("Classroom Course Name", value="Learning Path")
if st.button("Push Plan to Classroom"):
    plan = st.session_state.get("last_plan")
    if not plan:
        st.warning("Please generate a plan first.")
    else:
        payload = {"course_name": course_name, "plan": {"goals": goals, "level": "beginner", "preferred_languages": [lang], "duration_weeks": weeks}}
        try:
            resp = requests.post(f"{api_url}/api/classroom/push", json=payload, timeout=60)
            if resp.ok:
                st.success("Pushed to Google Classroom")
                st.json(resp.json())
            else:
                st.error(resp.text)
        except Exception as exc:
            st.exception(exc)

st.divider()
st.caption("Health check below")
try:
    resp = requests.get(f"{api_url}/health/", timeout=10)
    st.write({"health": resp.json() if resp.ok else resp.text})
except Exception as exc:
    st.write({"health_error": str(exc)})

