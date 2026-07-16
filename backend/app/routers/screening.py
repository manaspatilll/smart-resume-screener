import asyncio
import csv
import io
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
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
    shortlist_threshold: Optional[float] = None  # if omitted, uses SHORTLIST_THRESHOLD from config


@router.post("/run", response_model=ScreeningResponse)
async def run_screening(req: ScreenRequest):
    job = db.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    jd_data = json.loads(job["extracted_json"])

    threshold = req.shortlist_threshold if req.shortlist_threshold is not None else SHORTLIST_THRESHOLD
    if not (0 <= threshold <= 100):
        raise HTTPException(status_code=400, detail="shortlist_threshold must be between 0 and 100.")

    if req.resume_ids:
        resumes = [db.get_resume(rid) for rid in req.resume_ids]
        resumes = [r for r in resumes if r]
    else:
        resumes = db.get_all_resumes()

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes found to screen.")

    async def score_one(resume):
        resume_data = json.loads(resume["extracted_json"])
        try:
            score_data = await asyncio.wait_for(
                asyncio.to_thread(llm_service.score_resume_against_jd, resume_data, jd_data),
                timeout=290
            )
        except asyncio.TimeoutError:
            return ScoreResult(
                resume_id=resume["id"],
                candidate_name=resume_data.get("name") or resume["filename"],
                score=0,
                matched_skills=[],
                missing_skills=[],
                justification="Scoring timed out — LLM took too long for this resume.",
                shortlisted=False,
            )

        score = float(score_data.get("score", 0) or 0)
        matched = score_data.get("matched_skills", [])
        missing = score_data.get("missing_skills", [])
        justification = score_data.get("justification", "")
        shortlisted = score >= threshold

        db.save_score(req.job_id, resume["id"], score, matched, missing, justification, shortlisted)

        return ScoreResult(
            resume_id=resume["id"],
            candidate_name=resume_data.get("name") or resume["filename"],
            score=score,
            matched_skills=matched,
            missing_skills=missing,
            justification=justification,
            shortlisted=shortlisted,
        )

    results = list(await asyncio.gather(*[score_one(r) for r in resumes]))
    results.sort(key=lambda r: r.score, reverse=True)
    return ScreeningResponse(job_id=req.job_id, results=results, shortlist_threshold=threshold)


def _build_results_for_job(job_id: int) -> List[ScoreResult]:
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


@router.get("/results/{job_id}", response_model=List[ScoreResult])
def get_results(job_id: int):
    return _build_results_for_job(job_id)


@router.get("/export/{job_id}")
def export_results(job_id: int, format: str = Query("csv", pattern="^(csv|json)$")):
    """Download screening results for a job as CSV or JSON, ranked by score.
    Reuses the same result-building logic as /results/{job_id} so the
    exported file can never drift from what's shown in the UI."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = _build_results_for_job(job_id)
    job_title = json.loads(job["extracted_json"]).get("title") or f"job-{job_id}"
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_title)[:50]

    if format == "json":
        payload = json.dumps([r.model_dump() for r in results], indent=2)
        return StreamingResponse(
            io.BytesIO(payload.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_results.json"'},
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Candidate Name", "Score", "Shortlisted",
        "Matched Skills", "Missing Skills", "Justification",
    ])
    for r in results:
        writer.writerow([
            r.candidate_name,
            r.score,
            "Yes" if r.shortlisted else "No",
            "; ".join(r.matched_skills),
            "; ".join(r.missing_skills),
            r.justification,
        ])
    buffer.seek(0)
    return StreamingResponse(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}_results.csv"'},
    )