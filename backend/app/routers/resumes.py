from fastapi import APIRouter, UploadFile, File
from typing import List
from app.services.file_parser import extract_text_from_upload
from app.services import llm_service
from app import database as db
from app.models import ResumeUploadResponse, ExtractedResume

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    raw_text = extract_text_from_upload(file, content)
    extracted = llm_service.extract_resume_fields(raw_text)
    resume_id = db.save_resume(file.filename, raw_text, extracted)
    return ResumeUploadResponse(resume_id=resume_id, extracted=ExtractedResume(**extracted))


@router.post("/batch", response_model=List[ResumeUploadResponse])
async def upload_resumes_batch(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        content = await file.read()
        raw_text = extract_text_from_upload(file, content)
        extracted = llm_service.extract_resume_fields(raw_text)
        resume_id = db.save_resume(file.filename, raw_text, extracted)
        results.append(ResumeUploadResponse(resume_id=resume_id, extracted=ExtractedResume(**extracted)))
    return results


@router.get("")
def list_resumes():
    return db.get_all_resumes()
