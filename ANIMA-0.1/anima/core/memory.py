"""
ANIMA – Persistent Memory Layer
Manages soul.json, state.json, strategies.json on disk.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SOUL_TEMPLATE: Dict[str, Any] = {
    "user_id": "",
    "created_at": "",
    "total_messages": 0,
    "relationship_depth_score": 0,
    "llm_persona": {
        "communication_style": "balanced",
        "humor_level": 0.3,
        "challenge_threshold": 0.5,
        "earned_traits": []
    },
    "user_profile": {
        "dominant_emotions": {},
        "sensitivities": [],
        "values": [],
        "communication_preferences": []
    },
    "arc_patterns": {}
}

STATE_TEMPLATE: Dict[str, Any] = {
    "session_id": "",
    "started_at": "",
    "emotion_history": [],
    "last_strategy_key": None,
    "last_emotion": None,
    "message_count": 0
}

STRATEGY_TEMPLATE: Dict[str, Any] = {}


class AnimaMemory:
    def __init__(self, user_id: str, base_dir: Optional[str] = None):
        self.user_id = user_id
        root = Path(base_dir) if base_dir else Path.home() / ".anima" / "users"
        self.dir = root / user_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._soul_path = self.dir / "soul.json"
        self._state_path = self.dir / "state.json"
        self._strategies_path = self.dir / "strategies.json"
        self._init_files()

    def _init_files(self):
        if not self._soul_path.exists():
            soul = dict(SOUL_TEMPLATE)
            soul["user_id"] = self.user_id
            soul["created_at"] = _now()
            self._write(self._soul_path, soul)
        if not self._state_path.exists():
            self._write(self._state_path, dict(STATE_TEMPLATE))
        if not self._strategies_path.exists():
            self._write(self._strategies_path, {})

    def _read(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── Soul ──────────────────────────────
    def get_soul(self) -> dict:
        return self._read(self._soul_path)

    def update_soul(self, updates: dict):
        soul = self.get_soul()
        soul.update(updates)
        self._write(self._soul_path, soul)

    def patch_soul(self, path: list, value: Any):
        """Deep patch: path=['llm_persona','humor_level'], value=0.6"""
        soul = self.get_soul()
        d = soul
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value
        self._write(self._soul_path, soul)

    # ── State ─────────────────────────────
    def get_state(self) -> dict:
        return self._read(self._state_path)

    def update_state(self, updates: dict):
        state = self.get_state()
        state.update(updates)
        self._write(self._state_path, state)

    def push_emotion(self, emotion_dict: dict):
        state = self.get_state()
        history = state.get("emotion_history", [])
        history.append(emotion_dict)
        if len(history) > 20:
            history = history[-20:]
        state["emotion_history"] = history
        state["last_emotion"] = emotion_dict
        self._write(self._state_path, state)

    def new_session(self, session_id: str):
        import uuid
        state = {
            "session_id": session_id,
            "started_at": _now(),
            "emotion_history": [],
            "last_strategy_key": None,
            "last_emotion": None,
            "message_count": 0
        }
        self._write(self._state_path, state)

    # ── Strategies ────────────────────────
    def get_strategies(self) -> dict:
        return self._read(self._strategies_path)

    def get_strategy(self, key: str) -> Optional[dict]:
        return self.get_strategies().get(key)

    def upsert_strategy(self, key: str, prompt: str, score: float = 3.0):
        strategies = self.get_strategies()
        existing = strategies.get(key, {})
        version = existing.get("version", 0) + 1
        strategies[key] = {
            "prompt": prompt,
            "score": score,
            "uses": existing.get("uses", 0),
            "version": version,
            "updated_at": _now(),
            "history": existing.get("history", [])[-4:] + [
                {"prompt": existing.get("prompt", ""), "score": existing.get("score", 3.0)}
            ] if existing else []
        }
        self._write(self._strategies_path, strategies)

    def score_strategy(self, key: str, delta: float):
        strategies = self.get_strategies()
        if key not in strategies:
            return
        entry = strategies[key]
        old_score = entry.get("score", 3.0)
        entry["score"] = round(max(1.0, min(5.0, old_score + delta)), 2)
        entry["uses"] = entry.get("uses", 0) + 1
        self._write(self._strategies_path, strategies)

    def increment_messages(self):
        soul = self.get_soul()
        soul["total_messages"] = soul.get("total_messages", 0) + 1
        self._write(self._soul_path, soul)
        state = self.get_state()
        state["message_count"] = state.get("message_count", 0) + 1
        self._write(self._state_path, state)
