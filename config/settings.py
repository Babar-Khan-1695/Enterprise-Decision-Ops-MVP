from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "sample"
FAISS_DIR = DATA_DIR / "faiss_index"
MEMORY_DIR = BASE_DIR / "memory"
OUTPUT_DIR = BASE_DIR / "outputs" / "reports"

for path in [UPLOAD_DIR, SAMPLE_DIR, FAISS_DIR, MEMORY_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "groq/openai/gpt-oss-120b"
TOP_K = 6
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
