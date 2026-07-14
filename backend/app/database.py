import sqlite3
import json
from contextlib import contextmanager
from app.config import DATABASE_PATH


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                raw_text TEXT,
                extracted_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                content_hash TEXT UNIQUE,
                raw_text TEXT,
                extracted_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                resume_id INTEGER,
                score REAL,
                matched_skills TEXT,
                missing_skills TEXT,
                justification TEXT,
                shortlisted INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(job_id) REFERENCES jobs(id),
                FOREIGN KEY(resume_id) REFERENCES resumes(id)
                UNIQUE(job_id, resume_id)
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_job(title: str, raw_text: str, extracted: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (title, raw_text, extracted_json) VALUES (?, ?, ?)",
            (title, raw_text, json.dumps(extracted)),
        )
        conn.commit()
        return cur.lastrowid


def save_resume(filename: str, raw_text: str, extracted: dict, content_hash: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO resumes (filename, content_hash, raw_text, extracted_json) VALUES (?, ?, ?, ?)",
            (filename, content_hash, raw_text, json.dumps(extracted)),
        )
        conn.commit()
        return cur.lastrowid


def get_resume_by_hash(content_hash: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM resumes WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        return dict(row) if row else None


def save_score(job_id: int, resume_id: int, score: float, matched: list,
               missing: list, justification: str, shortlisted: bool):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO scores
               (job_id, resume_id, score, matched_skills, missing_skills, justification, shortlisted)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (job_id, resume_id, score, json.dumps(matched), json.dumps(missing),
             justification, int(shortlisted)),
        )
        conn.commit()


def get_resume(resume_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
        return dict(row) if row else None


def get_job(job_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None


def get_all_resumes():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM resumes ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_scores_for_job(job_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scores WHERE job_id = ? ORDER BY score DESC", (job_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    
def reset_db():
    with get_conn() as conn:
        conn.execute("DROP TABLE IF EXISTS scores")
        conn.execute("DROP TABLE IF EXISTS resumes")
        conn.execute("DROP TABLE IF EXISTS jobs")
        conn.commit()
