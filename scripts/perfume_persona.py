# Alaya · Persona System Operations
# Affinity tracking between personas (increment, decay).

import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import persona_key


def update_affinity(manas_dir, persona_name, increment=0.01):
    """Update affinity: other personas gain affinity toward the active persona.

    persona_name can be any identifier (display name, slug, canonical key).
    It will be resolved to the canonical key internally.
    """
    if not os.path.exists(manas_dir):
        return

    key = persona_key(manas_dir, persona_name)

    for f in os.listdir(manas_dir):
        if not f.endswith(".json") or f.endswith("_history.json"):
            continue
        mpath = os.path.join(manas_dir, f)
        try:
            with open(mpath, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[perfume_persona] WARNING: skipping corrupt JSON: {mpath} ({e})", file=sys.stderr)
            continue

        fkey = f.replace(".json", "")
        if fkey != key:
            aff = data.setdefault("affinity", {})
            if key not in aff:
                aff[key] = {"score": 0.0}
            existing = aff[key]
            if isinstance(existing, dict):
                existing["score"] = round(min(1.0, existing.get("score", 0.0) + increment), 4)
            elif isinstance(existing, (int, float)):
                aff[key] = round(min(1.0, existing + increment), 4)
            with open(mpath, "w", encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)


def decay_affinity(manas_dir, affinity_decay, xunxi_days):
    """Decay all affinity scores across all personas."""
    if not os.path.exists(manas_dir):
        return

    for mf in os.listdir(manas_dir):
        if not mf.endswith(".json") or mf.endswith("_history.json"):
            continue
        mpath = os.path.join(manas_dir, mf)
        try:
            with open(mpath, "r", encoding="utf-8") as f:
                pdata = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[perfume_persona] WARNING: skipping corrupt JSON: {mpath} ({e})", file=sys.stderr)
            continue

        aff = pdata.get("affinity", {})
        for other_name in aff:
            val = aff[other_name]
            if isinstance(val, dict) and "score" in val:
                # Nested format: {"other": {"score": 0.5}}
                val["score"] = round(val["score"] * (affinity_decay ** xunxi_days), 4)
            elif isinstance(val, (int, float)):
                # Flat format: {"alaya": 0.98}
                aff[other_name] = round(val * (affinity_decay ** xunxi_days), 4)

        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(pdata, f, ensure_ascii=False, indent=2)
