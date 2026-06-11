from typing import List

from llama_index.core.embeddings import BaseEmbedding
from sentence_transformers import SentenceTransformer


class EmbeddingPersonalizado(BaseEmbedding):
    _modelo: SentenceTransformer = None

    def __init__(self, nombre_modelo: str, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(
            self,
            "_modelo",
            SentenceTransformer(nombre_modelo),
        )

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._modelo.encode(query).tolist()

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._modelo.encode(text).tolist()

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._modelo.encode(texts).tolist()

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    def encode(self, text: str) -> List[float]:
        return self._modelo.encode(text).tolist()
