"""Query helpers over the two vector stores."""
from .embedder import embed_query
from .store import VectorStore


POLICY_STORE = "vector_store/policies.json"
IT_KB_STORE = "vector_store/it_kb.json"


def _search(store_path: str, query: str, k: int = 4) -> list[dict]:
    store = VectorStore(store_path)
    if not store.items:
        return []
    vec = embed_query(query)
    hits = store.search(vec, k=k)
    return [
        {
            "text": h["text"],
            "source": h["metadata"].get("source", "unknown"),
            "page": h["metadata"].get("page", 1),
            "score": h["score"],
        }
        for h in hits
    ]


def search_policy(query: str, k: int = 4) -> list[dict]:
    return _search(POLICY_STORE, query, k=k)


def search_it_kb(query: str, k: int = 4) -> list[dict]:
    return _search(IT_KB_STORE, query, k=k)