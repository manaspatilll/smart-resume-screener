import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SHORTLIST_THRESHOLD = int(os.getenv("SHORTLIST_THRESHOLD", "70"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "./resume_screener.db")
