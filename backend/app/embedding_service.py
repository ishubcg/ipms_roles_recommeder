from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return embeddings


def embed_query(text: str) -> np.ndarray:
    model = get_embedding_model()
    embedding = model.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return embedding[0]