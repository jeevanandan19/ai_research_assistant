"""
Embeddings Module
HuggingFace sentence-transformers embeddings (all-MiniLM-L6-v2)
"""
import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingsModule:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._embeddings = None

    def get_embeddings(self):
        """Lazy-load the HuggingFace embeddings model."""
        if self._embeddings is None:
            from langchain_huggingface import HuggingFaceEmbeddings
            logger.info(f"Loading embeddings model: {self.model_name}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("Embeddings model loaded.")
        return self._embeddings

    def embed_query(self, query: str) -> List[float]:
        return self.get_embeddings().embed_query(query)
