"""
RAG Chain Module
Uses modern LangChain LCEL pipeline (RetrievalQA removed in 1.x)
Pattern: retriever | format_docs | prompt | llm | parse
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

NOT_FOUND = "Information not found in the uploaded document."


class RAGChainModule:
    def __init__(self, vector_store_module, retrieval_k: int = 5):
        self.vector_store_module = vector_store_module
        self.retrieval_k = retrieval_k
        self._llm = None

    def _get_llm(self):
        if not self._llm:
            from modules.llm_provider import get_llm
            self._llm = get_llm(temperature=0.1)
        return self._llm

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Retrieve relevant chunks from FAISS, then ask the LLM with
        a grounded prompt. Returns answer + retrieved context.
        """
        if not question.strip():
            return {"success": False, "answer": "Please provide a question.",
                    "retrieved_context": [], "num_sources": 0}

        from modules.prompt_templates import get_qa_prompt

        # 1. Semantic retrieval
        try:
            source_docs = self.vector_store_module.similarity_search(
                question, k=self.retrieval_k
            )
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return {"success": False, "answer": f"Retrieval failed: {e}",
                    "retrieved_context": [], "num_sources": 0}

        if not source_docs:
            return {"success": True, "answer": NOT_FOUND,
                    "retrieved_context": [], "num_sources": 0}

        # 2. Build context string
        context = "\n\n".join(
            f"[Page {d.metadata.get('page', '?')}]\n{d.page_content.strip()}"
            for d in source_docs
        )

        # 3. Format prompt and call LLM
        prompt = get_qa_prompt()
        prompt_text = prompt.format(context=context, question=question)
        llm = self._get_llm()

        try:
            response = llm.invoke(prompt_text)
            answer = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {"success": False, "answer": f"LLM error: {e}",
                    "retrieved_context": [], "num_sources": 0}

        # 4. Format retrieved context for UI
        retrieved_context = [
            {
                "chunk_index": i + 1,
                "content": d.page_content.strip(),
                "page": d.metadata.get("page", "N/A"),
                "source": d.metadata.get("source", "Document"),
            }
            for i, d in enumerate(source_docs)
        ]

        logger.info(f"Answered using {len(source_docs)} sources.")
        return {
            "success": True,
            "answer": answer,
            "retrieved_context": retrieved_context,
            "num_sources": len(source_docs),
        }

    def invalidate_chain(self):
        """Reset LLM cache when a new document is loaded."""
        self._llm = None
        logger.info("RAG chain reset.")
