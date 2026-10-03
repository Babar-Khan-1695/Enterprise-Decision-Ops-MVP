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
TOP_K = 4
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120

# Groq on-demand/free-style limits can be much lower than the model context window.
# Keep the workflow deliberately paced and compact so multiple specialist agents
# do not burst requests into the same token-per-minute window.
AGENT_MAX_TOKENS = 550
SYNTHESIZER_MAX_TOKENS = 750
AGENT_TEMPERATURE = 0.2
# GPT-OSS supports low/medium/high reasoning. Low is used here to avoid
# spending most of the small TPM budget on hidden reasoning tokens.
GROQ_REASONING_EFFORT = "low"
AGENT_DELAY_SECONDS = 25
MAX_RETRIES = 2
RETRY_BASE_SECONDS = 30
MAX_EVIDENCE_CHARS = 3500
MAX_CONTEXT_CHARS = 3000
