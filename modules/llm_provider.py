"""
LLM Provider Module — Gemini + OpenAI with automatic model fallback.

Gemini free-tier models (June 2025):
  gemini-2.0-flash-lite   ← lightest, separate quota  [DEFAULT]
  gemini-2.0-flash        ← fast, general purpose
  gemini-2.5-flash        ← more capable
  gemini-2.5-pro          ← most capable

If a model returns 404 (not found) or 429 (quota), the next model
in the fallback list is tried automatically.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

GEMINI_FALLBACK_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"


def get_llm(provider: str = None, temperature: float = 0.3):
    """Return a LangChain chat LLM instance."""
    provider = provider or os.environ.get("LLM_PROVIDER", "gemini")
    if provider == "openai":
        return _get_openai_llm(temperature)
    elif provider == "gemini":
        return _get_gemini_llm(temperature)
    else:
        raise ValueError(f"Unknown provider: '{provider}'. Use 'gemini' or 'openai'.")


# ── Internal: Gemini ──────────────────────────────────────────────

def _strip_prefix(model: str) -> str:
    return model[len("models/"):] if model.startswith("models/") else model


def _build_gemini(model: str, api_key: str, temperature: float):
    """Build a ChatGoogleGenerativeAI instance without testing it."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=_strip_prefix(model),
        temperature=temperature,
        google_api_key=api_key,
    )


def _get_gemini_llm(temperature: float):
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: F401
    except ImportError:
        raise ImportError("Run: pip install langchain-google-genai")

    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key or api_key == "your_google_api_key_here":
        raise ValueError(
            "GOOGLE_API_KEY not set.\n"
            "  Edit .env → replace 'your_google_api_key_here' with your real key.\n"
            "  Free key: https://aistudio.google.com/app/apikey"
        )

    preferred = _strip_prefix(os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite").strip())
    ordered   = [preferred] + [m for m in GEMINI_FALLBACK_MODELS if m != preferred]

    return _FallbackGeminiLLM(api_key=api_key, models=ordered, temperature=temperature)


class _FallbackGeminiLLM:
    """
    Thin wrapper that delegates to ChatGoogleGenerativeAI but automatically
    retries with the next model in the fallback list on 404 / 429 errors.
    """

    def __init__(self, api_key: str, models: list, temperature: float):
        self._api_key     = api_key
        self._models      = models
        self._temperature = temperature
        self._current_idx = 0
        self._llm         = _build_gemini(models[0], api_key, temperature)
        logger.info(f"Gemini LLM initialized with model: {models[0]}")

    # Expose current model name for logging
    @property
    def model_name(self) -> str:
        return self._models[self._current_idx]

    def invoke(self, prompt, **kwargs):
        while self._current_idx < len(self._models):
            try:
                return self._llm.invoke(prompt, **kwargs)
            except Exception as e:
                err = str(e)
                if ("429" in err or "RESOURCE_EXHAUSTED" in err or
                        "404" in err or "NOT_FOUND" in err):
                    logger.warning(
                        f"Model '{self.model_name}' unavailable ({err[:80]}...). "
                        "Trying next fallback..."
                    )
                    self._current_idx += 1
                    if self._current_idx < len(self._models):
                        next_model = self._models[self._current_idx]
                        logger.info(f"Switching to: {next_model}")
                        self._llm = _build_gemini(next_model, self._api_key, self._temperature)
                        time.sleep(1)
                        continue
                    else:
                        raise RuntimeError(
                            "All Gemini models are unavailable (quota or not found).\n"
                            "  → Wait a few minutes and retry, OR\n"
                            "  → Use a different API key, OR\n"
                            "  → Set LLM_PROVIDER=openai in .env"
                        )
                else:
                    raise  # Non-quota error → surface immediately

    # Passthrough for LangChain internals that may call .model_name or ._llm
    def __getattr__(self, name):
        return getattr(self._llm, name)


# ── Internal: OpenAI ──────────────────────────────────────────────

def _get_openai_llm(temperature: float):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError("Run: pip install langchain-openai")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .env")

    model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
    logger.info(f"Using OpenAI model: {model}")
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, max_tokens=2000)
