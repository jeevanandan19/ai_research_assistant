"""
Summarizer Module — uses modern LangChain invoke() API
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHARS = 14000


def _build_context(chunks, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    parts, total = [], 0
    for c in chunks:
        text = c.page_content.strip()
        if total + len(text) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                parts.append(text[:remaining])
            break
        parts.append(text)
        total += len(text)
    return "\n\n".join(parts)


class SummarizerModule:
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if not self._llm:
            from modules.llm_provider import get_llm
            self._llm = get_llm(temperature=0.2)
        return self._llm

    def _invoke(self, prompt_template, **kwargs) -> str:
        llm = self._get_llm()
        prompt_text = prompt_template.format(**kwargs)
        response = llm.invoke(prompt_text)
        return response.content if hasattr(response, "content") else str(response)

    def generate_summary(self, chunks) -> Dict[str, Any]:
        from modules.prompt_templates import get_summarization_prompt
        if not chunks:
            raise ValueError("No chunks provided.")
        logger.info("Generating summary...")
        context = _build_context(chunks, 14000)
        text = self._invoke(get_summarization_prompt(), context=context)
        logger.info("Summary done.")
        return {"success": True, "summary": text}

    def generate_insights(self, chunks) -> Dict[str, Any]:
        from modules.prompt_templates import get_insight_extraction_prompt
        if not chunks:
            raise ValueError("No chunks provided.")
        logger.info("Extracting insights...")
        context = _build_context(chunks, 10000)
        text = self._invoke(get_insight_extraction_prompt(), context=context)
        return {"success": True, "insights": text}

    def detect_novelty(self, chunks) -> Dict[str, Any]:
        from modules.prompt_templates import get_novelty_detection_prompt
        if not chunks:
            raise ValueError("No chunks provided.")
        logger.info("Detecting novelty...")
        context = _build_context(chunks, 10000)
        text = self._invoke(get_novelty_detection_prompt(), context=context)
        return {"success": True, "novelty": text}
