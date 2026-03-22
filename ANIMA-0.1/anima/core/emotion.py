"""
ANIMA – Emotion Tensor Detection
Detects a 6-dimensional emotional state from a user message.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from typing import List


@dataclass
class EmotionTensor:
    primary: str = "neutral"
    valence: float = 0.5       # 0=negative  1=positive
    arousal: float = 0.5       # 0=calm      1=excited
    dominance: float = 0.5     # 0=submissive 1=dominant
    intensity: float = 0.5     # 0=mild      1=overwhelming
    context_tags: List[str] = field(default_factory=list)

    def key(self) -> str:
        """Primary composite key used for strategy lookup."""
        ctx = self.context_tags[0] if self.context_tags else "general"
        return f"{self.primary}:{ctx}"

    def fallback_key(self) -> str:
        return self.primary

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EmotionTensor":
        return cls(**d)


DETECT_PROMPT = """You are an expert psychologist and emotion analyst.
Analyse the user message below and return ONLY valid JSON (no markdown, no explanation).

Message: {message}

Return this exact JSON schema:
{{
  "primary": "<single lowercase emotion word>",
  "valence": <float 0.0-1.0>,
  "arousal": <float 0.0-1.0>,
  "dominance": <float 0.0-1.0>,
  "intensity": <float 0.0-1.0>,
  "context_tags": ["<tag1>", "<tag2>"]
}}

primary examples: curious, frustrated, joyful, anxious, sad, excited, confused, neutral, angry, grateful
context_tags examples: technical, personal, philosophical, creative, urgent, casual, emotional"""


class EmotionDetector:
    def __init__(self, adapter):
        self.adapter = adapter

    def detect(self, message: str) -> EmotionTensor:
        prompt = DETECT_PROMPT.format(message=message)
        raw = self.adapter.complete_json(prompt)
        try:
            data = json.loads(raw)
            data["valence"] = float(data.get("valence", 0.5))
            data["arousal"] = float(data.get("arousal", 0.5))
            data["dominance"] = float(data.get("dominance", 0.5))
            data["intensity"] = float(data.get("intensity", 0.5))
            data["context_tags"] = data.get("context_tags", [])[:3]
            return EmotionTensor(**data)
        except Exception:
            return EmotionTensor()
