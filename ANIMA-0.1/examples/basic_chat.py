"""
ANIMA Basic Chat Example
------------------------
Run:
    export GEMINI_API_KEY="your_key_here"
    python examples/basic_chat.py
"""
import os
from anima import ANIMA

api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
ai = ANIMA(api_key=api_key, user_id="demo_user")

@ai.on("emotion_detected")
def on_emotion(tensor, user_id):
    print(f"  [hook] Emotion: {tensor.primary} | valence={tensor.valence:.2f}")

@ai.on("rds_milestone")
def on_milestone(rds, mode_name, user_id):
    print(f"  [hook] Relationship milestone! RDS={rds:.1f} | Mode: {mode_name}")

@ai.on("arc_warning_fired")
def on_arc(arc, predicted_next):
    print(f"  [hook] Arc warning fired: {arc}")

print("ANIMA Basic Chat – type quit to exit\n")
while True:
    msg = input("You: ").strip()
    if msg.lower() in ("quit", "exit"):
        break
    if not msg:
        continue
    result = ai.chat(msg)
    print(f"\nANIMA: {result['response']}\n")
    print(f"  emotion={result['emotion']['primary']} | RDS={result['rds']} | mode={result['mode']}\n")

import json
print("\n=== Session Stats ===")
print(json.dumps(ai.get_stats(), indent=2))
