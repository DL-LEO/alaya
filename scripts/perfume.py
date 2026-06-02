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
from perfume_memory import update_ambient, migrate_from_manas, write_history, _ensure_ambient_fields
from perfume_persona import update_affinity, decay_affinity
import bi_observer


def parse_args():
    args = sys.argv[1:]
    result = {
        "level": None, "cards": [], "persona": None,
        "topic": None, "turns": 0, "tags": [],
        "mood": "", "summary": "",
        "sleep_check": False, "wake": None,
        "alaya_dir": "alaya", "wiki_dir": "wiki",
        "ambient": None, "history": None,
        "affinity_increment": 0.01
    }

    i = 0
    while i < len(args):
        if args[i] == "--level":
            i += 1
            if i < len(args):
                val = args[i]
                if val == "save":
                    result["level"] = "save"
                else:
                    try:
                        result["level"] = int(val)
                    except ValueError:
                        print(f"Invalid level: {val}")
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
        elif args[i] == "--ambient":
            i += 1
            result["ambient"] = args[i] if i < len(args) else None
        elif args[i] == "--history":
            i += 1
            result["history"] = args[i] if i < len(args) else None
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
        elif args[i] == "--affinity-increment":
            i += 1
            if i < len(args):
                try:
                    result["affinity_increment"] = float(args[i])
                except ValueError:
                    print(f"Invalid affinity increment: {args[i]}")
                    sys.exit(1)
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


# ── Reminder frequency control ──────────────────────────────────────

def _filter_by_reminder_tracking(items, config, today_str):
    """Filter health items so the same reminder isn't over-shown.

    Rules:
      - Never shown before → show
      - Shown <1 day ago  → skip (24h quiet)
      - Shown <7 days ago and already shown ≥3 times → skip
      - Otherwise → show
    """
    tracking = config.get("reminder_tracking", {})
    filtered = []

    for item in items:
        key = item["type"]
        entry = tracking.get(key, {"last_shown": None, "count": 0})

        if entry.get("last_shown") is None:
            filtered.append(item)
            continue

        try:
            last = datetime.strptime(entry["last_shown"], "%Y-%m-%d")
            today = datetime.strptime(today_str, "%Y-%m-%d")
            days_since = (today - last).days
        except (ValueError, TypeError):
            days_since = 999

        if days_since < 1:
            continue
        if 1 <= days_since < 7 and entry.get("count", 0) >= 3:
            continue

        filtered.append(item)

    return filtered


def _update_reminder_tracking(items, config, today_str):
    """Update reminder tracking after items have been shown."""
    tracking = config.get("reminder_tracking", {})

    for item in items:
        key = item["type"]
        entry = tracking.get(key, {"last_shown": None, "count": 0})

        # Reset count if >7 days since last show
        if entry.get("last_shown") is not None:
            try:
                last = datetime.strptime(entry["last_shown"], "%Y-%m-%d")
                today = datetime.strptime(today_str, "%Y-%m-%d")
                if (today - last).days >= 7:
                    entry["count"] = 0
            except (ValueError, TypeError):
                pass

        entry["last_shown"] = today_str
        entry["count"] = entry.get("count", 0) + 1
        tracking[key] = entry

    config["reminder_tracking"] = tracking


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
    # --affinity-increment controls the scenario:
    #   0.01 (default) = co-chat; 0.02 = same card cited; 0.03 = cite peer's seed
    if args["persona"]:
        manas_dir = os.path.join(alaya_dir, "manas")
        update_affinity(manas_dir, args["persona"], args.get("affinity_increment", 0.01))

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


