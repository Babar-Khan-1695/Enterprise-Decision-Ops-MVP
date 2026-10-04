from pathlib import Path
import json
import faiss
import numpy as np
from .embeddings import embed_texts
from config.settings import FAISS_DIR

INDEX_PATH = FAISS_DIR / "knowledge.index"
META_PATH = FAISS_DIR / "metadata.json"


def build_index(documents):
    if not documents:
        return False

    vectors = np.asarray(
        embed_texts([d["text"] for d in documents]),
        dtype="float32",
    )
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(
        json.dumps(documents, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def has_index():
    return INDEX_PATH.exists() and META_PATH.exists()


def get_index_stats():
    """Return truthful knowledge-base/index statistics for System Health."""
    if not has_index():
        return {
            "ready": False,
            "documents": 0,
            "chunks": 0,
            "sources": 0,
        }

    try:
        metadata = json.loads(
            META_PATH.read_text(encoding="utf-8")
        )
        sources = {
            str(item.get("source", "Unknown"))
            for item in metadata
            if isinstance(item, dict)
        }
        return {
            "ready": True,
            "documents": len(sources),
            "chunks": len(metadata),
            "sources": len(sources),
        }
    except Exception:
        return {
            "ready": False,
            "documents": 0,
            "chunks": 0,
            "sources": 0,
        }


def search(query, k=6):
    if not has_index():
        return []

    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(
        META_PATH.read_text(encoding="utf-8")
    )
    vector = np.asarray(
        embed_texts([query]),
        dtype="float32",
    )
    scores, ids = index.search(
        vector,
        min(k, len(metadata)),
    )

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx >= 0:
            item = dict(metadata[int(idx)])
            item["score"] = float(score)
            results.append(item)

    return results
