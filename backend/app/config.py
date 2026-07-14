import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EXTRACTION_MODEL = os.getenv("OLLAMA_EXTRACTION_MODEL", "gemma2:2b")
OLLAMA_SCORING_MODEL = os.getenv("OLLAMA_SCORING_MODEL", "gemma2:2b")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_HOST = os.getenv("GROQ_HOST", "https://api.groq.com/openai/v1")
GROQ_EXTRACTION_MODEL = os.getenv("GROQ_EXTRACTION_MODEL", "llama-3.1-8b-instant")
GROQ_SCORING_MODEL = os.getenv("GROQ_SCORING_MODEL", "llama-3.1-8b-instant")

SHORTLIST_THRESHOLD = float(os.getenv("SHORTLIST_THRESHOLD", "70"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "./resume_screener.db")