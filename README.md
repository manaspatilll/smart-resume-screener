# Smart Resume Screener

An AI-powered recruitment tool that extracts structured data from resumes and job descriptions, computes a deterministic skill match, then uses an LLM to produce a 0–100 match score with a human-readable justification — shortlisting the best candidates automatically.

## How it works

1. **Ingest** — Upload a job description (paste text or upload PDF/DOCX/TXT) and one or more candidate resumes (PDF/DOCX/TXT).
2. **Extract** — Raw text is parsed in Python using regex and keyword matching against a curated skill taxonomy. No LLM involved — same approach used by real-world ATS systems (Workday, Greenhouse).
3. **Match** — Candidate skills are compared against JD requirements using deterministic whole-word token matching in Python — `"Core Java"` matches `"Java"` but `"Java"` never false-matches `"JavaScript"`.
4. **Score** — Groq (`llama-3.1-8b-instant`) receives the confirmed matched/missing skills, experience status, and education context, and produces a 0–100 score with a written justification grounded in those facts. It also infers implied skills (e.g. OOP from Java experience) in the same call.
5. **Shortlist** — Candidates above a configurable score threshold are flagged; the full list is displayed ranked by score.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLite |
| Resume/JD Parsing | Python (regex + keyword taxonomy) |
| File Parsing | pdfplumber (PDF), python-docx (DOCX) |
| LLM | Groq API (`llama-3.1-8b-instant`) — scoring + inference only |
| Frontend | React + Vite, axios |

## Architecture

```
┌─────────────┐     upload JD/resumes      ┌──────────────┐
│   React UI  │ ─────────────────────────▶ │   FastAPI    │
│  (Vite)     │ ◀───────────────────────── │   backend    │
└─────────────┘     scores + justification └──────┬───────┘
                                                    │
                   ┌────────────────────────────────┼──────────────────────┐
                   ▼                                ▼                      ▼
            pdfplumber /                  Python extraction            SQLite
            python-docx                  (regex + skill taxonomy)     (jobs,
            text extraction              - skills, experience,        resumes,
                                         education, job titles        scores)
                                                    │
                                                    ▼
                                         Python skill matcher
                                         (deterministic, whole-word
                                         token comparison)
                                                    │
                                                    ▼
                                         Groq LLM (1 call/resume)
                                         - infer implied skills
                                         - produce score + justification
```


## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free Groq API key — get one at [console.groq.com/keys](https://console.groq.com/keys)

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
App available at `http://localhost:5173`.

### `.env` reference
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...your_key_here...
SHORTLIST_THRESHOLD=70
DATABASE_PATH=./resume_screener.db
```

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/jobs` | POST | Create a job description (file or text), returns extracted structured JD |
| `/resumes/batch` | POST | Upload multiple resumes, returns extracted structured data for each |
| `/screening/run` | POST | Score all (or selected) resumes against a job |
| `/screening/results/{job_id}` | GET | Retrieve previously computed results for a job |

## Project Structure

```
smart-resume-screener/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                # env-based configuration
│   │   ├── models.py                # Pydantic schemas
│   │   ├── database.py              # SQLite persistence layer
│   │   ├── services/
│   │   │   ├── file_parser.py       # PDF/DOCX/TXT text extraction
│   │   │   ├── extraction.py        # Python resume/JD field extraction
│   │   │   └── llm_service.py       # Groq scoring + deterministic skill matching
│   │   └── routers/
│   │       ├── jobs.py
│   │       ├── resumes.py
│   │       └── screening.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/
            ├── UploadJD.jsx
            ├── UploadResumes.jsx
            └── ResultsTable.jsx
```

## Possible Extensions
- Add embedding-based semantic skill matching to catch implied skills beyond what the LLM inference step covers
- Add CSV/PDF export of screening results
- Add authentication for multi-recruiter use
