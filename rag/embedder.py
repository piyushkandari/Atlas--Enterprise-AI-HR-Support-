"""Wrapper around Gemini embeddings with retries.

Uses langchain-google-genai. Returns plain lists of floats.
"""
import os
import time

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

# Replacement for the retired models/text-embedding-004 (shut down Jan 2026).
# If this 404s, list models with:
#   python -c "import os,dotenv;dotenv.load_dotenv();from google import genai;\
#   print([m.name for m in genai.Client(api_key=os.environ['GOOGLE_API_KEY']).models.list() if 'embed' in m.name.lower()])"
EMBED_MODEL = "models/gemini-embedding-001"

# Gemini embedding API accepts batches, but small batches are more reliable
# under load (fewer 503s). 16 texts per call is a good balance.
BATCH_SIZE = 16
MAX_RETRIES = 5
BACKOFF_SECONDS = 2.0

_embedder: GoogleGenerativeAIEmbeddings | None = None


def get_embedder() -> GoogleGenerativeAIEmbeddings:
    global _embedder
    if _embedder is None:
        _embedder = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    return _embedder


def _embed_batch_with_retry(batch: list[str]) -> list[list[float]]:
    """Embed one batch, retrying on transient errors."""
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return get_embedder().embed_documents(batch)
        except Exception as e:
            last_err = e
            wait = BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"  embed attempt {attempt} failed ({type(e).__name__}); "
                  f"retrying in {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError(f"Embedding failed after {MAX_RETRIES} attempts: {last_err}")


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Splits into small batches and retries."""
    if not texts:
        return []
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        out.extend(_embed_batch_with_retry(batch))
    return out


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return get_embedder().embed_query(text)