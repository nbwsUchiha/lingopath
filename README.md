# LingoPath - Multilingual Learning Path Generator

An end-to-end app that builds adaptive, multilingual study plans from open MOOC catalogs, generates quizzes, tracks learner progress, and syncs plans to Google Classroom. Backend is FastAPI; frontend is Streamlit; LLM is Groq via LangChain; optional translation via DeepL.

## Features
- Plan generation in multiple languages using Groq (LangChain)
- Course search from Coursera/edX (public catalog + sensible fallbacks)
- Quiz generation for any topic
- Progress tracking (in-memory local store)
- Google Classroom integration
  - Create or reuse a course
  - Create assignments from plan modules
  - Invite students by email and fetch enrollment code
  - Optional Meet URL included in assignment descriptions

## Tech Stack
- Backend: FastAPI (Uvicorn) @[LingoPath - HuggingFace](https://nbws-lingopath.hf.space/docs)
- Frontend: Streamlit @[LingoPath](https://lingopath.streamlit.app/)
- LLM: LangChain + Groq
- Translation: DeepL (optional)
- Google Classroom: google-api-python-client
- Packaging: Docker (for deployment)

## Repository Structure
```
.
├─ backend/
│  └─ app/
│     ├─ main.py                 # FastAPI app, routers wiring
│     ├─ config.py               # Settings from environment
│     ├─ api/
│     │  ├─ health.py            # GET /health
│     │  └─ routes.py            # /api: courses, plan, quiz, progress, classroom
│     ├─ models/
│     │  └─ schemas.py           # Pydantic models
│     └─ services/
│        ├─ llm.py               # Groq LLM via LangChain
│        ├─ mooc_providers.py    # Coursera/edX search wrappers with fallbacks
│        ├─ planner.py           # Build plan from goals + language
│        ├─ progress.py          # In-memory progress store
│        ├─ translator.py        # DeepL translator (optional)
│        └─ classroom.py         # Google Classroom integration
├─ frontend/
│  └─ streamlit_app.py          # Streamlit UI
├─ scripts/
│  └─ start.sh                  # Local dual run or HF backend-only mode
├─ requirements.txt
├─ Dockerfile                   # Combined image for FastAPI + Streamlit
├─ .env.example                 # Template for environment variables
└─ README.md
```

## Environment Variables
Copy `.env.example` to `.env` and fill in values.

Core
- APP_NAME: Multilingual Learning Path Generator
- ENVIRONMENT: local
- API_HOST: 0.0.0.0
- API_PORT: 8000
- STREAMLIT_PORT: 8501
- API_URL: http://localhost:8000

LLM (Groq)
- GROQ_API_KEY: your Groq key (required for LLM features)
- GROQ_MODEL: default `llama3-70b-8192`

Translation (optional)
- DEEPL_API_KEY: DeepL API key

Google Classroom (optional)
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REFRESH_TOKEN

Database (not used by default; progress is in-memory)
- SQLITE_URL: sqlite:///./data.db

## Local Development

### Prerequisites
- Python 3.11
- PowerShell (Windows) or bash (Linux/macOS)

### Setup and Install
Windows PowerShell:
```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

### Run Backend and Frontend
Run servers in separate terminals (recommended for Windows):

Terminal 1 (FastAPI):
```powershell
& .\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --http h11
```

Terminal 2 (Streamlit):
```powershell
& .\.venv\Scripts\Activate.ps1
$env:API_URL='http://127.0.0.1:8000'
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 127.0.0.1
```

Linux/macOS (or WSL) dual-run script:
```bash
bash scripts/start.sh
```

### Test Locally
- Backend docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health/
- Frontend: http://127.0.0.1:8501

### API Endpoints (summary)
- GET `/health/`
- GET `/api/courses?query=python&language=en&limit=6`
- POST `/api/plan` → PlanRequest
- POST `/api/quiz` → QuizRequest
- POST `/api/progress/{user_id}` → ProgressUpdate[]
- GET `/api/progress/{user_id}`
- POST `/api/classroom/push` → create assignments from plan
  - Payload fields: `course_name`, `plan`, `meet_url` (optional)
- POST `/api/classroom/invite` → invite students by email
  - Payload fields: `course_name`, `emails: string[]`
- GET `/api/classroom/enrollment_code?course_name=...` → enrollment code

## Google Classroom Configuration
1) Google Cloud project setup
- Enable APIs: Google Classroom API
- Create OAuth 2.0 Client (Web application or Desktop)
- Configure OAuth consent screen with required info

2) Scopes required
- https://www.googleapis.com/auth/classroom.courses
- https://www.googleapis.com/auth/classroom.coursework.me
- https://www.googleapis.com/auth/classroom.coursework.students
- https://www.googleapis.com/auth/classroom.rosters

3) Obtain a refresh token
- Use OAuth 2.0 Playground or a one-time auth flow to obtain `refresh_token` for the teacher account owning the course
- Ensure the above scopes are authorized
- Place `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` in environment

4) Using Classroom features
- Generate a plan in Streamlit
- Provide a `Course Name`
- (Optional) provide a `Meet URL` to include in assignments
- Push plan to Classroom → creates assignments under that course
- Invite students: paste emails and send invites, or share the enrollment code

Notes
- Domain policies may restrict invites or API usage; ensure Classroom API is allowed in your Google Workspace
- The refresh token must belong to the teacher who owns the course

## Deployment

### Option A: Backend on Hugging Face Spaces (Docker), Frontend on Streamlit Community Cloud
Recommended for separation of concerns.

Hugging Face Spaces (Backend)
- Create a Space with SDK: Docker
- Use your repository with the included `Dockerfile`
- Set Space Secrets:
  - GROQ_API_KEY (required)
  - GROQ_MODEL (optional)
  - DEEPL_API_KEY (optional)
  - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN (optional)
  - RUN_MODE=backend_only
- The `scripts/start.sh` will bind FastAPI to `PORT` when `RUN_MODE=backend_only`
- Test after deploy: open `/docs` and `/health/`

Backend-only Dockerfile variant
If you deploy a repo that contains only the backend code, use this Dockerfile in that repo:
```Dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["bash", "-lc", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-7860} --http h11"]
```

Streamlit Community Cloud (Frontend)
- New app → connect to GitHub repository
- Main file: `frontend/streamlit_app.py`
- Python version: 3.11
- Dependencies: `requirements.txt` at repo root
- App Secrets:
  - API_URL = `https://<your-hf-space>.hf.space`
- Deploy and verify the sidebar “Backend URL” points to your Space

### Option B: Both in one Hugging Face Space
The provided `Dockerfile` runs both FastAPI and Streamlit locally. HF Spaces expose a single port. To run both there, either:
- Keep backend-only on HF and run Streamlit on Streamlit Cloud (Option A), or
- Adjust `scripts/start.sh` to bind Streamlit to `$PORT` and run uvicorn on an internal port. If you want this, update the script accordingly.

## Docker (Local)
Build:
```bash
docker build -t learning-path:latest .
```
Run:
```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env learning-path:latest
```

## Troubleshooting
- Port already in use
  - Use a different port or stop the existing process
- PowerShell web cmdlets error on health request
  - Use a browser or `curl http://127.0.0.1:8000/health/`
- Classroom 403 / domain restrictions
  - Ensure the teacher account owns the course and API is allowed by admin
- LLM errors
  - Confirm `GROQ_API_KEY` is set; free tier has rate limits
- Translation has no effect
  - Set `DEEPL_API_KEY`, otherwise titles pass through unchanged

## Roadmap
- Persistent database for progress and user profiles
- Richer provider integrations and filters
- More robust quiz formats and grading
- Auth for multi-user deployments

## License
Specify your license here.

## Acknowledgments
- FastAPI, Streamlit, LangChain, Groq
- Google Classroom API, DeepL API
