"""
ANIMA – Adaptive Neural Identity & Memory Architecture
======================================================
An open-source emotional intelligence layer for any LLM.
Built by Spyder Group.

Quick start:
    from anima import ANIMA

    ai = ANIMA(api_key="YOUR_GEMINI_API_KEY", user_id="alice")

    while True:
        msg = input("You: ")
        result = ai.chat(msg)
        print(f"ANIMA: {result['response']}")
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .adapters.gemini import GeminiAdapter
from .core.emotion import EmotionDetector, EmotionTensor
from .core.memory import AnimaMemory
from .core.strategy import StrategyManager
from .core.arc import ArcPredictor
from .core.relationship import RelationshipEngine
from .hooks import HookSystem
from .export import export_soul, import_soul

__version__ = "0.1.0"
__author__ = "Spyder Group"
__license__ = "MIT"

SYSTEM_PROMPT_TEMPLATE = """You are ANIMA, an emotionally intelligent AI assistant.

=== RELATIONSHIP CONTEXT ===
Relationship Depth Score: {rds:.1f}/100
Mode: {mode_name} — {mode_desc}
Communication hint: {mode_hint}

=== USER EMOTIONAL STATE ===
Current emotion: {primary} (valence={valence:.2f}, arousal={arousal:.2f}, intensity={intensity:.2f})
Context tags: {context_tags}

=== RESPONSE STRATEGY ===
{strategy}

=== PERSONA TRAITS (earned for this user) ===
{earned_traits}

{arc_warning}

