# Alaya · Memory System Operations
# Interaction history (hot/cold), ambient state (mood, attention), migration.

import json, os, shutil
from datetime import datetime

_ALAYA_TODAY = os.environ.get("ALAYA_TODAY")

def _today_str() -> str:
    if _ALAYA_TODAY:
        return _ALAYA_TODAY
    return datetime.now().strftime("%Y-%m-%d")


def write_history(memory_dir, persona_key, entry, hot_limit=5, cold_limit=45):
    """Write an interaction entry to persona's history file (hot/cold dual-zone).

    persona_key should be the canonical key (JSON filename base, e.g. "feynman").
    Callers should resolve display names via persona_key() in lib/yaml_utils before calling.
    """
    os.makedirs(memory_dir, exist_ok=True)

    history_path = os.path.join(memory_dir, f"{persona_key}_history.json")

    history = {"hot": [], "cold": []}
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as fp:
                loaded = json.load(fp)
                if isinstance(loaded, dict):
                    history = loaded
                elif isinstance(loaded, list):
                    history = {"hot": loaded[-hot_limit:], "cold": []}
        except (json.JSONDecodeError, IOError):
            history = {"hot": [], "cold": []}

    hot = history.get("hot", [])
    cold = history.get("cold", [])
    hot.append(entry)

    if len(hot) > hot_limit:
        oldest = hot.pop(0)
        cold_entry = {
            "date": oldest["date"],
            "topic": oldest["topic"],
            "tags": oldest.get("tags", []),
            "summary": oldest.get("summary", oldest["topic"])
        }
        cold.append(cold_entry)

    cold = cold[-cold_limit:]

    with open(history_path, "w", encoding="utf-8") as fp:
        json.dump({"hot": hot, "cold": cold}, fp, ensure_ascii=False, indent=2)


def _ensure_ambient_fields(ambient):
    """Initialize missing semantic fields for forward compatibility."""
    defaults = {
        "mood_trajectory": [],
        "recent_themes": "",
        "open_threads": [],
        "user_style_notes": "",
        "save_prompt_count": 0
    }
    for key, default in defaults.items():
        if key not in ambient:
            ambient[key] = default
    return ambient


def update_ambient(memory_dir, mood=None, tags=None):
    """
    Mechanical layer only: mood overwrite + trajectory push + tag decay/boost.
    Semantic fields (recent_themes, open_threads, user_style_notes) are
    preserved as-is — the LLM writes those directly at session boundary.
    """
    os.makedirs(memory_dir, exist_ok=True)
    ambient_path = os.path.join(memory_dir, "ambient.json")

    ambient = {"recent_mood": "", "recent_attention": {}}
    if os.path.exists(ambient_path):
        try:
            with open(ambient_path, "r", encoding="utf-8") as f:
                ambient = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    ambient = _ensure_ambient_fields(ambient)

    # Global cap: ensure trajectory never exceeds 25 entries
    traj = ambient.get("mood_trajectory", [])
    if len(traj) > 25:
        ambient["mood_trajectory"] = traj[-25:]

    today = _today_str()

    # Mood: overwrite recent_mood + push to trajectory (cap 3)
    if mood:
        ambient["recent_mood"] = mood
        trajectory = ambient.get("mood_trajectory", [])
        trajectory.append({"mood": mood, "date": today})
        if len(trajectory) > 3:
            trajectory = trajectory[-3:]
        ambient["mood_trajectory"] = trajectory

    # Attention: decay existing + boost new tags
    attention = ambient.get("recent_attention", {})

    for tag in attention:
        attention[tag] = round(attention[tag] * 0.7, 2)

    if tags:
        for tag in tags:
            tag = tag.strip()
            if tag:
                attention[tag] = round(min(1.0, attention.get(tag, 0.0) + 0.3), 2)

    attention = {k: v for k, v in attention.items() if v >= 0.1}
    ambient["recent_attention"] = attention

    with open(ambient_path, "w", encoding="utf-8") as f:
        json.dump(ambient, f, ensure_ascii=False, indent=2)


def migrate_from_manas(alaya_dir):
    """Move history files from manas/ to memory/ (one-time migration). Returns count moved."""
    manas_dir = os.path.join(alaya_dir, "manas")
    memory_dir = os.path.join(alaya_dir, "memory")

    if not os.path.exists(manas_dir):
        return 0

    moved = 0
    for f in os.listdir(manas_dir):
        if f.endswith("_history.json"):
            src = os.path.join(manas_dir, f)
            dst = os.path.join(memory_dir, f)
            if not os.path.exists(dst):
                os.makedirs(memory_dir, exist_ok=True)
                shutil.move(src, dst)
                moved += 1

    return moved