def level_save(alaya_dir, wiki_dir, args, config):
    """--level save: Atomic session-boundary save for Steps 3-5 of the protocol.

    Takes structured semantic fields (--ambient JSON) and optional persona history
    (--history JSON), writes both, runs BI observer, and marks protocol checklist.
    Designed to replace three manual LLM steps with one script call.
    """
    today = _today_str()
    persona = args.get("persona")
    if not persona:
        print("Error: --persona is required for --level save")
        sys.exit(1)

    memory_dir = os.path.join(alaya_dir, "memory")
    os.makedirs(memory_dir, exist_ok=True)

    # ---- Step 3: Write ambient.json semantic fields ----
    ambient_json = args.get("ambient")
    ambient_path = os.path.join(memory_dir, "ambient.json")
    existing = {}
    if os.path.exists(ambient_path):
        try:
            with open(ambient_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    if ambient_json:
        try:
            semantic = json.loads(ambient_json)
        except json.JSONDecodeError as e:
            print(f"Error: --ambient is not valid JSON: {e}")
            sys.exit(1)

        # Merge semantic fields into existing (preserving mechanical fields)
        existing["recent_themes"] = semantic.get("recent_themes", existing.get("recent_themes", ""))
        existing["open_threads"] = semantic.get("open_threads", existing.get("open_threads", []))
        existing["user_style_notes"] = semantic.get("user_style_notes", existing.get("user_style_notes", ""))
        existing = _ensure_ambient_fields(existing)

        with open(ambient_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  [Step 3] Ambient semantic fields written")
    else:
        print(f"  [Step 3] --ambient not provided, skipping semantic fields")

    # ---- Step 4: Write persona history ----
    history_json = args.get("history")
    hl = config.get("memory", {}).get("hot_limit", 5)
    cl = config.get("memory", {}).get("cold_limit", 45)

    if history_json:
        try:
            entry = json.loads(history_json)
        except json.JSONDecodeError as e:
            print(f"Error: --history is not valid JSON: {e}")
            sys.exit(1)

        write_history(memory_dir, persona, entry, hot_limit=hl, cold_limit=cl)
        print(f"  [Step 4] History written for '{persona}'")
    else:
        # Minimal fallback entry
        entry = {
            "date": today,
            "topic": args.get("topic") or "session-end",
            "tags": args.get("tags", []),
            "mood": args.get("mood", ""),
            "summary": args.get("summary", "Session end — automatic save"),
            "key_insights": [],
            "cards_cited": args.get("cards", []),
            "turns": args.get("turns", 0),
        }
        write_history(memory_dir, persona, entry, hot_limit=hl, cold_limit=cl)
        print(f"  [Step 4] Minimal history written for '{persona}'")

    # ---- Step 5: BI Observer pass + System health ----
    try:
        obs = bi_observer.observe(alaya_dir)
        findings = []

        for d in obs.get("dormant", []):
            findings.append({
                "type": "dormant_persona",
                "persona": d["persona"],
                "detail": f"{d['days_since_last']}d inactive — interests: {', '.join(d['interest_foci'][:3])}"
            })

        for kg in obs.get("knowledge_gaps", []):
            if kg["issue"] == "no_category":
                findings.append({
                    "type": "knowledge_gap",
                    "interest": kg["interest_area"],
                    "detail": f"No wiki category matches '{kg['interest_area']}'"
                })
            else:
                cats = ", ".join(kg.get("categories", []))
                findings.append({
                    "type": "knowledge_gap_thin",
                    "interest": kg["interest_area"],
                    "detail": f"Thin categories: {cats}"
                })

        for an in obs.get("affinity_network", []):
            if an["trend"] == "asymmetric":
                findings.append({
                    "type": "affinity_asymmetry",
                    "pair": f"{an['pair'][0]} / {an['pair'][1]}",
                    "detail": f"Scores: {an['scores'][0]} vs {an['scores'][1]}"
                })

        # System health check
        health_items = bi_observer.check_health(alaya_dir, wiki_dir, config)
        health_items = _filter_by_reminder_tracking(health_items, config, today)
        if health_items:
            _update_reminder_tracking(health_items, config, today)
            save_config(alaya_dir, config)

        # Write bi_notes.json
        bi_notes_path = os.path.join(alaya_dir, "bi_notes.json")
        existing_notes = []
        if os.path.exists(bi_notes_path):
            try:
                with open(bi_notes_path, "r", encoding="utf-8") as f:
                    existing_notes = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        record = {"date": today, "persona": persona}
        if findings:
            record["findings"] = findings
        if health_items:
            record["system_health"] = health_items

        existing_notes.append(record)
        existing_notes = existing_notes[-20:]
        with open(bi_notes_path, "w", encoding="utf-8") as f:
            json.dump(existing_notes, f, ensure_ascii=False, indent=2)

        # Print summary
        parts = []
        if findings:
            parts.append(f"{len(findings)} observation(s)")
        if health_items:
            parts.append(f"{len(health_items)} health item(s)")
        msg = "; ".join(parts) if parts else "no notable patterns"
        print(f"  [Step 5] BI observer: {msg}")

        # Print health reminders in user-friendly format
        if health_items:
            high_count = sum(1 for h in health_items if h.get("severity") == "high")
            marker = "⚠️" if high_count else "📋"
            print(f"  {marker} alaya系统提醒您：")
            for item in health_items:
                print(f"    • {item['detail']}")
                print(f"      → {item['suggestion']}")

    except Exception as e:
        print(f"  [Step 5] BI observer note: {e}")

    # ---- Protocol checklist ----
    checklist_path = os.path.join(alaya_dir, "_protocol_checklist.json")
    checklist = {}
    if os.path.exists(checklist_path):
        try:
            with open(checklist_path, "r", encoding="utf-8") as f:
                checklist = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    checklist[today] = {
        "ambient_written": bool(ambient_json),
        "history_written": True,
        "bi_observed": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "persona": persona
    }
    with open(checklist_path, "w", encoding="utf-8") as f:
        json.dump(checklist, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Session boundary save complete for '{persona}'")
    print(f"  ambient: {'OK' if ambient_json else '--'} | history: OK | bi: OK")


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
    elif args["level"] == "save":
        level_save(args["alaya_dir"], args["wiki_dir"], args, config)
    elif args["level"] in ("--help", "-h", "help"):
        print("Usage:")
        print("  python scripts/perfume.py --level 1 --cards c1.md,c2.md [--persona Name]")
        print("    [--mood \"开心\"] [--tags tag1,tag2] --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --level 2 --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --level 3 --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --level save --persona Name")
        print("    [--ambient '{\"recent_themes\":\"...\",\"open_threads\":[...]}']")
        print("    [--history '{\"topic\":\"...\",\"tags\":[...],\"summary\":\"...\",\"key_insights\":[...]}']")
        print("    [--cards c1,c2] [--mood \"开心\"] [--tags t1,t2] --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --sleep-check --alaya DIR")
        print("  python scripts/perfume.py --wake \"keyword\" --alaya DIR --wiki DIR")
        print("  python scripts/perfume.py --help")
        sys.exit(0)
    else:
        print(f"Unknown level: {args['level']}")
        print("Run 'python scripts/perfume.py --help' for usage.")
        sys.exit(1)
