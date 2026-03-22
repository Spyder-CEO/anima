<div align="center">

<pre>
  ██████╗  ███╗  ██╗██╗███╗   ███╗ ██████╗
  ██╔══██╗████╗  ██║██║████╗ ████║██╔══██╗
  ███████║██╔██╗ ██║██║██╔████╔██║███████║
  ██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══██║
  ██║  ██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
</pre>

**Adaptive Neural Identity & Memory Architecture**

*The emotional intelligence layer your LLM never had.*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gemini](https://img.shields.io/badge/Powered%20by-Gemini-4285F4.svg)](https://ai.google.dev/)
[![Made by Spyder Group](https://img.shields.io/badge/Made%20by-Spyder%20Group-black.svg)](https://github.com/SpyderGroup)

</div>

---

## What is ANIMA?

ANIMA gives any LLM a **persistent emotional identity**. It detects how users feel, learns personalised response strategies, predicts emotional breakdowns before they happen, and deepens its relationship with every single message.

```
Session 1 (stranger):  "Can you explain transformers?"
→ Generic technical explanation.

Session 47 (trusted):  "Can you explain transformers?"
→ "You asked something similar last month when you were stuck on
   your thesis — remember we used the restaurant analogy? Same
   idea here, but let's go deeper since you've grown since then."
```

No vector databases. No cloud dependencies. Pure Python. Works with any LLM.

---

## Features

| Feature | Description |
|---|---|
| **6D Emotion Tensor** | Detects primary emotion + valence, arousal, dominance, intensity, context |
| **Arc Prediction** | Identifies `curious → stuck → frustrated` patterns and intervenes early |
| **Relationship Depth Score** | 0-100 score unlocks 4 communication modes as trust deepens |
| **Self-Rewriting Strategies** | LLM writes and rewrites its own system prompts per emotional state |
| **Evolving Persona** | AI earns relationship-specific traits like `uses_analogies_for_alice` |
| **Soul Portability** | Export/import your soul across any model or instance |
| **Plugin Hook API** | `@ai.on("emotion_detected")` — attach any callback to any event |
| **Zero-DB Architecture** | Three JSON files. No Postgres, no Redis, no Pinecone. |

---

## Quick Start

### Install

```bash
pip install anima-llm
```

Or from source:
```bash
git clone https://github.com/SpyderGroup/anima.git
cd anima
pip install -e .
```

### Chat via CLI

```bash
export GEMINI_API_KEY="your_key_here"
anima chat --user alice
```

### Use in Python

```python
from anima import ANIMA

ai = ANIMA(api_key="YOUR_GEMINI_API_KEY", user_id="alice")

result = ai.chat("I've been struggling with this bug for hours and I give up")
print(result["response"])
# → "Let's slow down. Hours on one bug is genuinely exhausting — before
#    anything else, tell me what you've already tried. Sometimes just
#    saying it out loud shakes something loose."

print(result["emotion"]["primary"])   # → "frustrated"
print(result["rds"])                   # → 12.3
print(result["mode"])                  # → "Familiar"
print(result["arc_warning"])           # → True (predicted burnout arc)
```

---

## How It Works

```
User message
     │
     ▼
┌─────────────────┐     ┌──────────────────┐
│  Emotion Tensor  │────▶│   Arc Predictor   │
│  Detector (6D)   │     │  (sequence match) │
└─────────────────┘     └────────┬─────────┘
                                  │
     ┌────────────────────────────▼──────────┐
     │           Strategy Manager             │
     │  exact key → fallback → generate new  │
     │  score strategies passively each turn │
     │  rewrite if score drops below 2.2     │
     └────────────────────────────┬──────────┘
                                  │
     ┌────────────────────────────▼──────────┐
     │         Relationship Engine            │
     │  RDS += f(intensity, valence)          │
     │  unlocks: Formal→Familiar→Trusted→Deep│
     └────────────────────────────┬──────────┘
                                  │
     ┌────────────────────────────▼──────────┐
     │          System Prompt Builder         │
     │  strategy + mode + arc + persona       │
     └────────────────────────────┬──────────┘
                                  │
                              Gemini API
                                  │
                             Response + Metadata
```

---

## Storage Layout

ANIMA stores all data in `~/.anima/users/<user_id>/`:

```
~/.anima/users/alice/
├── soul.json        ← deep profile, persona, arc patterns, RDS
├── state.json       ← live session state, emotion history
└── strategies.json  ← self-written response playbooks, scored + versioned
```

### soul.json (example)
```json
{
  "user_id": "alice",
  "relationship_depth_score": 63.4,
  "llm_persona": {
    "communication_style": "direct-but-warm",
    "earned_traits": ["uses_analogies_for_alice", "skips_basics"]
  },
  "arc_patterns": {
    "curious → confused → frustrated": 4
  }
}
```

### strategies.json (example)
```json
{
  "frustrated:technical": {
    "prompt": "Acknowledge effort first. Ask one clarifying question. Break the problem into smaller parts. Never suggest starting over unless explicitly asked.",
    "score": 4.3,
    "uses": 12,
    "version": 2
  }
}
```

---

## Plugin Hook API

```python
from anima import ANIMA

ai = ANIMA(api_key="...", user_id="bob")

@ai.on("emotion_detected")
def on_emotion(tensor, user_id):
    if tensor.primary == "frustrated" and tensor.intensity > 0.8:
        send_alert_to_human_support(user_id)

@ai.on("rds_milestone")
def on_milestone(rds, mode_name, user_id):
    award_loyalty_badge(user_id, mode_name)

@ai.on("arc_warning_fired")
def on_arc(arc, predicted_next):
    log_to_analytics(arc)

@ai.on("response_generated")
def on_response(response, metadata):
    save_to_database(response, metadata)
```

**All events:**

| Event | Payload |
|---|---|
| `emotion_detected` | `tensor, user_id` |
| `strategy_generated` | `key, prompt` |
| `strategy_rewritten` | `key, old_prompt, new_prompt` |
| `arc_warning_fired` | `arc, predicted_next` |
| `rds_milestone` | `rds, mode_name, user_id` |
| `session_started` | `session_id, user_id` |
| `response_generated` | `response, metadata` |

---

## Soul Export / Import

Take your emotional identity anywhere:

```bash
# Export
anima export --user alice --out alice_soul.json

# Import to a different instance (e.g. self-hosted)
anima import --user alice --file alice_soul.json --merge
```

```python
# In Python
ai.export_soul("alice_soul.json")
ai.import_soul("alice_soul.json", merge=True)
```

---

## CLI Reference

```bash
anima chat   --user <id> --key <key>              # Interactive chat
anima stats  --user <id> --key <key>              # Print soul stats
anima export --user <id> --key <key> [--out path] # Export soul
anima import --user <id> --key <key> --file path  # Import soul
anima reset  --user <id> --key <key> --confirm    # Wipe memory
```

In-chat commands: `/stats` `/export` `/quit`

---

## Relationship Depth Modes

| RDS Range | Mode | Behaviour |
|---|---|---|
| 0 – 20 | **Formal** | Careful, thorough, no assumptions |
| 20 – 45 | **Familiar** | Warm, references past topics |
| 45 – 70 | **Trusted** | Challenges user, uses patterns |
| 70 – 100 | **Deep** | Fully candid, earned humor, peer-level |

---

## Roadmap

- [ ] v0.2 – OpenAI / Anthropic / Ollama adapters
- [ ] v0.3 – Multi-user federated wisdom layer (opt-in strategy sharing)
- [ ] v0.4 – REST API server mode (`anima serve`)
- [ ] v0.5 – Web dashboard for soul visualisation
- [ ] v1.0 – Embedding-based strategy clustering for fuzzy lookup

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

```bash
git clone https://github.com/SpyderGroup/anima.git
pip install -e ".[dev]"
```

---

## Built by

<div align="center">

**Spyder Group**
*Building foundational AI infrastructure.*

· [Website](https://spyderglobalgroup.com)

</div>

---

<div align="center">
<sub>MIT Licensed · Made with intent</sub>
</div>
