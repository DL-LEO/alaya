# Alaya · BI Observer
# Passive pattern observer — no scoring, no ranking, no intervention.
# Usage: python scripts/bi_observer.py [alaya_dir] [--json]

import json, os, sys
from datetime import datetime, timedelta

alaya_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "alaya"
json_out = "--json" in sys.argv

def _days_since(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.now() - d).days
    except (ValueError, TypeError):
        return 999

def _read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def observe(alaya_dir):
    obs = {"persona_activity": [], "affinity_network": [], "dormant": [], "knowledge_gaps": []}
    mn_dir = os.path.join(alaya_dir, "manas")
    mem_dir = os.path.join(alaya_dir, "memory")
    wiki_dir = os.path.join(os.path.dirname(alaya_dir), "wiki")

    if not os.path.exists(mn_dir):
        return obs

    ambient = _read_json(os.path.join(mem_dir, "ambient.json")) or {}

    personas = {}
    history_last_dates = {}
    for fname in sorted(os.listdir(mn_dir)):
        if not fname.endswith(".json") or fname.endswith("_history.json"):
            continue
        data = _read_json(os.path.join(mn_dir, fname))
        if not data:
            continue
        name = data.get("persona", fname.replace(".json", ""))
        personas[name] = data

        hist = _read_json(os.path.join(mem_dir, f"{name}_history.json"))
        if hist and hist.get("hot"):
            last_date = hist["hot"][-1].get("date", "")
            history_last_dates[name] = last_date
            obs["persona_activity"].append({
                "persona": name,
                "recent_topic": hist["hot"][-1].get("topic", ""),
                "recent_mood": hist["hot"][-1].get("mood", ""),
                "hot_count": len(hist.get("hot", [])),
                "cold_count": len(hist.get("cold", [])),
                "last_interaction": last_date
            })
        else:
            history_last_dates[name] = None
            obs["persona_activity"].append({
                "persona": name,
                "recent_topic": "",
                "recent_mood": "",
                "hot_count": 0,
                "cold_count": 0,
                "last_interaction": None
            })

    # Affinity network insights
    for name, data in personas.items():
        aff = data.get("affinity", {})
        for other, v in aff.items():
            if other in personas and name < other:  # dedup pairs
                score_a = v.get("score", 0) if isinstance(v, dict) else v
                score_b = 0
                other_aff = personas[other].get("affinity", {}).get(name, {})
                if isinstance(other_aff, dict):
                    score_b = other_aff.get("score", 0)
                avg = round((score_a + score_b) / 2, 2)
                trend = "mutual_growing" if (score_a > 0.3 and score_b > 0.3) else \
                        "asymmetric" if abs(score_a - score_b) > 0.15 else "neutral"
                obs["affinity_network"].append({
                    "pair": (name, other),
                    "scores": (score_a, score_b),
                    "avg": avg,
                    "trend": trend
                })

    # Dormant persona detection
    for name, last_date in history_last_dates.items():
        days = _days_since(last_date) if last_date else 999
        if days >= 14:
            obs["dormant"].append({
                "persona": name,
                "days_since_last": days,
                "interest_foci": list(personas[name].get("ego_vector", {}).get("interest_foci", {}).keys())[:3]
            })

    # Knowledge gap detection
    if os.path.exists(wiki_dir):
        persona_interests = set()
        for p in personas.values():
            foci = p.get("ego_vector", {}).get("interest_foci", {})
            for k in foci:
                persona_interests.add(k.lower())

        existing_categories = set()
        for entry in os.listdir(wiki_dir):
            if os.path.isdir(os.path.join(wiki_dir, entry)) and not entry.startswith("."):
                existing_categories.add(entry.lower())

        category_card_counts = {}
        for cat in existing_categories:
            cat_dir = os.path.join(wiki_dir, cat)
            cat_file = os.path.join(cat_dir, "_category.md")
            count = 0
            if os.path.exists(cat_file):
                with open(cat_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("- [["):
                            count += 1
            category_card_counts[cat] = count

        for interest in persona_interests:
            matched = [c for c in existing_categories if interest in c or c in interest]
            if not matched:
                obs["knowledge_gaps"].append({
                    "interest_area": interest,
                    "issue": "no_category",
                    "description": f"No wiki category matches persona interest '{interest}'"
                })
            else:
                low_count = [c for c in matched if category_card_counts.get(c, 0) < 5]
                if low_count:
                    obs["knowledge_gaps"].append({
                        "interest_area": interest,
                        "issue": "thin",
                        "categories": low_count,
                        "card_counts": {c: category_card_counts.get(c, 0) for c in low_count}
                    })

    return obs

def print_report(obs):
    print("=" * 60)
    print("  Alaya · BI Observation Report")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if obs["persona_activity"]:
        print("\n── Persona Activity ──")
        for pa in obs["persona_activity"]:
            last = pa["last_interaction"] or "never"
            print(f"  {pa['persona']}: {pa['hot_count']}h/{pa['cold_count']}c | "
                  f"last: {last} | mood: {pa['recent_mood']} | {pa['recent_topic']}")

    if obs["affinity_network"]:
        print("\n── Affinity Network ──")
        for an in obs["affinity_network"]:
            a, b = an["pair"]
            print(f"  {a} ↔ {b}: {an['scores'][0]} / {an['scores'][1]} "
                  f"(avg {an['avg']}, {an['trend']})")

    if obs["dormant"]:
        print("\n── Dormant Personas ──")
        for d in obs["dormant"]:
            interests = ", ".join(d["interest_foci"])
            print(f"  {d['persona']}: {d['days_since_last']}d inactive | interests: {interests}")

    if obs["knowledge_gaps"]:
        print("\n── Knowledge Gaps ──")
        for kg in obs["knowledge_gaps"]:
            if kg["issue"] == "no_category":
                print(f"  [{kg['interest_area']}] No matching wiki category")
            else:
                cats = ", ".join(f"{c}({kg['card_counts'].get(c, 0)} cards)" for c in kg["categories"])
                print(f"  [{kg['interest_area']}] Thin categories: {cats}")

    print("\n" + "─" * 60)
    print("  BI Observer | No scoring · No comparison · No intervention")
    print("─" * 60)

if __name__ == "__main__":
    obs = observe(alaya_dir)
    if json_out:
        print(json.dumps(obs, ensure_ascii=False, indent=2))
    else:
        print_report(obs)
