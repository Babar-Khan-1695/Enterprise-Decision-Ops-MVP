from .vector_store import search


def retrieve_context(query, k=6):
    results = search(query, k)
    if not results:
        return "No indexed enterprise documents were available."
    blocks = []
    for item in results:
        blocks.append(f"SOURCE: {item['source']} | CHUNK: {item['chunk']} | SCORE: {item['score']:.3f}\n{item['text']}")
    return "\n\n---\n\n".join(blocks)
