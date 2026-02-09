from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def _get_env(name: str, default: Optional[str] = None) -> str:
    v = os.environ.get(name, default)
    if v is None or not str(v).strip():
        raise RuntimeError(f"Missing environment variable: {name}")
    return str(v).strip()


def generate_json(prompt: str) -> Dict[str, Any]:
    """
    Attempts to call Gemini via either:
      - google-genai (newer)
      - google-generativeai (older)
    Returns parsed JSON dict.

    Environment:
      GEMINI_API_KEY
      GEMINI_MODEL
      GEMINI_TEMPERATURE (optional)
    """
    api_key = _get_env("GEMINI_API_KEY")
    model = _get_env("GEMINI_MODEL")
    temperature = float(os.environ.get("GEMINI_TEMPERATURE", "0.2"))

    # 1) Try google-genai
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"temperature": temperature},
        )
        text = resp.text or ""
        return json.loads(text)
    except Exception:
        pass

    # 2) Try google-generativeai
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        resp = m.generate_content(
            prompt,
            generation_config={"temperature": temperature},
        )
        text = getattr(resp, "text", "") or ""
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(
            "Failed to call Gemini. Install either `google-genai` or `google-generativeai`, "
            "and verify GEMINI_API_KEY / GEMINI_MODEL are set."
        ) from e
