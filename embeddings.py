"""Lightweight embeddings utilities with graceful degradation when
heavy dependencies (sentence-transformers / scikit-learn) are not installed.
"""

_embed_model = None


def _get_model():
    """Lazily import and return a sentence-transformers model or None if unavailable."""
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None
    try:
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        return _embed_model
    except Exception:
        return None


def _has_sklearn():
    try:
        from sklearn.neighbors import NearestNeighbors  # noqa: F401
        return True
    except Exception:
        return False


from database import get_db


def build_user_embeddings():
    """Attempt to build an in-memory embeddings index. Returns None if resources
    (sentence-transformers or scikit-learn) are unavailable.
    """
    db = get_db()
    if db is None:
        return None

    profiles = list(db['user_profiles'].find({}))
    texts = []
    ids = []
    for p in profiles:
        uid = p.get('user_id')
        weekly = p.get('weekly_km', 0)
        last = p.get('last_activity')
        t = f"weekly_km:{weekly} last:{last} max_minutes:{p.get('max_minutes_per_session',120)}"
        texts.append(t)
        ids.append(uid)

    if not texts:
        return None

    model = _get_model()
    if model is None or not _has_sklearn():
        # Dependencies not available locally; return None so caller can fallback
        return None

    try:
        import numpy as np
        from sklearn.neighbors import NearestNeighbors
        vectors = model.encode(texts, convert_to_numpy=True)
        nbrs = NearestNeighbors(n_neighbors=min(10, len(vectors)), metric='cosine')
        nbrs.fit(vectors)
        return {'model': model, 'nbrs': nbrs, 'vectors': vectors, 'ids': ids}
    except Exception:
        return None


def query_similar_users(user_id, embeddings_index, topk=5):
    """Return topk similar user_ids to given user_id using built index.

    If embeddings_index is None, returns empty list to signal fallback behavior.
    """
    if embeddings_index is None:
        return []
    ids = embeddings_index.get('ids', [])
    if user_id not in ids:
        return []
    try:
        idx = ids.index(user_id)
        vec = embeddings_index['vectors'][idx].reshape(1, -1)
        dists, inds = embeddings_index['nbrs'].kneighbors(vec, n_neighbors=min(topk+1, len(ids)))
        results = []
        for i in inds[0]:
            uid = ids[i]
            if uid == user_id:
                continue
            results.append(uid)
            if len(results) >= topk:
                break
        return results
    except Exception:
        return []
