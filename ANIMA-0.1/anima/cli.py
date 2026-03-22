"""
ANIMA CLI
---------
Usage:
  anima chat   --user <id> --key <gemini_key> [--model gemini-2.0-flash]
  anima stats  --user <id> --key <gemini_key>
  anima export --user <id> --key <gemini_key> [--out soul.json]
  anima import --user <id> --key <gemini_key> --file soul.json [--merge]
  anima reset  --user <id> --key <gemini_key> --confirm
"""
import argparse
import sys
import os
import json


def _make_anima(args):
    from anima import ANIMA
    api_key = args.key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[ANIMA] ERROR: No API key. Use --key or set GEMINI_API_KEY env var.")
        sys.exit(1)
    return ANIMA(api_key=api_key, user_id=args.user, model=getattr(args, "model", "gemini-2.0-flash"))


def cmd_chat(args):
    ai = _make_anima(args)
    stats = ai.get_stats()
    print(f"\n  ██████╗  ███╗  ██╗██╗███╗   ███╗ ██████╗")
    print(f"  ██╔══██╗████╗  ██║██║████╗ ████║██╔══██╗")
    print(f"  ███████║██╔██╗ ██║██║██╔████╔██║███████║")
    print(f"  ██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══██║")
    print(f"  ██║  ██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║")
    print(f"  ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝")
    print(f"  Adaptive Neural Identity & Memory Architecture")
    print(f"  by Spyder Group  |  v0.1.0\n")
    print(f"  User: {args.user}  |  RDS: {stats['relationship_depth_score']:.1f}/100  |  Mode: {stats['mode']}")
    print(f"  Messages: {stats['total_messages']}  |  Strategies: {stats['strategies_learned']}  |  Traits: {len(stats['earned_traits'])}\n")
    print("  Type /quit to exit  |  /stats for live stats  |  /export to save soul\n")
    print("─" * 60)

    while True:
        try:
            user_input = input("\nYou → ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[ANIMA] Goodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("[ANIMA] Session ended. Your soul has been saved.")
            break
        if user_input.lower() == "/stats":
            s = ai.get_stats()
            print(json.dumps(s, indent=2))
            continue
        if user_input.lower().startswith("/export"):
            path = ai.export_soul()
            print(f"[ANIMA] Soul exported → {path}")
            continue

        result = ai.chat(user_input)
        emotion = result["emotion"]
        arc_flag = " Arc" if result["arc_warning"] else ""
        print(f"\nANIMA [{emotion['primary']} | RDS {result['rds']:.0f} | {result['mode']}{arc_flag}]")
        print(f"  {result['response']}\n")


def cmd_stats(args):
    ai = _make_anima(args)
    print(json.dumps(ai.get_stats(), indent=2))


def cmd_export(args):
    ai = _make_anima(args)
    out = getattr(args, "out", None)
    path = ai.export_soul(out)
    print(f"[ANIMA] Soul exported → {path}")


def cmd_import(args):
    ai = _make_anima(args)
    merge = getattr(args, "merge", False)
    ai.import_soul(args.file, merge=merge)
    print(f"[ANIMA] Soul imported from {args.file} (merge={merge})")


def cmd_reset(args):
    confirm = getattr(args, "confirm", False)
    ai = _make_anima(args)
    ai.reset(confirm=confirm)
    print(f"[ANIMA] All memory for user '{args.user}' has been wiped.")


def main():
    parser = argparse.ArgumentParser(
        prog="anima",
        description="ANIMA – Adaptive Neural Identity & Memory Architecture"
    )
    sub = parser.add_subparsers(dest="command")

    def add_common(p):
        p.add_argument("--user", required=True, help="User ID")
        p.add_argument("--key", default=None, help="Gemini API key (or set GEMINI_API_KEY)")
        p.add_argument("--model", default="gemini-2.5-flash-lite", help="Gemini model name")

    chat_p = sub.add_parser("chat", help="Start an ANIMA chat session")
    add_common(chat_p)

    stats_p = sub.add_parser("stats", help="Show ANIMA stats for a user")
    add_common(stats_p)

    export_p = sub.add_parser("export", help="Export soul to JSON file")
    add_common(export_p)
    export_p.add_argument("--out", default=None, help="Output file path")

    import_p = sub.add_parser("import", help="Import soul from JSON file")
    add_common(import_p)
    import_p.add_argument("--file", required=True, help="Path to soul export JSON")
    import_p.add_argument("--merge", action="store_true", help="Merge instead of overwrite")

    reset_p = sub.add_parser("reset", help="Wipe all memory for a user")
    add_common(reset_p)
    reset_p.add_argument("--confirm", action="store_true", help="Required to confirm reset")

    args = parser.parse_args()
    commands = {
        "chat": cmd_chat,
        "stats": cmd_stats,
        "export": cmd_export,
        "import": cmd_import,
        "reset": cmd_reset,
    }
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
