"""
Keyword Extractor Module
"""
import json
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class KeywordExtractorModule:
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if not self._llm:
            from modules.llm_provider import get_llm
            self._llm = get_llm(temperature=0.1)
        return self._llm

    def _build_context(self, chunks, max_chars: int = 8000) -> str:
        parts, total = [], 0
        for c in chunks:
            text = c.page_content.strip()
            if total + len(text) > max_chars:
                break
            parts.append(text)
            total += len(text)
        return "\n\n".join(parts)

    def _parse_response(self, text: str) -> Dict[str, List[str]]:
        # Try to extract JSON from the response
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "primary_keywords": data.get("primary_keywords", []),
                    "technical_methods": data.get("technical_methods", []),
                    "datasets_and_metrics": data.get("datasets_and_metrics", []),
                    "domain_concepts": data.get("domain_concepts", []),
                }
            except json.JSONDecodeError:
                pass

        # Fallback: extract quoted or capitalised terms
        logger.warning("JSON parse failed — using fallback keyword extraction.")
        words = re.findall(r'"([^"]+)"', text)
        if not words:
            words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
        return {
            "primary_keywords": list(dict.fromkeys(words[:15])),
            "technical_methods": [],
            "datasets_and_metrics": [],
            "domain_concepts": [],
        }

    def extract_keywords(self, chunks) -> Dict[str, Any]:
        from modules.prompt_templates import get_keyword_extraction_prompt
        if not chunks:
            raise ValueError("No chunks provided.")

        logger.info("Extracting keywords...")
        context = self._build_context(chunks)
        prompt = get_keyword_extraction_prompt()
        llm = self._get_llm()

        prompt_text = prompt.format(context=context)
        response = llm.invoke(prompt_text)
        text = response.content if hasattr(response, "content") else str(response)

        categorized = self._parse_response(text)

        all_kw, seen = [], set()
        for lst in categorized.values():
            for kw in lst:
                k = kw.strip()
                if k and k.lower() not in seen:
                    all_kw.append(k)
                    seen.add(k.lower())

        logger.info(f"Extracted {len(all_kw)} keywords.")
        return {
            "success": True,
            "categorized": categorized,
            "all_keywords": all_kw,
            "total_count": len(all_kw),
        }
