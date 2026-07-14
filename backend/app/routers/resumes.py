import asyncio
import hashlib
import json
from fastapi import APIRouter, UploadFile, File
from typing import List
from app.services.file_parser import extract_text_from_upload
from app.services import extraction
from app import database as db
from app.models import ResumeUploadResponse, ExtractedResume

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def _process_single(file: UploadFile, content: bytes) -> ResumeUploadResponse:
    content_hash = _hash(content)
    existing = db.get_resume_by_hash(content_hash)
    if existing:
        extracted = json.loads(existing["extracted_json"])
        return ResumeUploadResponse(resume_id=existing["id"], extracted=ExtractedResume(**extracted))
    raw_text = extract_text_from_upload(file, content)
    extracted = extraction.extract_resume_fields(raw_text)
    resume_id = db.save_resume(file.filename, raw_text, extracted, content_hash)
    return ResumeUploadResponse(resume_id=resume_id, extracted=ExtractedResume(**extracted))


@router.post("", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    return await _process_single(file, content)


@router.post("/batch", response_model=List[ResumeUploadResponse])
async def upload_resumes_batch(files: List[UploadFile] = File(...)):
    contents = await asyncio.gather(*[f.read() for f in files])
    results = await asyncio.gather(*[
        _process_single(file, content)
        for file, content in zip(files, contents)
    ])
    return list(results)