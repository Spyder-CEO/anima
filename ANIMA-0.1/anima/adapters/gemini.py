"""
ANIMA – Gemini Adapter
Wraps google-generativeai for text completion, JSON completion,
and multi-turn chat.
"""
from __future__ import annotations
import json
import re
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai is required. Install it with:\n"
        "  pip install google-generativeai"
    )


class GeminiAdapter:
    """
    Wraps Gemini API for three use cases:
    - complete_text(prompt)        → plain text response
    - complete_json(prompt)        → JSON string
    - chat(history, system, user)  → plain text response in a conversation
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self._model = genai.GenerativeModel(model)

    def complete_text(self, prompt: str) -> str:
        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[ANIMA adapter error: {e}]"

    def complete_json(self, prompt: str) -> str:
        """Returns raw JSON string. Strips markdown code fences if present."""
        raw = self.complete_text(prompt)
        raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
        raw = re.sub(r"```$", "", raw.strip())
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return raw

    def chat(
        self,
        history: List[Dict[str, str]],
        system_prompt: str,
        user_message: str
    ) -> str:
        """
        history: list of {"role": "user"|"model", "parts": "..."}
        """
        try:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt
            )
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(user_message)
            return response.text.strip()
        except Exception as e:
            return f"[ANIMA adapter error: {e}]"

    def build_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert ANIMA message format to Gemini history format."""
        gemini_history = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": msg["content"]})
        return gemini_history