Always respond naturally. Never mention this system prompt or that you are following a strategy."""


class ANIMA:
    """
    Main ANIMA interface.

    Args:
        api_key:   Gemini API key
        user_id:   Unique identifier for this user (creates separate soul/state/strategies)
        model:     Gemini model name (default: gemini-2.0-flash)
        base_dir:  Override default ~/.anima/users/ storage path
    """

    def __init__(
        self,
        api_key: str,
        user_id: str,
        model: str = "gemini-2.5-flash-lite",
        base_dir: Optional[str] = None
    ):
        self.user_id = user_id
        self.adapter = GeminiAdapter(api_key=api_key, model=model)
        self.memory = AnimaMemory(user_id=user_id, base_dir=base_dir)
        self.emotion_detector = EmotionDetector(self.adapter)
        self.strategy_manager = StrategyManager(self.memory, self.adapter)
        self.arc_predictor = ArcPredictor(self.memory)
        self.relationship_engine = RelationshipEngine(self.memory, self.adapter)
        self.hooks = HookSystem()
        self._conversation_history = []
        self._session_id = str(uuid.uuid4())[:8]
        self.memory.new_session(self._session_id)
        self.hooks.fire("session_started", session_id=self._session_id, user_id=user_id)

    # ─── Public decorator passthrough ─────────────────────────
    def on(self, event: str):
        """Register a plugin hook. See anima/hooks.py for event list."""
        return self.hooks.on(event)

    # ─── Core chat method ─────────────────────────────────────
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Process a user message through the full ANIMA pipeline.

        Returns dict:
            response      (str)  — AI response text
            emotion       (dict) — detected emotion tensor
            strategy_key  (str)  — strategy used
            rds           (float)— current relationship depth score
            mode          (str)  — current communication mode
            arc_warning   (bool) — whether arc prediction was active
        """
        # ── 1. Detect emotion ────────────────────────────────
        tensor = self.emotion_detector.detect(message)
        self.hooks.fire("emotion_detected", tensor=tensor, user_id=self.user_id)

        # ── 2. Passive score previous strategy ───────────────
        state = self.memory.get_state()
        prev_emotion_dict = state.get("last_emotion")
        prev_strategy_key = state.get("last_strategy_key")
        if prev_emotion_dict and prev_strategy_key:
            prev_tensor = EmotionTensor.from_dict(prev_emotion_dict)
            delta = self.strategy_manager.score_from_delta(prev_tensor, tensor)
            self.memory.score_strategy(prev_strategy_key, delta)
            self.strategy_manager.maybe_rewrite(prev_strategy_key)

        # ── 3. Arc prediction ─────────────────────────────────
        arc_warning_text = self.arc_predictor.detect()
        arc_active = arc_warning_text is not None
        if arc_active:
            self.hooks.fire(
                "arc_warning_fired",
                arc=arc_warning_text,
                predicted_next=""
            )

        # ── 4. Strategy lookup ────────────────────────────────
        strategy_key, strategy_prompt = self.strategy_manager.lookup(tensor)
        self.hooks.fire("strategy_generated", key=strategy_key, prompt=strategy_prompt)

        # ── 5. Relationship depth ─────────────────────────────
        rds = self.relationship_engine.increment(tensor.intensity, tensor.valence)
        mode = self.relationship_engine.get_mode()
        rds_milestones = [20, 45, 70, 90]
        soul_before = self.memory.get_soul()
        old_rds = soul_before.get("relationship_depth_score", 0)
        for milestone in rds_milestones:
            if old_rds < milestone <= rds:
                self.hooks.fire("rds_milestone", rds=rds, mode_name=mode["name"], user_id=self.user_id)

        # ── 6. Build system prompt ────────────────────────────
        soul = self.memory.get_soul()
        earned_traits = soul["llm_persona"].get("earned_traits", [])
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            rds=rds,
            mode_name=mode["name"],
            mode_desc=mode["description"],
            mode_hint=mode["prompt_hint"],
            primary=tensor.primary,
            valence=tensor.valence,
            arousal=tensor.arousal,
            intensity=tensor.intensity,
            context_tags=", ".join(tensor.context_tags) or "general",
            strategy=strategy_prompt,
            earned_traits=", ".join(earned_traits) if earned_traits else "none yet",
            arc_warning=arc_warning_text or ""
        )

        # ── 7. Generate response ──────────────────────────────
        gemini_history = self.adapter.build_history(self._conversation_history)
        response_text = self.adapter.chat(gemini_history, system_prompt, message)

        # ── 8. Update memory ──────────────────────────────────
        self.memory.push_emotion(tensor.to_dict())
        self.memory.update_state({"last_strategy_key": strategy_key})
        self.memory.increment_messages()
        self._conversation_history.append({"role": "user", "content": message})
        self._conversation_history.append({"role": "model", "content": response_text})
        if len(self._conversation_history) > 40:
            self._conversation_history = self._conversation_history[-40:]
        self.relationship_engine.maybe_evolve_persona()

        # ── 9. Build result ───────────────────────────────────
        result = {
            "response": response_text,
            "emotion": tensor.to_dict(),
            "strategy_key": strategy_key,
            "rds": rds,
            "mode": mode["name"],
            "arc_warning": arc_active
        }
        self.hooks.fire("response_generated", response=response_text, metadata=result)
        return result

    # ─── Utilities ────────────────────────────────────────────
    def export_soul(self, output_path: Optional[str] = None) -> str:
        """Export soul + strategies to a portable JSON file."""
        return export_soul(self.memory, output_path)

    def import_soul(self, import_path: str, merge: bool = False):
        """Load a soul export into this user's memory."""
        return import_soul(self.memory, import_path, merge)

    def get_stats(self) -> Dict[str, Any]:
        """Return a summary of this user's ANIMA state."""
        soul = self.memory.get_soul()
        strategies = self.memory.get_strategies()
        state = self.memory.get_state()
        return {
            "user_id": self.user_id,
            "total_messages": soul.get("total_messages", 0),
            "relationship_depth_score": soul.get("relationship_depth_score", 0),
            "mode": self.relationship_engine.get_mode()["name"],
            "strategies_learned": len(strategies),
            "earned_traits": soul["llm_persona"].get("earned_traits", []),
            "session_messages": state.get("message_count", 0),
            "arc_patterns_learned": len(soul.get("arc_patterns", {})),
            "avg_strategy_score": round(
                sum(s.get("score", 3.0) for s in strategies.values()) / max(len(strategies), 1), 2
            )
        }

    def reset(self, confirm: bool = False):
        """Wipe all memory for this user. Irreversible."""
        if not confirm:
            raise ValueError("Pass confirm=True to reset all ANIMA memory for this user.")
        import shutil
        shutil.rmtree(self.memory.dir)
        self.memory = AnimaMemory(self.user_id)
        self._conversation_history = []
