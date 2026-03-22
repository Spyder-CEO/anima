"""
ANIMA – Soul Export / Import
Portable soul_export.json that works across any LLM or ANIMA instance.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


EXPORT_VERSION = "anima-soul-v1"


def export_soul(memory, output_path: Optional[str] = None) -> str:
    """Export soul + strategies to a portable JSON file. Returns file path."""
    soul = memory.get_soul()
    strategies = memory.get_strategies()
    export_data = {
        "anima_export_version": EXPORT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "soul": soul,
        "strategies": strategies
    }
    if output_path is None:
        output_path = str(Path.cwd() / f"soul_{memory.user_id}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    return output_path


def import_soul(memory, import_path: str, merge: bool = False):
    """
    Import a soul export file.
    merge=True: keep existing strategies and merge (don't overwrite better ones)
    merge=False: full overwrite
    """
    with open(import_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("anima_export_version") != EXPORT_VERSION:
        raise ValueError(
            f"Incompatible export version: {data.get('anima_export_version')}. "
            f"Expected {EXPORT_VERSION}."
        )

    imported_soul = data.get("soul", {})
    imported_strategies = data.get("strategies", {})

    if merge:
        existing_strategies = memory.get_strategies()
        for key, imported_entry in imported_strategies.items():
            existing = existing_strategies.get(key)
            if existing is None or imported_entry.get("score", 3.0) > existing.get("score", 3.0):
                existing_strategies[key] = imported_entry
        memory._write(memory._strategies_path, existing_strategies)
        existing_soul = memory.get_soul()
        for key in ["llm_persona", "user_profile", "arc_patterns"]:
            if key in imported_soul:
                existing_soul[key] = imported_soul[key]
        memory._write(memory._soul_path, existing_soul)
    else:
        imported_soul["user_id"] = memory.user_id
        memory._write(memory._soul_path, imported_soul)
        memory._write(memory._strategies_path, imported_strategies)

    return True
