import json
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services import llm_service
from app import database as db
from app.models import ScoreResult, ScreeningResponse
from app.config import SHORTLIST_THRESHOLD

router = APIRouter(prefix="/screening", tags=["screening"])


class ScreenRequest(BaseModel):
    job_id: int
    resume_ids: Optional[List[int]] = None  # if omitted, screens ALL resumes on file


@router.post("/run", response_model=ScreeningResponse)
def run_screening(req: ScreenRequest):
    job = db.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    jd_data = json.loads(job["extracted_json"])

    if req.resume_ids:
        resumes = [db.get_resume(rid) for rid in req.resume_ids]
        resumes = [r for r in resumes if r]
    else:
        resumes = db.get_all_resumes()

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes found to screen.")

    results = []
    for resume in resumes:
        resume_data = json.loads(resume["extracted_json"])
        score_data = llm_service.score_resume_against_jd(resume_data, jd_data)

        score = float(score_data.get("score", 0))
        matched = score_data.get("matched_skills", [])
        missing = score_data.get("missing_skills", [])
        justification = score_data.get("justification", "")
        shortlisted = score >= SHORTLIST_THRESHOLD

        db.save_score(req.job_id, resume["id"], score, matched, missing, justification, shortlisted)

        results.append(
            ScoreResult(
                resume_id=resume["id"],
                candidate_name=resume_data.get("name") or resume["filename"],
                score=score,
                matched_skills=matched,
                missing_skills=missing,
                justification=justification,
                shortlisted=shortlisted,
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return ScreeningResponse(job_id=req.job_id, results=results)


@router.get("/results/{job_id}", response_model=List[ScoreResult])
def get_results(job_id: int):
    rows = db.get_scores_for_job(job_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No screening results found for this job yet.")

    results = []
    for row in rows:
        resume = db.get_resume(row["resume_id"])
        resume_data = json.loads(resume["extracted_json"]) if resume else {}
        results.append(
            ScoreResult(
                resume_id=row["resume_id"],
                candidate_name=resume_data.get("name") or (resume["filename"] if resume else "Unknown"),
                score=row["score"],
                matched_skills=json.loads(row["matched_skills"]),
                missing_skills=json.loads(row["missing_skills"]),
                justification=row["justification"],
                shortlisted=bool(row["shortlisted"]),
            )
        )
    return results
