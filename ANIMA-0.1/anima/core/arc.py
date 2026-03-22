"""
ANIMA – Emotional Arc Predictor
Tracks sequences of emotions and fires preemptive strategy shifts
when a known negative arc is detected early.
"""
from __future__ import annotations
from typing import List, Optional
from .emotion import EmotionTensor

KNOWN_NEGATIVE_ARCS = [
    ["curious", "confused", "frustrated"],
    ["excited", "anxious", "overwhelmed"],
    ["hopeful", "neutral", "sad"],
    ["curious", "stuck", "disengaged"],
    ["joyful", "neutral", "frustrated"],
]

ARC_WARNING_PROMPT = """WARNING – Arc Prediction Active:
The user has shown the emotional sequence: {arc}.
Historical data suggests they may be heading toward: {predicted_next}.
Proactively shift your tone to prevent emotional deterioration.
Be more encouraging, simplify language, and acknowledge their effort explicitly."""


class ArcPredictor:
    def __init__(self, memory):
        self.memory = memory

    def get_recent_primaries(self, n: int = 5) -> List[str]:
        state = self.memory.get_state()
        history = state.get("emotion_history", [])
        return [e.get("primary", "neutral") for e in history[-n:]]

    def detect(self) -> Optional[str]:
        """
        Returns an arc-warning system prompt snippet if a known negative arc
        is detected in the recent emotion history. Returns None otherwise.
        """
        recent = self.get_recent_primaries(5)
        if len(recent) < 2:
            return None

        for arc in KNOWN_NEGATIVE_ARCS:
            arc_len = len(arc)
            # Check if any sub-sequence of recent matches arc[:-1]
            trigger = arc[:-1]
            for i in range(len(recent) - len(trigger) + 1):
                if recent[i:i + len(trigger)] == trigger:
                    return ARC_WARNING_PROMPT.format(
                        arc=" → ".join(trigger),
                        predicted_next=arc[-1]
                    )

        # Check for custom learned arcs from soul
        soul = self.memory.get_soul()
        learned = soul.get("arc_patterns", {})
        for arc_key, data in learned.items():
            trigger = arc_key.split("→")
            trigger = [t.strip() for t in trigger[:-1]]
            predicted = arc_key.split("→")[-1].strip()
            if len(recent) >= len(trigger):
                if recent[-len(trigger):] == trigger:
                    return ARC_WARNING_PROMPT.format(
                        arc=" → ".join(trigger),
                        predicted_next=predicted
                    )
        return None

    def record_arc_outcome(self, arc: List[str]):
        """Record completed emotional arcs into soul for future learning."""
        if len(arc) < 3:
            return
        soul = self.memory.get_soul()
        patterns = soul.get("arc_patterns", {})
        key = " → ".join(arc[-3:])
        patterns[key] = patterns.get(key, 0) + 1
        soul["arc_patterns"] = patterns
        self.memory.update_soul(soul)
