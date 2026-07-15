import json
import re
import requests
from fastapi import HTTPException
from app.config import (
    LLM_PROVIDER,
    OLLAMA_HOST,
    OLLAMA_SCORING_MODEL,
    GROQ_API_KEY,
    GROQ_HOST,
    GROQ_SCORING_MODEL,
)

_MODEL_BY_ROLE = {
    "ollama": {"scoring": OLLAMA_SCORING_MODEL},
    "groq": {"scoring": GROQ_SCORING_MODEL},
}

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

Already-confirmed matched skills: {matched_skills}
Skills not found in resume: {missing_skills}
Experience requirement: {experience_status} (candidate has {candidate_experience} years, job requires {min_experience} years)

For each missing skill, first decide if it is REASONABLY implied by the candidate's
confirmed skills and experience (e.g. someone listing Java and C++ can reasonably be
assumed to understand basic OOP concepts, since OOP is fundamental to both languages).
Do NOT assume skills that require distinct, separate knowledge — e.g. knowing Python
does NOT imply knowing SQL, and experience with one database does NOT imply knowing a
different specific database product. Then produce a score and justification.

Return ONLY a valid JSON object (no markdown fences, no commentary):
{{
  "inferred_skills": ["skill1", "skill2"],
  "score": number (0-100),
  "justification": "2-3 sentences for a hiring manager"
}}

JSON:"""


def _call_ollama(prompt: str, model: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "num_predict": 1024},
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not reach Ollama. Make sure it's running "
                f"(`ollama serve`) and the model `{model}` is pulled "
                f"(`ollama pull {model}`)."
            ),
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM request timed out.")


def _call_groq(prompt: str, model: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not set. Add it to backend/.env (get one at "
            "https://console.groq.com/keys), or set LLM_PROVIDER=ollama to use a local model.",
        )
    try:
        response = requests.post(
            f"{GROQ_HOST}/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Groq rejected the API key. Check GROQ_API_KEY in backend/.env.")
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Groq rate limit hit. Wait a moment and retry, or lower request volume.")
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Could not reach Groq API. Check your internet connection.")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Groq request timed out.")


def _call_llm(prompt: str, role: str) -> str:
    """Provider-agnostic entry point. `role` is currently always 'scoring' —
    resolved to the right model name for whichever provider is active."""
    model = _MODEL_BY_ROLE[LLM_PROVIDER][role]
    if LLM_PROVIDER == "groq":
        return _call_groq(prompt, model=model)
    return _call_ollama(prompt, model=model)


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

    candidate_experience = resume_data.get("total_experience_years", 0) or 0
    min_experience = jd_data.get("min_experience_years", 0) or 0
    experience_status = "MET" if candidate_experience >= min_experience else "NOT MET"

    prompt = SCORING_PROMPT.format(
        required_skills=", ".join(jd_data.get("required_skills", []) or []) or "none listed",
        preferred_skills=", ".join(jd_data.get("preferred_skills", []) or []) or "none listed",
        min_experience=min_experience,
        education_requirement=jd_data.get("education_requirement") or "not specified",
        candidate_experience=candidate_experience,
        candidate_education=json.dumps(resume_data.get("education", [])),
        candidate_titles=", ".join(resume_data.get("job_titles", []) or []) or "none listed",
        matched_skills=", ".join(match["matched_skills"]) or "none",
        missing_skills=", ".join(match["missing_skills"]) or "none",
        experience_status=experience_status,
    )

    raw = _call_llm(prompt, role="scoring")
    llm_result = _parse_json_response(raw)

    # some models occasionally nest the whole result under a "score" key
    if "score" in llm_result and isinstance(llm_result["score"], dict):
        llm_result = llm_result["score"]

    inferred = llm_result.get("inferred_skills", [])
    inferred_set = {_normalize(s) for s in inferred}

    final_matched = match["matched_skills"] + [
        f"{s} (inferred)" for s in inferred
        if _normalize(s) in {_normalize(m) for m in match["missing_skills"]}
    ]
    final_missing = [s for s in match["missing_skills"] if _normalize(s) not in inferred_set]

    return {
        "score": float(llm_result.get("score", 0) or 0),
        "matched_skills": final_matched,
        "missing_skills": final_missing,
        "justification": llm_result.get("justification", ""),
    }