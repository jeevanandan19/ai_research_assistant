"""
Vector Store Module — FAISS with LangChain
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class VectorStoreModule:
    def __init__(self, embeddings_module, index_path: str = "database/faiss_index"):
        self.embeddings_module = embeddings_module
        self.index_path = index_path
        self.vector_store = None

    def create_vector_store(self, chunks: list):
        from langchain_community.vectorstores import FAISS
        if not chunks:
            raise ValueError("No chunks provided.")
        logger.info(f"Creating FAISS store with {len(chunks)} chunks...")
        embeddings = self.embeddings_module.get_embeddings()
        self.vector_store = FAISS.from_documents(chunks, embeddings)
        logger.info("FAISS store created.")
        return self.vector_store

    def save_vector_store(self, path: str = None):
        save_path = path or self.index_path
        os.makedirs(save_path, exist_ok=True)
        self.vector_store.save_local(save_path)
        logger.info(f"Saved FAISS index to: {save_path}")
        return save_path

    def load_vector_store(self, path: str = None):
        from langchain_community.vectorstores import FAISS
        load_path = path or self.index_path
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"No FAISS index at: {load_path}")
        embeddings = self.embeddings_module.get_embeddings()
        self.vector_store = FAISS.load_local(
            load_path, embeddings, allow_dangerous_deserialization=True
        )
        logger.info(f"Loaded FAISS index from: {load_path}")
        return self.vector_store

    def similarity_search(self, query: str, k: int = 5) -> list:
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized.")
        return self.vector_store.similarity_search(query, k=k)

    def get_retriever(self, k: int = 5):
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized.")
        return self.vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": k}
        )

    def index_exists(self, path: str = None) -> bool:
        return os.path.exists(path or self.index_path)
