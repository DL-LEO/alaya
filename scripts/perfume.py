# Alaya · Xunxi (Cultivation / Habit-Perfume)
# Thin orchestrator that delegates to knowledge, memory, and persona modules.
#
# Usage:
#   python scripts/perfume.py --level 1 --cards card1.md,card2.md --persona Feynman \
#     --topic "quantum" --turns 3 --tags "physics,curiosity" --mood "好奇" \
#     --summary "one line" --alaya DIR --wiki DIR
#
#   python scripts/perfume.py --level 2 --alaya DIR --wiki DIR
#   python scripts/perfume.py --level 3 --alaya DIR --wiki DIR
#   python scripts/perfume.py --sleep-check --alaya DIR
#   python scripts/perfume.py --wake "keyword" --alaya DIR --wiki DIR

import json, os, sys
from datetime import datetime

_ALAYA_TODAY = os.environ.get("ALAYA_TODAY")


def _today() -> datetime:
    if _ALAYA_TODAY:
        return datetime.strptime(_ALAYA_TODAY, "%Y-%m-%d")
    return datetime.now()


def _today_str() -> str:
    return _today().strftime("%Y-%m-%d")


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from perfume_knowledge import boost_cards, decay_all, wake_seeds, sleep_check as check_sleep
from perfume_memory import update_ambient, migrate_from_manas, write_history
from perfume_persona import update_affinity, decay_affinity


def parse_args():
    args = sys.argv[1:]
    result = {
        "level": None, "cards": [], "persona": None,
        "topic": None, "turns": 0, "tags": [],
        "mood": "", "summary": "",
        "sleep_check": False, "wake": None,
        "alaya_dir": "alaya", "wiki_dir": "wiki"
    }

    i = 0
    while i < len(args):
        if args[i] == "--level":
            i += 1
            if i < len(args):
                try:
                    result["level"] = int(args[i])
                except ValueError:
                    print(f"Invalid level: {args[i]}")
                    sys.exit(1)
        elif args[i] == "--cards":
            i += 1
            if i < len(args) and not args[i].startswith("--"):
                result["cards"] = [c.strip() for c in args[i].split(",") if c.strip()]
        elif args[i] == "--persona":
            i += 1
            result["persona"] = args[i] if i < len(args) else None
        elif args[i] == "--topic":
            i += 1
            result["topic"] = args[i] if i < len(args) else None
        elif args[i] == "--turns":
            i += 1
            if i < len(args):
                try:
                    result["turns"] = int(args[i])
                except ValueError:
                    print(f"Invalid turns: {args[i]}")
                    sys.exit(1)
        elif args[i] == "--tags":
            i += 1
            if i < len(args) and not args[i].startswith("--"):
                result["tags"] = [t.strip() for t in args[i].split(",") if t.strip()]
        elif args[i] == "--mood":
            i += 1
            result["mood"] = args[i] if i < len(args) else ""
        elif args[i] == "--summary":
            i += 1
            result["summary"] = args[i] if i < len(args) else ""
        elif args[i] == "--alaya":
            i += 1
            result["alaya_dir"] = args[i] if i < len(args) else result["alaya_dir"]
        elif args[i] == "--wiki":
            i += 1
            result["wiki_dir"] = args[i] if i < len(args) else result["wiki_dir"]
        elif args[i] == "--sleep-check":
            result["sleep_check"] = True
        elif args[i] == "--wake":
            i += 1
            result["wake"] = args[i] if i < len(args) else None
        else:
            if result["alaya_dir"] == "alaya":
                result["alaya_dir"] = args[i]
            elif result["wiki_dir"] == "wiki":
                result["wiki_dir"] = args[i]
        i += 1

    return result


def _migrate_config(config):
    """Auto-migrate flat config (v1.7) to nested structure (v1.8+)."""
    if "knowledge" in config:
        return config

    knowledge = {
        "version": config.get("version", "1.7.0"),
        "top_k": config.pop("top_k", 3),
        "max_cards": config.pop("max_cards", 5),
        "half_life_default": config.pop("half_life_default", 30),
        "strength_decay": config.pop("strength_decay", 0.977),
        "sleep_threshold": config.pop("sleep_threshold", 0.1),
        "wake_strength": config.pop("wake_strength", 0.5),
        "sleep_notification_threshold": config.pop("sleep_notification_threshold", 30),
        "dirty_categories": config.pop("dirty_categories", []),
        "sleep_counter": config.pop("sleep_counter", 0)
    }

    persona = {
        "version": config.get("version", "1.7.0"),
        "max_cards_per_persona": config.pop("max_cards_per_persona", 5),
        "affinity_decay": config.pop("affinity_decay", 0.992)
    }

    memory = {
        "version": "1.0.0",
        "hot_limit": 5,
        "cold_limit": 45
    }

    config["knowledge"] = knowledge
    config["memory"] = memory
    config["persona"] = persona
    return config


