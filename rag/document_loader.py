from pathlib import Path
from .document_processor import extract_pdf, chunk_text


def load_uploaded_documents(paths):
    documents = []
    for path in paths:
        path = Path(path)
        if path.suffix.lower() == ".pdf":
            text = extract_pdf(path)
            for i, chunk in enumerate(chunk_text(text)):
                documents.append({"text": chunk, "source": path.name, "chunk": i})
    return documents
