"""JSON-backed vector store with cosine similarity search.

For a few hundred chunks this is instant. Each item is stored as:
    {"text": ..., "metadata": {...}, "vector": [...]}
The whole store is one JSON file under vector_store/.
"""
import json
import math
from pathlib import Path


class VectorStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.items: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            self.items = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.items), encoding="utf-8")

    def clear(self) -> None:
        self.items = []

    def add(self, text: str, metadata: dict, vector: list[float]) -> None:
        self.items.append({"text": text, "metadata": metadata, "vector": vector})

    def search(self, query_vector: list[float], k: int = 4,
               where: dict | None = None) -> list[dict]:
        """Top-k by cosine similarity, optionally filtered by metadata."""
        def _matches(md: dict) -> bool:
            if not where:
                return True
            return all(md.get(key) == val for key, val in where.items())

        scored = []
        for item in self.items:
            if not _matches(item["metadata"]):
                continue
            score = _cosine(query_vector, item["vector"])
            scored.append({
                "text": item["text"],
                "metadata": item["metadata"],
                "score": round(score, 4),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)