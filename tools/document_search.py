import os
import config.settings as settings
from config.logger import logger

def document_search(query: str) -> dict:
    """
    Searches documents in DOCS_FOLDER for content relevant to the query.
    Supports .txt, .md, .pdf, and .docx files.
    Never sends full documents to the agent — only top-scored excerpts.
    """
    docs_path = settings.DOCS_FOLDER

    if not os.path.exists(docs_path):
        return {
            "status": "error",
            "message": f"Folder not found: {docs_path}"
        }

    query_words = set(query.lower().split())
    scored_results = []

    for filename in os.listdir(docs_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.SUPPORTED_EXTENSIONS:
            continue
        if filename.startswith("~$"):
            continue

        filepath = os.path.join(docs_path, filename)

        try:
            content = _extract_text(filepath, ext)
        except Exception as e:
            logger.warning(f"Could not read {filename}: {e}")
            continue

        if not content.strip():
            continue

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

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_results[:3]

    clean_results = [
        {"source": r["source"], "excerpt": r["excerpt"]}
        for r in top_results
    ]

    return {"status": "success", "results": clean_results}


def _extract_text(filepath: str, ext: str) -> str:
    """Extracts plain text from .txt, .md, .pdf, or .docx files."""

    if ext in (".txt", ".md"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    elif ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join(
            para.text for para in doc.paragraphs if para.text.strip()
        )

    return ""


def _relevance_score(chunk: str, query_words: set) -> float:
    """Scores a chunk by how many query words appear in it."""
    chunk_words = set(chunk.lower().split())
    matched_words = query_words.intersection(chunk_words)

    if not matched_words:
        return 0.0

    score = len(matched_words) / len(query_words)
    length_penalty = min(1.0, 200 / max(len(chunk.split()), 1))

    return round(score * length_penalty, 4)


def _split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """Splits text into overlapping chunks so boundary content isn't missed."""
    words = text.split()
    chunks = []
    step = chunk_size // 2

    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks


def get_indexed_files() -> list[str]:
    """Returns a list of all supported files currently in DOCS_FOLDER."""
    if not os.path.exists(settings.DOCS_FOLDER):
        return []
    return [
    f for f in os.listdir(settings.DOCS_FOLDER)
    if os.path.splitext(f)[1].lower() in settings.SUPPORTED_EXTENSIONS
]