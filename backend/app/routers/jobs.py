from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, Union
from app.services.file_parser import extract_text_from_upload
from app.services import llm_service
from app import database as db
from app.models import JobCreateResponse, ExtractedJD

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse)
async def create_job(
    file: Union[UploadFile, str, None] = File(None),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
):
    """Create a job description either from an uploaded file (PDF/DOCX/TXT) or raw pasted text."""
    # Swagger UI (and some HTML forms) send an empty string "" for an unset
    # optional file field instead of omitting it — normalize that to None.
    if isinstance(file, str) or not getattr(file, "filename", None):
        file = None

    if not file and not text:
        raise HTTPException(status_code=400, detail="Provide either a file or text for the job description.")

    if file:
        content = await file.read()
        raw_text = extract_text_from_upload(file, content)
    else:
        raw_text = text

    extracted = llm_service.extract_jd_fields(raw_text)
    job_id = db.save_job(title or extracted.get("title") or "Untitled Role", raw_text, extracted)

    return JobCreateResponse(job_id=job_id, extracted=ExtractedJD(**extracted))


@router.get("/{job_id}")
def get_job(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job