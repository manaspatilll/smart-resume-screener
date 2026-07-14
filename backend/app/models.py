from pydantic import BaseModel
from typing import List, Optional


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class ExtractedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    total_experience_years: Optional[float] = None
    job_titles: List[str] = []
    education: List[Education] = []
    raw_text: str = ""


class ExtractedJD(BaseModel):
    title: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    min_experience_years: Optional[float] = None
    education_requirement: Optional[str] = None
    raw_text: str = ""


class ScoreResult(BaseModel):
    resume_id: int
    candidate_name: Optional[str]
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    justification: str
    shortlisted: bool


class JobCreateResponse(BaseModel):
    job_id: int
    extracted: ExtractedJD


class ResumeUploadResponse(BaseModel):
    resume_id: int
    extracted: ExtractedResume


class ScreeningResponse(BaseModel):
    job_id: int
    results: List[ScoreResult]

class Job(BaseModel):
    id: int
    title: Optional[str]
    extracted: ExtractedJD
