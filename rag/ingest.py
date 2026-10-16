"""Read data/policies (PDFs) and data/it_kb (TXT) into the vector store.

Run from project root:
    python -m rag.ingest

Safe to re-run — it rebuilds both stores from scratch.
"""
from pathlib import Path

from pypdf import PdfReader

from .embedder import embed_documents
from .store import VectorStore


POLICY_PDF_DIR = Path("data/policies")
IT_KB_DIR = Path("data/it_kb")
POLICY_STORE = "vector_store/policies.json"
IT_KB_STORE = "vector_store/it_kb.json"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _chunk(text: str) -> list[str]:
    """Character-based chunker with overlap."""
    text = text.strip()
    if len(text) <= CHUNK_SIZE:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def _read_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] — page numbers are 1-indexed."""
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    return pages


def ingest_policies() -> int:
    store = VectorStore(POLICY_STORE)
    store.clear()

    for pdf in sorted(POLICY_PDF_DIR.glob("*.pdf")):
        for page_num, page_text in _read_pdf_pages(pdf):
            chunks = _chunk(page_text)
            if not chunks:
                continue
            vectors = embed_documents(chunks)
            for ch, vec in zip(chunks, vectors):
                store.add(ch, {
                    "source": pdf.name,
                    "page": page_num,
                    "scope": "company",
                }, vec)

    store.save()
    return len(store.items)


def ingest_it_kb() -> int:
    store = VectorStore(IT_KB_STORE)
    store.clear()

    for txt in sorted(IT_KB_DIR.glob("*.txt")):
        text = txt.read_text(encoding="utf-8")
        chunks = _chunk(text)
        if not chunks:
            continue
        vectors = embed_documents(chunks)
        for ch, vec in zip(chunks, vectors):
            store.add(ch, {
                "source": txt.name,
                "page": 1,
                "scope": "company",
            }, vec)

    store.save()
    return len(store.items)


def main() -> None:
    print("Ingesting policies...")
    n1 = ingest_policies()
    print(f"  stored {n1} policy chunks")

    print("Ingesting IT KB...")
    n2 = ingest_it_kb()
    print(f"  stored {n2} IT KB chunks")

    print("Done. Vector store at ./vector_store/")


if __name__ == "__main__":
    main()