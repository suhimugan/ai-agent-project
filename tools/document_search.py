import os
from config.settings import DOCS_FOLDER


def document_search(query: str) -> dict:
    """
    Searches local documents for content relevant to the query.
    Uses relevance scoring — partial word matches are ranked and returned.
    Never sends full documents to the agent — only top-scored excerpts.
    """
    docs_path = DOCS_FOLDER

    if not os.path.exists(docs_path):
        return {
            "status": "error",
            "message": f"Docs folder not found: {docs_path}"
        }

    query_words = set(query.lower().split())
    scored_results = []

    for filename in os.listdir(docs_path):
        if not filename.endswith((".txt", ".md")):
            continue

        filepath = os.path.join(docs_path, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = _split_into_chunks(content, chunk_size=500)

        for chunk in chunks:
            score = _relevance_score(chunk, query_words)
            if score > 0:
                scored_results.append({
                    "source": filename,
                    "excerpt": chunk.strip(),
                    "score": score
                })

    if not scored_results:
        return {
            "status": "no_results",
            "message": f"No documents found matching: {query}"
        }

    # Sort by relevance score, return top 3
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_results[:3]

    # Remove score from what gets sent to the agent
    clean_results = [
        {"source": r["source"], "excerpt": r["excerpt"]}
        for r in top_results
    ]

    return {"status": "success", "results": clean_results}


def _relevance_score(chunk: str, query_words: set) -> float:
    """
    Scores a chunk based on how many query words appear in it.
    Longer chunks are penalized slightly to prefer focused excerpts.
    """
    chunk_lower = chunk.lower()
    chunk_words = set(chunk_lower.split())

    matched_words = query_words.intersection(chunk_words)
    if not matched_words:
        return 0.0

    # Score = matched words / total query words (0.0 to 1.0)
    score = len(matched_words) / len(query_words)

    # Small penalty for very long chunks (prefer focused excerpts)
    length_penalty = min(1.0, 200 / max(len(chunk.split()), 1))
    
    return round(score * length_penalty, 4)


def _split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """
    Splits text into overlapping chunks.
    Overlap ensures answers near chunk boundaries are not missed.
    """
    words = text.split()
    chunks = []
    step = chunk_size // 2  # 50% overlap between chunks

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks