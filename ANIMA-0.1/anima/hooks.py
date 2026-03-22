"""
ANIMA – Plugin Hook System
Allows developers to attach callbacks to ANIMA lifecycle events.

Usage:
    from anima import ANIMA
    ai = ANIMA(api_key="...", user_id="ian")

    @ai.on("emotion_detected")
    def handle_emotion(tensor, user_id):
        print(f"Detected: {tensor.primary} for {user_id}")

    @ai.on("strategy_rewritten")
    def log_rewrite(key, old_prompt, new_prompt):
        print(f"Strategy {key} was rewritten")

Available events:
    - emotion_detected(tensor, user_id)
    - strategy_generated(key, prompt)
    - strategy_rewritten(key, old_prompt, new_prompt)
    - arc_warning_fired(arc, predicted_next)
    - rds_milestone(rds, mode_name, user_id)
    - session_started(session_id, user_id)
    - response_generated(response, metadata)
"""
from __future__ import annotations
from typing import Callable, Dict, List, Any


class HookSystem:
    VALID_EVENTS = {
        "emotion_detected",
        "strategy_generated",
        "strategy_rewritten",
        "arc_warning_fired",
        "rds_milestone",
        "session_started",
        "response_generated",
    }

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {e: [] for e in self.VALID_EVENTS}

    def on(self, event: str):
        """Decorator: @ai.on("emotion_detected")"""
        if event not in self.VALID_EVENTS:
            raise ValueError(
                f"Unknown event '{event}'. Valid events: {self.VALID_EVENTS}"
            )
        def decorator(fn: Callable):
            self._hooks[event].append(fn)
            return fn
        return decorator

    def fire(self, event: str, **kwargs: Any):
        for fn in self._hooks.get(event, []):
            try:
                fn(**kwargs)
            except Exception as e:
                print(f"[ANIMA hook error] Event={event} fn={fn.__name__}: {e}")
