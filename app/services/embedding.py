# embedding wrapper
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

MODEL = SentenceTransformer(os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"))
Q = QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))


def embed_text(text: str):
    vec = MODEL.encode(text)
    return vec.tolist()


def upsert_vector(collection: str, point_id: str, vector: list, payload: dict):
    # Ensure collection exists
    try:
        Q.recreate_collection(collection_name=collection, vector_size=len(vector))
    except Exception:
        # collection may already exist
        pass
    Q.upsert(
        collection_name=collection,
        points=[{"id": point_id, "vector": vector, "payload": payload}],
    )


def search_vectors(collection: str, query_vec: list, limit=5):
    hits = Q.search(collection_name=collection, query_vector=query_vec, limit=limit)
    return hits
