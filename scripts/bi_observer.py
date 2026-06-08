# Alaya · BI Observer
# Passive pattern observer — no scoring, no ranking, no intervention.
# Usage: python scripts/bi_observer.py [alaya_dir] [--json]

import json, os, re, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import is_category_file, category_file_for, get_description

alaya_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "alaya"
json_out = "--json" in sys.argv

_ALAYA_TODAY = os.environ.get("ALAYA_TODAY")


def _now():
    """Return current datetime, respecting ALAYA_TODAY for time simulation."""
    if _ALAYA_TODAY:
        return datetime.strptime(_ALAYA_TODAY, "%Y-%m-%d")
    return datetime.now()


def _days_since(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (_now() - d).days
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

    personas = {}          # keyed by canonical key (filename base)
    persona_display = {}   # canonical key -> display name
    history_last_dates = {}
    for fname in sorted(os.listdir(mn_dir)):
        if not fname.endswith(".json") or fname.endswith("_history.json"):
            continue
        data = _read_json(os.path.join(mn_dir, fname))
        if not data:
            continue
        key = fname.replace(".json", "")
        display = data.get("persona", key)
        persona_display[key] = display
        personas[key] = data

        hist = _read_json(os.path.join(mem_dir, f"{key}_history.json"))
        if hist and hist.get("hot"):
            last_date = hist["hot"][-1].get("date", "")
            history_last_dates[key] = last_date
            obs["persona_activity"].append({
                "persona": display,
                "recent_topic": hist["hot"][-1].get("topic", ""),
                "recent_mood": hist["hot"][-1].get("mood", ""),
                "hot_count": len(hist.get("hot", [])),
                "cold_count": len(hist.get("cold", [])),
                "last_interaction": last_date
            })
        else:
            history_last_dates[key] = None
            obs["persona_activity"].append({
                "persona": display,
                "recent_topic": "",
                "recent_mood": "",
                "hot_count": 0,
                "cold_count": 0,
                "last_interaction": None
            })

    # Affinity network insights
    for key, data in personas.items():
        aff = data.get("affinity", {})
        for other_key, v in aff.items():
            if other_key in personas and key < other_key:  # dedup pairs
                score_a = v.get("score", 0) if isinstance(v, dict) else v
                score_b = 0
                other_aff = personas[other_key].get("affinity", {}).get(key, {})
                if isinstance(other_aff, dict):
                    score_b = other_aff.get("score", 0)
                avg = round((score_a + score_b) / 2, 2)
                trend = "mutual_growing" if (score_a > 0.3 and score_b > 0.3) else \
                        "asymmetric" if abs(score_a - score_b) > 0.15 else "neutral"
                obs["affinity_network"].append({
                    "pair": (persona_display[key], persona_display[other_key]),
                    "scores": (score_a, score_b),
                    "avg": avg,
                    "trend": trend
                })

    # Dormant persona detection
    for key, last_date in history_last_dates.items():
        days = _days_since(last_date) if last_date else 999
        if days >= 14:
            obs["dormant"].append({
                "persona": persona_display[key],
                "days_since_last": days,
                "interest_foci": list(personas[key].get("ego_vector", {}).get("interest_foci", {}).keys())[:3]
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
            cat_file = os.path.join(cat_dir, category_file_for(cat))
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

def check_health(alaya_dir, wiki_dir, config):
    """
    System health observation — still passive, no intervention.
    Returns list of dicts, each with: type, severity, detail, suggestion, plus type-specific fields.
    Called by perfume.py --level save.
    """
    items = []
    today = _now()
    today_str = today.strftime("%Y-%m-%d")

    # Get base observations for dormant/gap data
    obs = observe(alaya_dir)

    # 1. Dirty categories (config)
    dirty = config.get("knowledge", {}).get("dirty_categories", [])
    if dirty:
        cat_list = "、".join(dirty[:5])
        items.append({
            "type": "dirty_categories",
            "severity": "high" if len(dirty) >= 5 else "medium",
            "detail": f"检测到 {len(dirty)} 个脏类别（{cat_list}）",
            "suggestion": "建议您对智能体说「重建索引」，智能体会自动全量构建知识图谱，修复所有脏类别和连边关系"
        })

    # 2. Index missing or stale
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        items.append({
            "type": "index_missing",
            "severity": "high",
            "detail": "知识图谱索引 index.md 不存在，尚未初始化",
            "suggestion": "建议您对智能体说「构建索引」，智能体会自动初始化知识图谱的三层网络结构"
        })
    else:
        index_mtime = os.path.getmtime(index_path)
        newest_mtime = _get_newest_card_mtime(wiki_dir)
        if newest_mtime and index_mtime < newest_mtime:
            days_stale = max(1, int((today.timestamp() - index_mtime) / 86400))
            items.append({
                "type": "index_stale",
                "severity": "medium",
                "detail": f"索引上次更新是 {days_stale} 天前，最近有卡片变更未同步",
                "suggestion": "建议您对智能体说「重建索引」，智能体会同步最新的卡片变更和关系网络"
            })

    # 3. Orphan cards
    orphans = _find_orphan_cards(wiki_dir)
    if orphans:
        items.append({
            "type": "orphan_cards",
            "severity": "low",
            "detail": f"发现 {len(orphans)} 张孤立卡片未被纳入类别索引",
            "suggestion": "建议您对智能体说「重建索引」，智能体会将孤立卡片接入对应的类别关系网络"
        })

    # Orphan categories (folders not in index.md)
    orphan_cats = _find_orphan_categories(wiki_dir)
    if orphan_cats:
        cat_details = "、".join(
            f"{c['category']}({c['card_count']}张卡片)" for c in orphan_cats[:5]
        )
        items.append({
            "type": "orphan_categories",
            "severity": "medium",
            "detail": f"发现 {len(orphan_cats)} 个孤立类别未被 index.md 收录：{cat_details}",
            "suggestion": "建议您对智能体说「重建索引」，智能体会自动将所有类别注册到索引中"
        })

    # Mass dormancy (sleep_counter approaching threshold)
    sleep_counter = config.get("knowledge", {}).get("sleep_counter", 0)
    threshold = config.get("knowledge", {}).get("sleep_notification_threshold", 30)
    if sleep_counter >= threshold * 0.8:
        items.append({
            "type": "mass_dormancy",
            "severity": "medium",
            "detail": f"已有 {sleep_counter}/{threshold} 张卡片进入休眠状态",
            "suggestion": "建议您对智能体说「检查休眠卡片」，智能体会检查并汇总知识库中休眠卡片的情况"
        })

    # Dormant persona cluster (>=2)
    dormant = obs.get("dormant", [])
    if len(dormant) >= 2:
        names_days = [f"{d['persona']}({d['days_since_last']}d)" for d in dormant[:4]]
        names_list = [d['persona'] for d in dormant[:2]]
        items.append({
            "type": "dormant_cluster",
            "severity": "low",
            "detail": f"{len(dormant)} 个角色超过 14 天未互动：{'、'.join(names_days)}",
            "suggestion": f"建议您和{'、'.join(names_list)}聊聊最近的话题，重新激活他们的视角和知识储备"
        })

    # Interest-category alignment (persona interests with no wiki category)
    alignment_gaps = _find_interest_category_gaps(alaya_dir, wiki_dir)
    for gap in alignment_gaps:
        personas_str = "、".join(gap["personas"])
        if len(gap["personas"]) > 1:
            detail = f"{len(gap['personas'])} 个角色（{personas_str}）的兴趣「{gap['interest']}」在知识库中无对应类别"
            suggestion = f"建议您对智能体说「导入 {gap['interest']} 领域的文献」，智能体会自动创建类别并建立知识卡片"
        else:
            detail = f"角色「{personas_str}」的兴趣领域「{gap['interest']}」在知识库中无对应类别目录"
            suggestion = f"建议您对智能体说「在 wiki 下创建 {gap['interest']} 类别并导入知识卡片」，智能体会自动建立新的类别目录"
        items.append({
            "type": "knowledge_gap",
            "severity": "medium",
            "detail": detail,
            "suggestion": suggestion
        })

    # Thin categories (card count <5, from observe data)
    for kg in obs.get("knowledge_gaps", []):
        if kg["issue"] != "thin":
            continue
        interest = kg["interest_area"]
        counts_str = "、".join(
            f"{c}({kg.get('card_counts', {}).get(c, 0)}张)"
            for c in kg.get("categories", [])
        )
        items.append({
            "type": "knowledge_gap_thin",
            "severity": "low",
            "detail": f"角色兴趣领域「{interest}」匹配的类别卡片偏少：{counts_str}",
            "suggestion": f"建议您对智能体说「补充 {interest} 的知识卡片」，智能体会导入更多相关内容"
        })

    # Build canonical key → display name mapping (for cold capacity display)
    _mn_dir = os.path.join(alaya_dir, "manas")
    _persona_display = {}
    if os.path.isdir(_mn_dir):
        for _f in os.listdir(_mn_dir):
            if _f.endswith(".json") and not _f.endswith("_history.json"):
                _data = _read_json(os.path.join(_mn_dir, _f))
                if _data:
                    _k = _f.replace(".json", "")
                    _persona_display[_k] = _data.get("persona", _k)

    # Cold capacity approaching limit
    cold_warnings = _check_cold_capacity(alaya_dir, config, _persona_display)
    items.extend(cold_warnings)

    # Xunxi stale (>7 days)
    last_xunxi = config.get("last_xunxi_time", "")
    if last_xunxi:
        try:
            days_since = (today - datetime.strptime(last_xunxi, "%Y-%m-%d")).days
            if days_since >= 7:
                items.append({
                    "type": "xunxi_stale",
                    "severity": "low",
                    "detail": f"上次熏习（强度衰减维护）是 {days_since} 天前",
                    "suggestion": "建议您对智能体说「运行熏习」，智能体会执行卡片强度衰减计算和知识维护"
                })
        except ValueError:
            pass

    # Description freshness checks (v2.0)
    items.extend(_check_descriptions(wiki_dir, alaya_dir))

    return items


def _get_newest_card_mtime(wiki_dir):
    """Return the most recent mtime across all card files under wiki/."""
    if not os.path.isdir(wiki_dir):
        return None
    newest = 0.0
    for entry in os.listdir(wiki_dir):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".md") and fname not in ("index.md", "log.md") and not is_category_file(fname):
                try:
                    mtime = os.path.getmtime(os.path.join(cat_path, fname))
                    if mtime > newest:
                        newest = mtime
                except OSError:
                    pass
    return newest if newest > 0 else None


def _extract_cards_section(content):
    """Extract only the ## Cards section from a category file.

    Avoids treating [[wiki-links]] in ## Related Categories or other sections
    as card references during orphan detection.
    """
    import re as _re
    cards_start = content.find('## Cards')
    if cards_start < 0:
        return ''
    section = content[cards_start:]
    # Stop at next ## heading or END-AUTO marker (whichever comes first)
    next_boundary = _re.search(r'\n## |<!-- END-AUTO -->', section[8:])
    if next_boundary:
        section = section[:8 + next_boundary.start()]
    return section



def _find_orphan_cards(wiki_dir):
    """Find cards on disk not listed in any {cat}_category.md."""
    if not os.path.isdir(wiki_dir):
        return []
    orphans = []
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        cat_md_path = os.path.join(cat_path, category_file_for(entry))
        linked = set()
        if os.path.exists(cat_md_path):
            try:
                with open(cat_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Only scan ## Cards section to avoid treating cross-category
                # links in ## Related Categories as card references
                cards_section = _extract_cards_section(content)
                if cards_section:
                    linked.update(re.findall(r'\[\[([^\]]+?)\]\]', cards_section))
            except (IOError, UnicodeDecodeError):
                pass
        for fname in os.listdir(cat_path):
            if not fname.endswith(".md") or fname in ("index.md", "log.md") or is_category_file(fname):
                continue
            card_name = fname[:-3]
            if card_name not in linked:
                orphans.append(f"{entry}/{card_name}")
    return orphans


def _find_orphan_categories(wiki_dir):
    """Find category directories not registered in index.md (orphan categories)."""
    if not os.path.isdir(wiki_dir):
        return []
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        return []  # index missing handled separately in check_health
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()
    registered = set(re.findall(r'\[\[([^/\]]+)/[^\]]*_category[^\]]*\]\]', index_content))
    orphans = []
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        if not os.path.exists(os.path.join(cat_path, category_file_for(entry))):
            continue
        if entry not in registered:
            card_count = sum(
                1 for f in os.listdir(cat_path)
                if f.endswith(".md") and f not in ("index.md", "log.md") and not is_category_file(f)
            )
            orphans.append({"category": entry, "card_count": card_count})
    return orphans


def _find_interest_category_gaps(alaya_dir, wiki_dir):
    """Find persona interests with no matching wiki category directory."""
    if not os.path.isdir(wiki_dir):
        return []
    existing = set()
    for entry in os.listdir(wiki_dir):
        cat_path = os.path.join(wiki_dir, entry)
        if os.path.isdir(cat_path) and os.path.exists(os.path.join(cat_path, category_file_for(entry))):
            existing.add(entry.lower())
    mn_dir = os.path.join(alaya_dir, "manas")
    interest_map = {}
    if os.path.isdir(mn_dir):
        for fname in sorted(os.listdir(mn_dir)):
            if not fname.endswith(".json") or fname.endswith("_history.json"):
                continue
            data = _read_json(os.path.join(mn_dir, fname))
            if not data:
                continue
            name = data.get("persona", fname.replace(".json", ""))
            foci = data.get("ego_vector", {}).get("interest_foci", {})
            for interest in foci:
                il = interest.lower()
                if il not in interest_map:
                    interest_map[il] = {"interest": interest, "personas": []}
                if name not in interest_map[il]["personas"]:
                    interest_map[il]["personas"].append(name)
    gaps = []
    for info in interest_map.values():
        interest_lower = info["interest"].lower()
        if not any(interest_lower in c or c in interest_lower for c in existing):
            gaps.append(info)
    gaps.sort(key=lambda g: len(g["personas"]), reverse=True)
    return gaps


def _check_cold_capacity(alaya_dir, config, persona_display=None):
    """Check if persona cold zones are approaching their limit."""
    persona_display = persona_display or {}
    mem_dir = os.path.join(alaya_dir, "memory")
    cold_limit = config.get("memory", {}).get("cold_limit", 45)
    warnings = []
    if not os.path.exists(mem_dir):
        return warnings
    for fname in sorted(os.listdir(mem_dir)):
        if not fname.endswith("_history.json"):
            continue
        try:
            with open(os.path.join(mem_dir, fname), "r", encoding="utf-8") as f:
                hist = json.load(f)
            cold_count = len(hist.get("cold", []))
            if cold_count >= cold_limit * 0.8:
                key = fname.replace("_history.json", "")
                display = persona_display.get(key, key)
                warnings.append({
                    "type": "cold_capacity",
                    "severity": "low",
                    "detail": f"角色「{display}」的历史冷区已达 {cold_count}/{cold_limit} 条",
                    "suggestion": f"建议您对智能体说「整理 {display} 的早期记忆」，智能体会帮您归档处理"
                })
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    return warnings


def _check_descriptions(wiki_dir, alaya_dir):
    """Run all description-related health checks (v2.0)."""
    items = []
    items.extend(_check_missing_card_descriptions(wiki_dir))
    items.extend(_check_stale_category_descriptions(wiki_dir, alaya_dir))
    items.extend(_check_index_description_sync(wiki_dir, alaya_dir))
    items.extend(_check_category_proliferation(wiki_dir))
    return items


def _check_missing_card_descriptions(wiki_dir):
    """Check for cards without description field in YAML frontmatter."""
    if not os.path.isdir(wiki_dir):
        return []
    missing = []
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.endswith('.md') or fname in ('index.md', 'log.md') or is_category_file(fname):
                continue
            fpath = os.path.join(cat_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if content.startswith('---'):
                    dash = content.find('---', 3)
                    if dash > 0:
                        yaml_str = content[3:dash]
                        if 'description:' not in yaml_str:
                            missing.append(f"{entry}/{fname[:-3]}")
            except (IOError, UnicodeDecodeError):
                pass
    if missing:
        return [{
            "type": "missing_descriptions",
            "severity": "low",
            "detail": f"检测到 {len(missing)} 张卡片缺少描述字段：{'、'.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
            "suggestion": "建议您对智能体说「补充卡片描述」，智能体会自动为缺失描述的卡片生成描述"
        }]
    return []


def _check_stale_category_descriptions(wiki_dir, alaya_dir):
    """Check if category descriptions are stale (card count changed >=30%)."""
    if not os.path.isdir(wiki_dir):
        return []
    meta_path = os.path.join(alaya_dir, '.index_metadata.json')
    if not os.path.exists(meta_path):
        return []
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    stale = meta.get('stale_descriptions', [])
    if stale:
        cat_list = '、'.join(stale[:5])
        return [{
            "type": "stale_category_descriptions",
            "severity": "medium",
            "detail": f"检测到 {len(stale)} 个类别的头部描述可能过时：{cat_list}",
            "suggestion": "建议您对智能体说「更新类别描述」，智能体会检查并更新过时的类别描述"
        }]
    return []


def _check_index_description_sync(wiki_dir, alaya_dir):
    """Check if index.md descriptions are in sync with category files."""
    if not os.path.isdir(wiki_dir):
        return []
    index_path = os.path.join(wiki_dir, 'index.md')
    if not os.path.exists(index_path):
        return []

    index_mtime = os.path.getmtime(index_path)
    stale_count = 0
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        cat_file = os.path.join(cat_path, category_file_for(entry))
        if os.path.exists(cat_file) and os.path.getmtime(cat_file) > index_mtime:
            stale_count += 1

    if stale_count > 0:
        return [{
            "type": "index_desync",
            "severity": "low",
            "detail": f"检测到 {stale_count} 个类别的描述已更新但索引未同步",
            "suggestion": "请运行「python scripts/build_index.py --full」将分类精化描述同步至索引（index.md 已合并为单层 base 块，由 --full 统一生成）"
        }]
    return []


def _check_category_proliferation(wiki_dir):
    """Check if there are too many categories relative to card count."""
    if not os.path.isdir(wiki_dir):
        return []
    total_cards = 0
    cat_count = 0
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        cat_file = os.path.join(cat_path, category_file_for(entry))
        if not os.path.exists(cat_file):
            continue
        cat_count += 1
        for fname in os.listdir(cat_path):
            if fname.endswith('.md') and fname not in ('index.md', 'log.md') and not is_category_file(fname):
                total_cards += 1

    import math
    recommended_max = max(5, int(math.sqrt(total_cards)) + 2)
    if cat_count > recommended_max and total_cards > 0:
        return [{
            "type": "category_proliferation",
            "severity": "low",
            "detail": f"当前 {cat_count} 个类别对应 {total_cards} 张卡片（建议 ≤{recommended_max} 个类别），分类可能过于分散",
            "suggestion": "建议您审视分类结构，考虑合并相近的类别，对智能体说「审视分类结构」"
        }]
    return []


def print_report(obs):
    print("=" * 60)
    print("  Alaya · BI Observation Report")
    print(f"  {_now().strftime('%Y-%m-%d %H:%M')}")
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
