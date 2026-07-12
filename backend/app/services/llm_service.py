import json
import re
import requests
from fastapi import HTTPException
from app.config import OLLAMA_HOST, OLLAMA_MODEL

RESUME_EXTRACTION_PROMPT = """You are a resume parsing engine. Extract structured information from the resume text below.

Return ONLY a valid JSON object (no markdown fences, no commentary) with exactly this shape:
{{
  "name": string or null,
  "email": string or null,
  "phone": string or null,
  "skills": [list of technical/soft skills mentioned, deduplicated, as short strings],
  "total_experience_years": number (estimate total professional experience in years, 0 if fresher/student),
  "job_titles": [list of past job titles / internship roles held],
  "education": [{{"degree": string, "institution": string, "year": string}}]
}}

Resume text:
\"\"\"
{text}
\"\"\"

JSON:"""

JD_EXTRACTION_PROMPT = """You are a job description parsing engine. Extract structured requirements from the job description below.

Return ONLY a valid JSON object (no markdown fences, no commentary) with exactly this shape:
{{
  "title": string or null,
  "required_skills": [list of must-have skills/technologies],
  "preferred_skills": [list of nice-to-have skills/technologies],
  "min_experience_years": number (0 if not specified or entry-level),
  "education_requirement": string or null
}}

Job description text:
\"\"\"
{text}
\"\"\"

JSON:"""

# NOTE: matched_skills / missing_skills are NOT asked of the LLM anymore.
# Small local models are unreliable at exact set comparison (they occasionally
# hallucinate a skill as "missing" even when it's clearly present). Those two
# lists are now computed deterministically in Python (see compute_skill_match
# below) and passed in here as already-known facts. The LLM's job is narrowed
# to what it's actually good at: producing a defensible score and a natural
# language explanation grounded in those facts.
SCORING_PROMPT = """You are an expert technical recruiter writing a short match assessment.

Job requirements:
- Required skills: {required_skills}
- Preferred skills: {preferred_skills}
- Minimum experience required: {min_experience} years
- Education requirement: {education_requirement}

Candidate profile:
- Total experience: {candidate_experience} years
- Education: {candidate_education}
- Job titles held: {candidate_titles}

Already-confirmed facts (do not contradict these):
- Skills the candidate HAS that the job wants: {matched_skills}
- Skills the job wants that the candidate is MISSING: {missing_skills}

Based on all of the above, return ONLY a valid JSON object (no markdown fences, no commentary) with exactly this shape:
{{
  "score": number (0-100, weight required skills and experience heavily, preferred skills lightly),
  "justification": "2-4 sentences explaining the score for a hiring manager, referencing the matched/missing skills and experience fit above"
}}

JSON:"""


def _call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1024},
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not reach Ollama. Make sure it's running "
                f"(`ollama serve`) and the model `{OLLAMA_MODEL}` is pulled "
                f"(`ollama pull {OLLAMA_MODEL}`)."
            ),
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM request timed out.")


def _parse_json_response(raw: str) -> dict:
    """LLMs often wrap JSON in markdown fences or add stray text. Clean it up."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail=f"LLM returned malformed JSON. Raw output: {raw[:500]}",
        )


def extract_resume_fields(text: str) -> dict:
    prompt = RESUME_EXTRACTION_PROMPT.format(text=text[:8000])
    raw = _call_ollama(prompt)
    data = _parse_json_response(raw)
    data["raw_text"] = text
    return data


def extract_jd_fields(text: str) -> dict:
    prompt = JD_EXTRACTION_PROMPT.format(text=text[:8000])
    raw = _call_ollama(prompt)
    data = _parse_json_response(raw)
    data["raw_text"] = text
    return data


def _normalize(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip().lower())


def _tokenize(skill: str) -> set:
    """Split into whole-word tokens (letters/numbers/+/#/.) so 'C' doesn't
    accidentally match inside 'concepts', and 'Java' doesn't match inside
    'JavaScript'."""
    return set(re.findall(r"[a-z0-9\+\#\.]+", skill.lower()))


def _skill_present(jd_skill: str, candidate_skills: list) -> bool:
    """A JD skill counts as present if the full normalized strings match
    exactly, OR the two share a meaningful whole-word token (length > 2,
    to skip trivial single-letter overlaps)."""
    jd_norm = _normalize(jd_skill)
    jd_tokens = _tokenize(jd_skill)

    for cand in candidate_skills:
        if jd_norm == _normalize(cand):
            return True
        cand_tokens = _tokenize(cand)
        if any(len(t) > 2 for t in (jd_tokens & cand_tokens)):
            return True
    return False


def compute_skill_match(jd_data: dict, resume_data: dict) -> dict:
    """Deterministic (non-LLM) skill comparison. This is the source of truth
    for matched_skills / missing_skills — the LLM never invents these."""
    required = jd_data.get("required_skills", []) or []
    preferred = jd_data.get("preferred_skills", []) or []
    candidate_skills = resume_data.get("skills", []) or []

    matched_required = [s for s in required if _skill_present(s, candidate_skills)]
    missing_required = [s for s in required if not _skill_present(s, candidate_skills)]
    matched_preferred = [s for s in preferred if _skill_present(s, candidate_skills)]
    missing_preferred = [s for s in preferred if not _skill_present(s, candidate_skills)]

    return {
        "matched_skills": matched_required + matched_preferred,
        "missing_skills": missing_required + missing_preferred,
        "matched_required": matched_required,
        "missing_required": missing_required,
    }


def score_resume_against_jd(resume_data: dict, jd_data: dict) -> dict:
    match = compute_skill_match(jd_data, resume_data)

    prompt = SCORING_PROMPT.format(
        required_skills=", ".join(jd_data.get("required_skills", []) or []) or "none listed",
        preferred_skills=", ".join(jd_data.get("preferred_skills", []) or []) or "none listed",
        min_experience=jd_data.get("min_experience_years", 0) or 0,
        education_requirement=jd_data.get("education_requirement") or "not specified",
        candidate_experience=resume_data.get("total_experience_years", 0) or 0,
        candidate_education=json.dumps(resume_data.get("education", [])),
        candidate_titles=", ".join(resume_data.get("job_titles", []) or []) or "none listed",
        matched_skills=", ".join(match["matched_skills"]) or "none",
        missing_skills=", ".join(match["missing_skills"]) or "none",
    )
    raw = _call_ollama(prompt)
    llm_result = _parse_json_response(raw)

    return {
        "score": llm_result.get("score", 0),
        "matched_skills": match["matched_skills"],
        "missing_skills": match["missing_skills"],
        "justification": llm_result.get("justification", ""),
    }