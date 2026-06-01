# Alaya · Knowledge System Operations
# Card strength boost, decay, sleep tracking, dirty category detection.

import os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import read_frontmatter, get_field, get_field_float, set_field, rebuild_content, find_card

CORE_THRESHOLD = 0.5


def boost_cards(wiki_dir, cited_cards, kcfg, today):
    """Boost strength of cited cards. Returns (updated_count, dirty_categories)."""
    updated = 0
    dirty = list(kcfg.get('dirty_categories', []))

    for card_path in cited_cards:
        result = _read_card(wiki_dir, card_path)
        if result is None:
            continue
        content, yaml_str, dash, fpath = result

        old_strength = get_field_float(yaml_str, "strength") or 0.5
        strength = min(1.0, old_strength + 0.03)

        # Mark the card's category as dirty for index rebuild
        cat_dir = os.path.basename(os.path.dirname(fpath))
        if cat_dir not in dirty:
            dirty.append(cat_dir)

        count_str = get_field(yaml_str, "activation_count")
        count = int(count_str) + 1 if count_str else 1

        yaml_str = set_field(yaml_str, "strength", f"{strength:.2f}")
        yaml_str = set_field(yaml_str, "activation_count", str(count))
        yaml_str = set_field(yaml_str, "last_activated", today)

        new_content = rebuild_content(yaml_str, dash, content)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        updated += 1

    return updated, dirty


def decay_all(wiki_dir, kcfg, today):
    """Decay all card strengths. Returns (total, decayed, newly_sleeping)."""
    decay = kcfg.get("strength_decay", 0.977)
    sleep_threshold = kcfg.get("sleep_threshold", 0.1)

    decayed = 0
    slept = 0
    total = 0

    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith(".md") or fname in ("index.md", "log.md", "_category.md"):
                continue

            fpath = os.path.join(root, fname)
            result = read_frontmatter(fpath)
            if result is None:
                continue

            content, yaml_str, dash = result

            strength = get_field_float(yaml_str, "strength")
            if strength is None:
                continue
            total += 1

            last_activated = get_field(yaml_str, "last_activated")
            if last_activated:
                try:
                    last_date = datetime.strptime(last_activated, "%Y-%m-%d")
                    days = (today - last_date).days
                except ValueError:
                    days = 0
            else:
                days = 0

            if days > 0:
                new_strength = strength * (decay ** days)
                new_strength = round(new_strength, 4)

                was_awake = strength >= sleep_threshold
                is_sleeping = new_strength < sleep_threshold

                yaml_str = set_field(yaml_str, "strength", f"{new_strength:.4f}")
                decayed += 1

                if was_awake and is_sleeping:
                    slept += 1

            new_content = rebuild_content(yaml_str, dash, content)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)

    return total, decayed, slept


def wake_seeds(wiki_dir, keyword, kcfg, today):
    """Wake dormant seeds matching keyword. Returns woken count."""
    keyword_lower = keyword.lower()
    wake_strength = kcfg.get("wake_strength", 0.5)
    sleep_threshold = kcfg.get("sleep_threshold", 0.1)
    woken = 0

    for root, dirs, files in os.walk(wiki_dir):
        for fname in files:
            if not fname.endswith(".md") or fname in ("index.md", "log.md", "_category.md"):
                continue

            fpath = os.path.join(root, fname)
            result = read_frontmatter(fpath)
            if result is None:
                continue

            content, yaml_str, dash = result

            strength = get_field_float(yaml_str, "strength")
            if strength is None or strength >= sleep_threshold:
                continue

            title = fname.replace(".md", "").lower().replace("-", " ")
            if keyword_lower in title:
                yaml_str = set_field(yaml_str, "strength", str(wake_strength))
                yaml_str = set_field(yaml_str, "last_activated", today)
                new_content = rebuild_content(yaml_str, dash, content)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                woken += 1
                print(f"  Woken: {fname.replace('.md', '')} ({strength:.4f} -> {wake_strength})")

    return woken


def sleep_check(kcfg):
    """Check sleep counter. Returns (should_notify, counter, threshold)."""
    counter = kcfg.get("sleep_counter", 0)
    threshold = kcfg.get("sleep_notification_threshold", 30)
    return counter >= threshold, counter, threshold


def _read_card(wiki_dir, card_path):
    """Read card YAML frontmatter. Returns (content, yaml_str, dash, fpath) or None."""
    if card_path.startswith("wiki/") or card_path.startswith("wiki\\"):
        fpath = os.path.join(os.path.dirname(wiki_dir), card_path)
    elif os.path.exists(os.path.join(wiki_dir, card_path)):
        fpath = os.path.join(wiki_dir, card_path)
    else:
        found = find_card(wiki_dir, card_path.replace('.md', ''))
        if found:
            fpath = found
        else:
            return None

    result = read_frontmatter(fpath)
    if result is None:
        return None
    content, yaml_str, dash = result
    return content, yaml_str, dash, fpath
