# Smart Resume Screener

An AI-powered recruitment tool that extracts structured data from resumes and job descriptions, then computes a match score with a human-readable justification — shortlisting the best candidates automatically. Built with a **local LLM** (via Ollama), so it runs entirely offline with zero API cost.

## How it works

1. **Ingest** — Upload a job description (paste text or upload PDF/DOCX/TXT) and one or more candidate resumes (PDF/DOCX/TXT).
2. **Extract** — Each document's raw text is passed to a local LLM (Ollama, `llama3.2`) which returns structured JSON: skills, experience, education, job titles for resumes; required/preferred skills, minimum experience, and education requirements for job descriptions.
3. **Match** — Candidate skills are compared against job requirements using deterministic, whole-word token matching in Python (not the LLM) — see [Design Decisions](#design-decisions) for why.
4. **Score** — The LLM takes the confirmed matched/missing skills plus experience and education context, and produces a 0–100 match score with a written justification, grounded in those facts.
5. **Shortlist** — Candidates above a configurable score threshold are flagged and the full list is displayed ranked by score.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLite |
| Resume/JD Parsing | pdfplumber (PDF), python-docx (DOCX) |
| LLM | Ollama (local, `llama3.2`) — no API key, no cost |
| Frontend | React + Vite, axios |

## Architecture

```
┌─────────────┐     upload JD/resumes      ┌──────────────┐
│   React UI  │ ─────────────────────────▶ │   FastAPI    │
│  (Vite)     │ ◀───────────────────────── │   backend    │
└─────────────┘     scores + justification └──────┬───────┘
                                                    │
                        ┌───────────────────────────┼───────────────────────┐
                        ▼                            ▼                       ▼
                 pdfplumber/                  Ollama (local LLM)          SQLite
                 python-docx                  - extract structured        (jobs,
                 text extraction              data from raw text          resumes,
                                               - score + justify           scores)
                                               (given pre-computed
                                               matched/missing skills)
                                                    ▲
                                                    │
                                          Python skill matcher
                                          (deterministic, whole-word
                                          token comparison — computes
                                          matched_skills/missing_skills,
                                          NOT the LLM)
```

## Design Decisions

**Why is skill matching done in Python, not the LLM, if this is an "LLM match scorer"?**
The LLM still computes the match score — that's the core requirement, and it's fully LLM-driven, reasoning over experience, education, and skill coverage to produce the 0–100 score and justification. What's *not* LLM-driven is the supporting fact: "does the candidate have skill X or not." Small local models (`llama3.2` is 3B parameters) are unreliable at exact set comparison — in testing, it occasionally claimed a candidate was "missing" a skill that was clearly present in their profile. Rather than let the score be built on a hallucinated foundation, matched/missing skills are computed deterministically in Python (whole-word token overlap, so "Core Java" matches "Java" but "Java" doesn't false-match "JavaScript"), and the LLM is given those confirmed facts to reason over for the score and justification. This is the same division of labor a real recruiter uses: check the requirements list mechanically, then apply judgment on top.

**Known limitation:** matching is literal — it checks whether a skill is explicitly listed in the resume's extracted skills array, not whether it's reasonably implied (e.g. a resume that lists "Java" but not "OOP" won't get credit for OOP, even though OOP is implicit to Java experience). This trades recall for precision and explainability.

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) installed locally

### 1. Install and start Ollama
```bash
ollama pull llama3.2
ollama serve
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
App available at `http://localhost:5173`.

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
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── config.py            # env-based configuration
│   │   ├── models.py            # Pydantic schemas
│   │   ├── database.py          # SQLite persistence layer
│   │   ├── services/
│   │   │   ├── file_parser.py   # PDF/DOCX/TXT text extraction
│   │   │   └── llm_service.py   # Ollama prompts + deterministic skill matching
│   │   └── routers/
│   │       ├── jobs.py
│   │       ├── resumes.py
│   │       └── screening.py
│   └── requirements.txt
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
- Swap Ollama for a hosted API (OpenAI/Anthropic) via a single flag in `llm_service.py`
- Add authentication for multi-recruiter use
- Add CSV/PDF export of screening results
- Add embedding-based semantic skill matching (to catch implied skills like OOP-from-Java) as a middle ground between literal matching and full LLM inference
