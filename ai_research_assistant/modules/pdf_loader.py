"""
PDF Loader Module — uses PyPDFLoader from langchain_community
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PDFLoaderModule:
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"valid": False, "message": "File does not exist"}
        if path.suffix.lower() != ".pdf":
            return {"valid": False, "message": "File is not a PDF"}
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            return {"valid": False, "message": f"File too large ({size_mb:.1f} MB). Max 50 MB."}
        return {"valid": True, "message": "OK", "size_mb": round(size_mb, 2)}

    def load_pdf(self, file_path: str):
        """Load PDF and return list of LangChain Document objects."""
        from langchain_community.document_loaders import PyPDFLoader
        v = self.validate_file(file_path)
        if not v["valid"]:
            raise ValueError(v["message"])
        logger.info(f"Loading: {file_path}")
        docs = PyPDFLoader(file_path).load()
        if not docs:
            raise ValueError("No content extracted from PDF.")
        logger.info(f"Loaded {len(docs)} pages.")
        return docs

    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        docs = self.load_pdf(file_path)
        full_text = " ".join(d.page_content for d in docs)
        return {
            "filename": path.name,
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "total_pages": len(docs),
            "word_count": len(full_text.split()),
            "char_count": len(full_text),
            "file_path": str(file_path),
        }
