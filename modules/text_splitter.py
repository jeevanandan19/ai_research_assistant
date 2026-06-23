"""
Text Splitter Module — RecursiveCharacterTextSplitter
"""
import logging
from typing import List

logger = logging.getLogger(__name__)


class TextSplitterModule:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        logger.info(f"TextSplitter: chunk_size={chunk_size}, overlap={chunk_overlap}")

    def split_documents(self, documents) -> list:
        chunks = self.splitter.split_documents(documents)
        for i, c in enumerate(chunks):
            c.metadata["chunk_id"] = i
        logger.info(f"Created {len(chunks)} chunks.")
        return chunks

    def get_stats(self, chunks: list) -> dict:
        if not chunks:
            return {}
        sizes = [len(c.page_content) for c in chunks]
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": round(sum(sizes) / len(sizes)),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
        }
