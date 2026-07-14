import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Both extraction and scoring currently use the same model. We tried
# splitting extraction to a smaller llama3.2:1b for speed, but it proved
# unreliable — it failed to extract even trivial fields (name, email, and
# the resume's own Technical Skills section) on real test data. Correctness
# matters more than speed for a tool whose entire job is accurate
# extraction, so both stay on the 3B model for now.
OLLAMA_EXTRACTION_MODEL = os.getenv("OLLAMA_EXTRACTION_MODEL", "gemma2:2b")
OLLAMA_SCORING_MODEL = os.getenv("OLLAMA_SCORING_MODEL", "gemma2:2b")

SHORTLIST_THRESHOLD = float(os.getenv("SHORTLIST_THRESHOLD", "70"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "./resume_screener.db")