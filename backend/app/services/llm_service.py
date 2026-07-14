import json
import re
from datetime import datetime
import requests
from dateutil import parser as date_parser
from fastapi import HTTPException
from app.config import OLLAMA_HOST, OLLAMA_EXTRACTION_MODEL, OLLAMA_SCORING_MODEL

RESUME_EXTRACTION_PROMPT = """You are a resume parsing engine. Extract structured information from the resume text below.

Return ONLY a valid JSON object (no markdown fences, no commentary) with exactly this shape:
{{
  "name": string or null,
  "email": string or null,
  "phone": string or null,
  "skills": [list of technical/soft skills mentioned, deduplicated, as short strings],
  "experience_entries": [list of PAID internships/jobs only — do NOT include student clubs,
    volunteer roles, or education — each as {{"role": string, "start_date": "Mon YYYY" format
    e.g. 'Dec 2025', "end_date": "Mon YYYY" format or 'Present' if ongoing}}],
  "total_experience_years": number (your best estimate as a fallback; this will be
    recalculated from experience_entries dates when possible, so accuracy here matters
    less than getting experience_entries right),
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

Already-confirmed matched skills: {matched_skills}
Skills not found in resume: {missing_skills}
Experience requirement: {experience_status} (candidate has {candidate_experience} years, job requires {min_experience} years)

For each missing skill, first decide if it is reasonably implied by the candidate's confirmed skills and experience. Then produce a score and justification.

Return ONLY a valid JSON object (no markdown fences, no commentary):
{{
  "inferred_skills": ["skill1", "skill2"],
  "score": number (0-100),
  "justification": "2-3 sentences for a hiring manager"
}}

JSON:"""


# For skills the deterministic matcher couldn't find literally, we ask the
# LLM ONE follow-up question: is this specific gap reasonably implied by what
# the candidate actually has (e.g. Java experience implies basic OOP)? This
# is a narrow yes/no/reason judgment per skill, not a re-derivation of the
# whole match — which keeps it far less prone to hallucination than asking
# the LLM to reconstruct matched/missing from scratch.
INFERENCE_PROMPT = """You are an expert technical recruiter assessing implied skills.

The candidate's resume lists these skills: {candidate_skills}
Their job titles: {candidate_titles}
Their total experience: {candidate_experience} years

The following required/preferred job skills were NOT explicitly listed in their resume:
{missing_skills}

For each missing skill, decide if it is REASONABLY implied by the candidate's actual
listed skills and experience (e.g. someone listing Java and C++ can reasonably be
assumed to understand basic OOP concepts, since OOP is fundamental to both languages).
Do NOT assume skills that require distinct, separate knowledge — e.g. knowing Python
does NOT imply knowing SQL, and experience with one database does NOT imply knowing a
different specific database product.

Return ONLY a valid JSON array (no markdown fences, no commentary), one object per
missing skill, in exactly this shape:
[
  {{"skill": "the exact skill name as given", "implied": true or false, "reason": "one short sentence"}}
]

Missing skills to assess: {missing_skills}

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


def _parse_month_year(value: str):
    """Parse strings like 'Dec 2025', 'February 2026', or 'Present'/'Current'
    into a datetime. Returns None if it can't be parsed — callers must
    handle that by skipping the entry, never guessing."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower() in ("present", "current", "now", "ongoing", "till date"):
        return datetime.today()
    try:
        # default day=1 avoids dateutil guessing today's day-of-month
        return date_parser.parse(value, default=datetime(1900, 1, 1))
    except (ValueError, OverflowError):
        return None


def _compute_experience_years(experience_entries) -> float | None:
    """Sum durations from explicit start/end dates. Returns None (not 0) if
    no entries were parseable at all, so callers can fall back to the LLM's
    own estimate rather than wrongly zeroing out real experience due to a
    date format we didn't recognize."""
    if not experience_entries:
        return None

    total_months = 0
    parsed_any = False
    for entry in experience_entries:
        if not isinstance(entry, dict):
            continue
        start = _parse_month_year(entry.get("start_date", ""))
        end = _parse_month_year(entry.get("end_date", ""))
        if not start or not end:
            continue
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if months > 0:
            total_months += months
            parsed_any = True

    if not parsed_any:
        return None
    return round(total_months / 12, 2)


