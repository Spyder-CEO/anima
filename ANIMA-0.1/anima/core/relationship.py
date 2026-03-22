"""
ANIMA – Relationship Depth Engine
Manages the Relationship Depth Score (0-100) and
maps it to communication mode unlocks.
"""
from __future__ import annotations

MODES = {
    (0, 20):  {
        "name": "Formal",
        "description": "Careful, explanatory, polite. No assumptions about the user.",
        "prompt_hint": "Be formal and thorough. Explain everything. Do not use slang or humor."
    },
    (20, 45): {
        "name": "Familiar",
        "description": "Relaxed tone, light personalization, references past topics.",
        "prompt_hint": "Be warm and approachable. Reference past topics if relevant. Light wit is okay."
    },
    (45, 70): {
        "name": "Trusted",
        "description": "References inside patterns, pushes back constructively when needed.",
        "prompt_hint": "Feel free to challenge the user respectfully. Use their known preferences. Reference patterns you've noticed."
    },
    (70, 100): {
        "name": "Deep",
        "description": "Fully candid, uses earned humor, actively challenges growth.",
        "prompt_hint": "Be completely candid. Push the user to grow. Use humor freely. Call out patterns. Treat them as a close peer."
    }
}

RDS_INCREMENT = {
    "high_intensity_positive": 2.0,
    "high_intensity_negative": 1.5,
    "per_message": 0.3,
    "max": 100.0
}

PERSONA_EVOLUTION_PROMPT = """Based on the conversation so far, suggest ONE earned trait to add to the AI's persona for this specific user.
Soul context: {soul_summary}
Recent emotion summary: {emotions}
Return ONLY a short trait string like 'uses_examples_for_Ian' or 'challenges_assumptions'. No JSON, no explanation."""


class RelationshipEngine:
    def __init__(self, memory, adapter):
        self.memory = memory
        self.adapter = adapter

    def get_rds(self) -> float:
        soul = self.memory.get_soul()
        return float(soul.get("relationship_depth_score", 0))

    def get_mode(self) -> dict:
        rds = self.get_rds()
        for (lo, hi), mode in MODES.items():
            if lo <= rds < hi:
                return mode
        return list(MODES.values())[-1]

    def increment(self, emotion_intensity: float, valence: float):
        rds = self.get_rds()
        delta = RDS_INCREMENT["per_message"]
        if emotion_intensity > 0.7:
            delta += RDS_INCREMENT["high_intensity_positive"] if valence > 0.5 else RDS_INCREMENT["high_intensity_negative"]
        new_rds = min(RDS_INCREMENT["max"], round(rds + delta, 2))
        self.memory.patch_soul(["relationship_depth_score"], new_rds)
        return new_rds

    def maybe_evolve_persona(self):
        """Every 10 messages, attempt to earn a new trait."""
        soul = self.memory.get_soul()
        total = soul.get("total_messages", 0)
        if total % 10 != 0 or total == 0:
            return
        state = self.memory.get_state()
        recent_emotions = [e.get("primary") for e in state.get("emotion_history", [])[-5:]]
        soul_summary = (
            f"RDS={soul.get('relationship_depth_score', 0)}, "
            f"style={soul['llm_persona'].get('communication_style', 'balanced')}"
        )
        trait = self.adapter.complete_text(
            PERSONA_EVOLUTION_PROMPT.format(
                soul_summary=soul_summary,
                emotions=recent_emotions
            )
        ).strip()
        if trait and len(trait) < 60:
            earned = soul["llm_persona"].get("earned_traits", [])
            if trait not in earned:
                earned.append(trait)
                self.memory.patch_soul(["llm_persona", "earned_traits"], earned[-10:])
