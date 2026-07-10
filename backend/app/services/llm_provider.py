"""Optional LLM provider for AIC Intelligence.

Wraps Vertex AI Gemini when it is available (google-cloud-aiplatform installed
AND a project configured AND the API reachable). Every failure path degrades
gracefully to ``None`` so callers fall back to the deterministic heuristic
planner — the feature therefore works with no external dependency and simply
gets smarter once Vertex AI is enabled.

Nothing here ever sees raw microdata: callers pass only column names, labels
and the user's typed question.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_MODEL_NAME = os.getenv("AIC_LLM_MODEL", "gemini-1.5-flash")
_CACHED_MODEL: Any = None
_TRIED_INIT = False


def _project() -> Optional[str]:
    return (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
        or os.getenv("GCLOUD_PROJECT")
    )


def _init_model() -> Any:
    """Lazily initialise the Gemini model; return None if unavailable."""
    global _CACHED_MODEL, _TRIED_INIT
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL
    if _TRIED_INIT:
        return _CACHED_MODEL
    _TRIED_INIT = True

    # Explicit opt-out.
    if os.getenv("AIC_DISABLE_LLM", "").lower() in ("1", "true", "yes"):
        logger.info("AIC LLM disabled via AIC_DISABLE_LLM")
        return None
    project = _project()
    if not project:
        logger.info("AIC LLM: no GCP project configured; using heuristic planner")
        return None
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=project, location=os.getenv("AIC_LLM_LOCATION", "us-central1"))
        _CACHED_MODEL = GenerativeModel(_MODEL_NAME)
        logger.info("AIC LLM: initialised Vertex AI model %s", _MODEL_NAME)
    except Exception as exc:  # ImportError, auth, API-not-enabled, etc.
        logger.info("AIC LLM unavailable (%s); using heuristic planner", exc)
        _CACHED_MODEL = None
    return _CACHED_MODEL


def is_available() -> bool:
    return _init_model() is not None


def generate_json(prompt: str, *, timeout: int = 20) -> Optional[dict[str, Any]]:
    """Ask the model for a JSON object. Returns a dict, or None on any failure."""
    model = _init_model()
    if model is None:
        return None
    try:
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
        )
        text = (resp.text or "").strip()
        if not text:
            return None
        # Be tolerant of accidental code fences.
        if text.startswith("```"):
            text = text.strip("`")
            text = text[text.find("{"):]
        return json.loads(text)
    except Exception as exc:
        logger.warning("AIC LLM generate_json failed (%s); falling back", exc)
        return None