def extract_resume_fields(text: str) -> dict:
    prompt = RESUME_EXTRACTION_PROMPT.format(text=text[:8000])
    raw = _call_ollama(prompt, model=OLLAMA_EXTRACTION_MODEL)
    data = _parse_json_response(raw)
    data["raw_text"] = text

    # Prefer a deterministic experience calculation over the LLM's own
    # total_experience_years figure — small local models have repeatedly
    # proven unreliable at this kind of arithmetic (e.g. estimating "2
    # years" from a resume with a single 3-month internship). If we got
    # parseable date ranges, recompute from those instead of trusting the
    # model's own guess.
    computed_years = _compute_experience_years(data.get("experience_entries"))
    if computed_years is not None:
        data["total_experience_years"] = computed_years

    return data


def extract_jd_fields(text: str) -> dict:
    prompt = JD_EXTRACTION_PROMPT.format(text=text[:8000])
    raw = _call_ollama(prompt, model=OLLAMA_EXTRACTION_MODEL)
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


def _parse_json_array_response(raw: str) -> list:
    """Same cleanup as _parse_json_response but for a JSON array instead of
    an object. Returns [] on any failure rather than raising — this
    inference step is an enhancement, not critical path, so a failure here
    should never break scoring."""
    try:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        result = json.loads(cleaned)
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"[infer_implied_skills] failed to parse LLM response: {e}\nRaw: {raw[:200]}")
        return []


def infer_implied_skills(missing_skills: list, resume_data: dict) -> list:
    """Ask the LLM, in one call, which of the still-missing skills are
    reasonably implied by the candidate's actual background. Returns a list
    of {"skill": ..., "reason": ...} for skills judged as implied."""
    if not missing_skills:
        return []

    prompt = INFERENCE_PROMPT.format(
        candidate_skills=", ".join(resume_data.get("skills", []) or []) or "none listed",
        candidate_titles=", ".join(resume_data.get("job_titles", []) or []) or "none listed",
        candidate_experience=resume_data.get("total_experience_years", 0) or 0,
        missing_skills=", ".join(missing_skills),
    )

    try:
        raw = _call_ollama(prompt, model=OLLAMA_SCORING_MODEL)
    except HTTPException:
        return []  # if Ollama is briefly unreachable, degrade gracefully

    parsed = _parse_json_array_response(raw)

    # match LLM's returned skill strings back to our original list by
    # normalized comparison, since the model may reword slightly
    missing_lookup = {_normalize(s): s for s in missing_skills}
    inferred = []
    for item in parsed:
        if not isinstance(item, dict) or not item.get("implied"):
            continue
        skill_norm = _normalize(str(item.get("skill", "")))
        if skill_norm in missing_lookup:
            inferred.append({"skill": missing_lookup[skill_norm], "reason": item.get("reason", "")})

    return inferred


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

    raw = _call_ollama(prompt, model=OLLAMA_SCORING_MODEL)
    llm_result = _parse_json_response(raw)

   # llama3.2 occasionally nests the whole result under a "score" key
    if "score" in llm_result and isinstance(llm_result["score"], dict):
        llm_result = llm_result["score"]

    inferred = llm_result.get("inferred_skills", [])
    inferred_set = {_normalize(s) for s in inferred}

    final_matched = match["matched_skills"] + [f"{s} (inferred)" for s in inferred if _normalize(s) in {_normalize(m) for m in match["missing_skills"]}]
    final_missing = [s for s in match["missing_skills"] if _normalize(s) not in inferred_set]

    return {
        "score": float(llm_result.get("score", 0) or 0),
        "matched_skills": final_matched,
        "missing_skills": final_missing,
        "justification": llm_result.get("justification", ""),
    }