def load_config(alaya_dir):
    """Load config with auto-migration."""
    config_path = os.path.join(alaya_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    config = _migrate_config(config)

    moved = migrate_from_manas(alaya_dir)
    if moved > 0:
        print(f"Migrated {moved} history file(s) from manas/ to memory/")
        save_config(alaya_dir, config)

    return config


def save_config(alaya_dir, config):
    config_path = os.path.join(alaya_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _sub(config, system):
    """Get subsystem config dict."""
    return config.get(system, {})


def level_1(alaya_dir, wiki_dir, args, config):
    """Level 1: Auto-update after every reply. Knowledge boost + mechanical ambient only.

    Semantic memory fields (recent_themes, open_threads, user_style_notes,
    persona history) are handled by LLM at session boundary with user confirmation.
    """
    today = _today_str()
    kcfg = _sub(config, "knowledge")

    # Knowledge: boost cited cards
    updated, dirty = boost_cards(wiki_dir, args["cards"], kcfg, today)
    if dirty:
        kcfg["dirty_categories"] = dirty

    # Persona: update affinity (mechanical increment, auto)
    if args["persona"]:
        manas_dir = os.path.join(alaya_dir, "manas")
        update_affinity(manas_dir, args["persona"])

    # Memory: write persona history stub (mechanical layer)
    if args["persona"]:
        memory_dir = os.path.join(alaya_dir, "memory")
        topic = args.get("topic") or "auto-maintenance"
        entry = {
            "date": today,
            "topic": topic,
            "tags": args.get("tags", []),
            "summary": "Level 1 maintenance — affinity updated.",
            "key_insights": [],
            "cards_cited": args.get("cards", []),
            "turns": args.get("turns", 1),
        }
        hl = config.get("memory", {}).get("hot_limit", 5)
        cl = config.get("memory", {}).get("cold_limit", 45)
        write_history(memory_dir, args["persona"], entry, hot_limit=hl, cold_limit=cl)

    # Memory: mechanical only — mood + attention decay/boost
    if args.get("mood") or args.get("tags"):
        memory_dir = os.path.join(alaya_dir, "memory")
        update_ambient(memory_dir, mood=args.get("mood"), tags=args.get("tags"))

    save_config(alaya_dir, config)
    print(f"Level 1 complete: {updated} cards updated")


def level_2(alaya_dir, wiki_dir, config):
    """Level 2: Full xunxi — decay, affinity decay, sleep check."""
    kcfg = _sub(config, "knowledge")
    pcfg = _sub(config, "persona")
    today = _today()
    today_str = today.strftime("%Y-%m-%d")

    last_xunxi = config.get("last_xunxi_time", "")
    xunxi_days = 1
    if last_xunxi:
        try:
            last_time = datetime.strptime(last_xunxi, "%Y-%m-%d")
            xunxi_days = max(1, (today - last_time).days)
        except ValueError:
            pass

    # Knowledge: decay all card strengths
    total, decayed, slept = decay_all(wiki_dir, kcfg, today)

    # Persona: decay all affinity scores
    manas_dir = os.path.join(alaya_dir, "manas")
    decay_affinity(manas_dir, pcfg.get("affinity_decay", 0.992), xunxi_days)

    kcfg["sleep_counter"] = kcfg.get("sleep_counter", 0) + slept
    config["last_xunxi_time"] = today_str
    save_config(alaya_dir, config)

    print(f"Level 2 complete: {total} cards checked, {decayed} decayed, {slept} newly sleeping")


def level_3(alaya_dir, wiki_dir, config):
    """Level 3: Backfill — run level 2 only if stale."""
    last = config.get("last_xunxi_time", "")
    if last:
        try:
            last_time = datetime.strptime(last, "%Y-%m-%d")
            hours = (_today() - last_time).total_seconds() / 3600
            if hours < 24:
                print(f"Level 3 skipped: last xunxi was {hours:.0f} hours ago (< 24h)")
                return
        except ValueError:
            pass

    print("Level 3: stale xunxi detected, running full update...")
    level_2(alaya_dir, wiki_dir, config)


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args["alaya_dir"])

    if args["sleep_check"]:
        kcfg = _sub(config, "knowledge")
        should_notify, counter, threshold = check_sleep(kcfg)
        if should_notify:
            print(f"Sleep notification: {counter} seeds have entered sleep (threshold: {threshold})")
            print("  Consider reviewing dormant knowledge cards.")
            kcfg["sleep_counter"] = 0
            save_config(args["alaya_dir"], config)
        else:
            print(f"Sleep counter: {counter}/{threshold} — no notification needed")

    elif args["wake"]:
        kcfg = _sub(config, "knowledge")
        today = _today_str()
        woken = wake_seeds(args["wiki_dir"], args["wake"], kcfg, today)
        if woken == 0:
            print(f"No dormant seeds matched '{args['wake']}'")
        else:
            kcfg["sleep_counter"] = max(0, kcfg.get("sleep_counter", 0) - woken)
            save_config(args["alaya_dir"], config)

    elif args["level"] == 1:
        level_1(args["alaya_dir"], args["wiki_dir"], args, config)
    elif args["level"] == 2:
        level_2(args["alaya_dir"], args["wiki_dir"], config)
    elif args["level"] == 3:
        level_3(args["alaya_dir"], args["wiki_dir"], config)
    else:
        print("Usage:")
        print("  python scripts/perfume.py --level 1 --cards c1.md,c2.md [--persona Name]")
        print("    [--mood \"开心\"] [--tags tag1,tag2] --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --level 2 --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --level 3 --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --sleep-check --alaya DIR")
        print("  python scripts/perfume.py --wake \"keyword\" --alaya DIR --wiki DIR")
        sys.exit(1)
