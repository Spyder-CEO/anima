"""
ANIMA – Strategy Manager
Looks up, generates, scores, and rewrites response strategies.
"""
from __future__ import annotations
from typing import Optional, Tuple
from .emotion import EmotionTensor

STRATEGY_GEN_PROMPT = """You are ANIMA, an emotionally intelligent AI system designing your own response strategy.

User profile context: {soul_summary}
Current emotion tensor: primary={primary}, valence={valence:.2f}, arousal={arousal:.2f}, dominance={dominance:.2f}, intensity={intensity:.2f}, tags={tags}

Write a concise system prompt (2-4 sentences) that tells an AI how to best respond when a user feels this way.
Focus on: tone, pacing, language style, what to avoid, what to emphasize.
Return ONLY the prompt text, no JSON, no labels."""

STRATEGY_REWRITE_PROMPT = """You are ANIMA improving a response strategy that performed poorly.

Emotion key: {key}
Old strategy (score {score:.1f}/5.0): {old_prompt}

The old strategy underperformed. Rewrite it to be significantly better.
Return ONLY the new prompt text."""


class StrategyManager:
    def __init__(self, memory, adapter):
        self.memory = memory
        self.adapter = adapter

    def lookup(self, tensor: EmotionTensor) -> Tuple[str, str]:
        """Returns (key_used, prompt). Tries exact → fallback → generates fresh."""
        # 1. Exact composite key
        entry = self.memory.get_strategy(tensor.key())
        if entry and entry.get("score", 3.0) >= 2.0:
            return tensor.key(), entry["prompt"]

        # 2. Primary-only fallback
        entry = self.memory.get_strategy(tensor.fallback_key())
        if entry and entry.get("score", 3.0) >= 2.0:
            return tensor.fallback_key(), entry["prompt"]

        # 3. Generate fresh
        prompt = self._generate(tensor)
        key = tensor.key()
        self.memory.upsert_strategy(key, prompt, score=3.0)
        return key, prompt

    def _generate(self, tensor: EmotionTensor) -> str:
        soul = self.memory.get_soul()
        soul_summary = (
            f"RDS={soul.get('relationship_depth_score', 0)}, "
            f"style={soul['llm_persona'].get('communication_style', 'balanced')}, "
            f"traits={soul['llm_persona'].get('earned_traits', [])}"
        )
        prompt_text = STRATEGY_GEN_PROMPT.format(
            soul_summary=soul_summary,
            primary=tensor.primary,
            valence=tensor.valence,
            arousal=tensor.arousal,
            dominance=tensor.dominance,
            intensity=tensor.intensity,
            tags=tensor.context_tags
        )
        return self.adapter.complete_text(prompt_text)

    def maybe_rewrite(self, key: str):
        """Rewrites strategy if score has dropped below threshold."""
        entry = self.memory.get_strategy(key)
        if not entry:
            return
        if entry.get("score", 3.0) < 2.2 and entry.get("uses", 0) >= 3:
            rewrite_prompt = STRATEGY_REWRITE_PROMPT.format(
                key=key,
                score=entry["score"],
                old_prompt=entry["prompt"]
            )
            new_prompt = self.adapter.complete_text(rewrite_prompt)
            self.memory.upsert_strategy(key, new_prompt, score=3.0)

    def score_from_delta(self, prev_tensor: EmotionTensor, curr_tensor: EmotionTensor) -> float:
        """Passive scoring: if user became more positive, strategy worked."""
        valence_delta = curr_tensor.valence - prev_tensor.valence
        intensity_drop = prev_tensor.intensity - curr_tensor.intensity
        score_delta = (valence_delta * 0.6) + (intensity_drop * 0.3)
        return round(score_delta, 3)
