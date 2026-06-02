# Alaya · Build Index (v2.0)
# Generates two-layer knowledge graph from wiki/{category}/ subfolders.
#
# Layer 1: wiki/index.md — category overview with descriptions
# Layer 2: wiki/{category}/{category}_category.md — card list with descriptions
# Layer 3: wiki/{category}/*.md — knowledge cards (leaf nodes)
#
# Card descriptions are read from YAML frontmatter. Missing descriptions
# are auto-extracted from card body (blockquote or first paragraph).
# Category headers and index entries can be refined via LLM by the Agent.
#
# v2.0 changes:
#   - _category.md renamed to {category}_category.md (distinguishable in Obsidian graph)
#   - Removed: Concept Network, Card Relations, Core/Peripheral/Dormant tiers
#   - Added: card description extraction, auto category headers, index descriptions
#   - Old _category.md files are auto-migrated on first run
#
# Usage:
#   python scripts/build_index.py [wiki_dir] [alaya_dir]          # full rebuild
#   python scripts/build_index.py --category {cat} [wiki_dir]     # single category
#   python scripts/build_index.py --incremental [wiki_dir]        # only changed categories

import json, os, re, sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bi_observer
from lib.yaml_utils import (
    read_frontmatter, get_field, get_field_float, set_field,
    inject_metadata, rebuild_content, extract_title, get_tags,
    get_description, set_description, slugify, get_all_cards,
    is_category_file, category_file_for, extract_description_from_body,
)

SKIP_FILES = {'index.md', 'log.md'}


def parse_args():
    args = sys.argv[1:]
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'
    category = None
    incremental = False
    classify_card = None

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == '--incremental':
            incremental = True
            i += 1
        elif args[i] == '--classify-card' and i + 1 < len(args):
            classify_card = args[i + 1]
            i += 2
        elif args[i] == '--alaya' and i + 1 < len(args):
            alaya_dir = args[i + 1]
            i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = args[i + 1]
            i += 2
        elif args[i] == '--full':
            # Full rebuild (default behavior, explicit flag for CLI compatibility)
            i += 1
        elif not args[i].startswith('--'):
            if wiki_dir == 'wiki':
                wiki_dir = args[i]
            elif alaya_dir == 'alaya':
                alaya_dir = args[i]
            i += 1
        else:
            i += 1

    return wiki_dir, alaya_dir, category, incremental, classify_card


def load_config(alaya_dir):
    config_path = os.path.join(alaya_dir, 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _kcfg(config):
    """Get knowledge subsystem config (handles flat v1.7 and nested v1.8+)."""
    if 'knowledge' in config:
        return config['knowledge']
    return config


def save_config(alaya_dir, config):
    config_path = os.path.join(alaya_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_index_meta(alaya_dir):
    path = os.path.join(alaya_dir, '.index_metadata.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'last_full_build': '', 'categories': {}, 'stale_descriptions': []}


def save_index_meta(alaya_dir, meta):
    path = os.path.join(alaya_dir, '.index_metadata.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def discover_categories(wiki_dir):
    """Return list of (category_slug, category_path) from wiki/ subfolders."""
    categories = []
    if not os.path.isdir(wiki_dir):
        return categories
    for entry in sorted(os.listdir(wiki_dir)):
        if entry.startswith('.'):
            continue
        cat_path = os.path.join(wiki_dir, entry)
        if os.path.isdir(cat_path):
            # Check if it has at least one .md card (not just category file)
            has_cards = any(
                f.endswith('.md') and f not in SKIP_FILES and not is_category_file(f)
                for f in os.listdir(cat_path)
            )
            if has_cards:
                categories.append((entry, cat_path))
    return categories


def scan_category_cards(cat_path, half_life_default=30):
    """Scan a category folder, inject missing metadata, extract descriptions.

    Returns list of card dicts with keys: name, created_by, strength, tags,
    description, modified.
    """
    cards = []
    today = datetime.now().strftime('%Y-%m-%d')

    for fname in sorted(os.listdir(cat_path)):
        if not fname.endswith('.md') or fname in SKIP_FILES or is_category_file(fname):
            continue

        fpath = os.path.join(cat_path, fname)
        result = read_frontmatter(fpath)
        card_name = fname[:-3]

        if result is None:
            # No YAML at all — wrap with full frontmatter
            with open(fpath, 'r', encoding='utf-8') as f:
                body = f.read()
            desc = extract_description_from_body(body)
            desc_line = f'\ndescription: "{desc}"' if desc else ''
            new_content = (
                f'---\nseed_type: REFINED\ncreated_by: system\n'
                f'strength: 0.5\nlast_activated: {today}\n'
                f'activation_count: 0\nhalf_life: {half_life_default}{desc_line}\n---\n\n{body}'
            )
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            cards.append({
                'name': card_name,
                'created_by': 'system',
                'strength': 0.5,
                'tags': [],
                'description': desc or '',
                'modified': True,
            })
            continue

        content, yaml_str, dash = result

        # Inject missing Alaya metadata
        needs_inject = (
            'seed_type:' not in yaml_str or
            'strength:' not in yaml_str or
            'last_activated:' not in yaml_str
        )
        if needs_inject:
            new_yaml = inject_metadata(yaml_str, {'last_activated': today})
            new_content = rebuild_content(new_yaml, dash, content)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            yaml_str = new_yaml
            content = new_content

        # Get or generate description
        desc = get_description(yaml_str)
        desc_was_generated = False
        if not desc:
            body_text = content[dash + 3:].lstrip('\n')
            desc = extract_description_from_body(body_text)
            if desc:
                new_yaml = set_description(yaml_str, desc)
                new_content = rebuild_content(new_yaml, dash, content)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                yaml_str = new_yaml
                desc_was_generated = True

        cards.append({
            'name': card_name,
            'created_by': get_field(yaml_str, 'created_by') or '',
            'strength': get_field_float(yaml_str, 'strength') or 0.5,
            'tags': get_tags(yaml_str),
            'description': desc or '',
            'modified': needs_inject or desc_was_generated,
        })

    return cards


def generate_category_header(cards):
    """Generate a 100-200 char Chinese category overview from its cards.

    Structure (3 segments):
      1. Domain positioning — from tag statistics (~30 chars)
      2. Semantic overview — top card descriptions aggregated (~60-120 chars)
      3. Reading guidance — optional, for length floor (~15 chars)

    This is the Python fallback. LLM refinement triggered via Agent produces
    richer output with cross-card logical structure and cross-category hints.
    """
    cards_sorted = sorted(cards, key=lambda c: c.get('strength', 0), reverse=True)
    active_cards = [c for c in cards_sorted if c.get('strength', 0) >= 0.1]

    if not active_cards:
        active_cards = cards_sorted

    total = len(cards_sorted)

    # --- Segment 1: Domain positioning ---
    tag_counts = defaultdict(int)
    for c in active_cards:
        for t in c.get('tags', []):
            tag_counts[t.lower()] += 1

    top_tags = sorted(tag_counts, key=tag_counts.get, reverse=True)[:6]
    tag_str = '、'.join(top_tags) if top_tags else '多个领域'

    header = f"本类别聚焦于 {tag_str} 等领域，共收录 {total} 张知识卡片。"

    # --- Segment 2: Semantic overview from card descriptions ---
    descs = [c['description'].strip() for c in active_cards[:5]
             if c.get('description', '').strip()]

    if descs:
        if total == 1:
            header += f" 核心主题：{descs[0]}"
        elif total == 2:
            header += f" 涵盖：{descs[0]}；{descs[1]}。"
        else:
            # 3+ cards: sample top 2 descriptions as entry points
            header += f" 核心议题如：{descs[0]}；{descs[1]}。"
            if total >= 6:
                header += f" 其余 {total - 2} 张卡片延伸至相关子领域。"
            else:
                header += f" 其余卡片亦围绕相关主题展开。"
    else:
        # No descriptions available — generic fallback
        header += f" 各卡片覆盖该领域的核心概念与方法。"

    # --- Segment 3: Reading guidance ---
    if total <= 2:
        header += " 可通过卡片正文深入了解具体内容。"

    return header


def generate_category_md(cat_slug, cards):
    """Generate {cat}_category.md content in v2.0 format."""
    cards_sorted = sorted(cards, key=lambda c: c['strength'], reverse=True)
    header = generate_category_header(cards_sorted)

    lines = [
        f'# {cat_slug}\n',
        f'\n',
        f'<!-- AUTO -->\n',
        f'{header}\n',
        f'\n',
        f'## Cards\n',
    ]

    for c in cards_sorted:
        desc = c.get('description', '')
        if desc:
            lines.append(f'- [[{c["name"]}]] — {desc}\n')
        else:
            lines.append(f'- [[{c["name"]}]]\n')

    lines.append('\n<!-- END-AUTO -->\n')
    return ''.join(lines)


def extract_index_description(category_header):
    """Extract the index.md category entry from the category header.

    Uses the full header (up to 300 chars) since the enhanced header is
    already a structured multi-sentence overview. Only truncates if excessive.
    """
    if not category_header:
        return ''
    # Full header usually fits within 300 chars — use as-is
    if len(category_header) <= 300:
        return category_header
    # Otherwise take up to sentence boundaries within 300 chars
    parts = re.split(r'(?<=[。.])', category_header)
    result = ''
    for p in parts:
        if len(result) + len(p) <= 300:
            result += p
        else:
            break
    return result if result else category_header[:300]


def generate_index_md(category_data):
    """Generate wiki/index.md content in v2.0 format."""
    today = datetime.now().strftime('%Y-%m-%d')

    lines = [
        f'# Knowledge Index\n',
        f'\n',
        f'<!-- AUTO -->\n',
        f'## Categories\n',
        f'\n',
    ]

    for cat in sorted(category_data.keys()):
        cards = category_data[cat]
        # Generate the same header that would go into the category file
        header = generate_category_header(cards)
        index_desc = extract_index_description(header)
        cat_file = category_file_for(cat).replace('.md', '')
        lines.append(f'- [[{cat}/{cat_file}|{cat}]]\n')
        if index_desc:
            lines.append(f'  {index_desc}\n')
        else:
            lines.append(f'  _{len(cards)} 张卡片_\n')
        lines.append('\n')

    lines.append('<!-- END-AUTO -->\n')
    return ''.join(lines)


def write_with_auto_preserve(filepath, new_auto_content):
    """Write file. Preserves <!-- MANUAL --> blocks and restores them near original positions.

    Each MANUAL block is matched to its preceding heading/context in the old file.
    If the same context exists in the new content, the block is placed right after it.
    Otherwise, the block is appended at the end (preserving backward compatibility).
    """
    manual_blocks = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = f.read()
        # Extract manual blocks with position context
        i = 0
        while True:
            start = existing.find('<!-- MANUAL -->', i)
            if start < 0:
                break
            end = existing.find('<!-- END-MANUAL -->', start)
            if end < 0:
                break

            # Capture context: the nearest heading before this MANUAL block
            before = existing[:start]
            heading_match = None
            for m in re.finditer(r'^(#{1,4})\s+(.+)$', before, re.MULTILINE):
                heading_match = m  # last heading wins (closest to the block)
            if heading_match:
                context_key = heading_match.group(0).strip()
            else:
                # Fallback: use up to 80 chars of preceding text
                context_key = before[-80:].strip().split('\n')[-1] if before.strip() else ''

            content = existing[start + len('<!-- MANUAL -->'):end]
            manual_blocks.append((context_key, content))
            i = end + len('<!-- END-MANUAL -->')

    # Insert MANUAL blocks into new content at context-matched positions
    result = new_auto_content
    for context_key, block_content in manual_blocks:
        block_marker = '\n<!-- MANUAL -->' + block_content + '<!-- END-MANUAL -->\n'
        if context_key and context_key in result:
            # Find the line end after the matching context heading
            insert_pos = result.find(context_key) + len(context_key)
            line_end = result.find('\n', insert_pos)
            if line_end < 0:
                line_end = len(result)
            # Insert right after the heading line
            result = result[:line_end + 1] + block_marker + result[line_end + 1:]
        else:
            # Fallback: append at end (backward compatible)
            result += block_marker

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result)


def migrate_old_category_file(cat_path, cat_slug):
    """Migrate old _category.md to {cat}_category.md.

    Preserves MANUAL blocks from old file. Returns True if migration occurred.
    """
    old_path = os.path.join(cat_path, '_category.md')
    new_path = os.path.join(cat_path, category_file_for(cat_slug))

    if not os.path.exists(old_path):
        return False

    # If new file already exists, just delete old
    if os.path.exists(new_path):
        os.remove(old_path)
        print(f'  Migrated (removed old): {cat_slug}/_category.md')
        return True

    # Extract MANUAL blocks from old file
    manual_blocks = []
    with open(old_path, 'r', encoding='utf-8') as f:
        old_content = f.read()
    i = 0
    while True:
        start = old_content.find('<!-- MANUAL -->', i)
        if start < 0:
            break
        end = old_content.find('<!-- END-MANUAL -->', start)
        if end < 0:
            break
        manual_blocks.append(old_content[start + len('<!-- MANUAL -->'):end])
        i = end + len('<!-- END-MANUAL -->')

    # Move old file to new filename (content will be regenerated on next build)
    os.rename(old_path, new_path)
    print(f'  Migrated: {cat_slug}/_category.md -> {cat_slug}/{category_file_for(cat_slug)}')
    return True


def classify_card_to_category(card_tags, existing_categories):
    """Try to classify a card into an existing category based on tag overlap.

    Returns (matched_category | None, candidates | None).
    If exactly one category matches, returns (cat, None).
    If multiple match, returns (None, [cat1, cat2, ...]).
    If none match, returns (None, None).
    """
    if not existing_categories:
        return (None, None)

    tag_set = {t.lower().replace(' ', '-') for t in card_tags}
    if not tag_set:
        return (None, None)

    matches = []
    for cat_slug, cat_tags in existing_categories.items():
        cat_tag_set = {t.lower().replace(' ', '-') for t in cat_tags}
        overlap = tag_set & cat_tag_set
        if overlap:
            matches.append((cat_slug, len(overlap)))

    matches.sort(key=lambda x: x[1], reverse=True)

    if not matches:
        return (None, None)
    elif len(matches) == 1:
        return (matches[0][0], None)
    else:
        # Multiple matches: if one is clearly better (2x overlap), use it
        if matches[0][1] >= matches[1][1] * 2:
            return (matches[0][0], None)
        return (None, [m[0] for m in matches])


def main():
    wiki_dir, alaya_dir, target_category, incremental, classify_card = parse_args()
    config = load_config(alaya_dir)
    index_meta = load_index_meta(alaya_dir)
    half_life = _kcfg(config).get('half_life_default', 30)
    today = datetime.now().strftime('%Y-%m-%d')

    # --classify-card mode: output classification suggestion as JSON
    if classify_card:
        card_tags = []
        card_name = classify_card
        card_path = os.path.join(wiki_dir, classify_card) if os.path.exists(os.path.join(wiki_dir, classify_card)) else None
        if card_path is None:
            # Try to find the card
            for entry in os.listdir(wiki_dir):
                test_path = os.path.join(wiki_dir, entry, classify_card)
                if os.path.exists(test_path):
                    card_path = test_path
                    break
                test_path = os.path.join(wiki_dir, entry, classify_card + '.md')
                if os.path.exists(test_path):
                    card_path = test_path
                    card_name = classify_card + '.md'
                    break

        if card_path and os.path.exists(card_path):
            result = read_frontmatter(card_path)
            if result:
                _, yaml_str, _ = result
                card_tags = get_tags(yaml_str)

        # Build existing category tag profiles
        categories = discover_categories(wiki_dir)
        cat_tag_profiles = {}
        for slug, cat_path in categories:
            cards = scan_category_cards(cat_path, half_life)
            all_tags = set()
            for c in cards:
                for t in c.get('tags', []):
                    all_tags.add(t)
            cat_tag_profiles[slug] = sorted(all_tags)

        matched, candidates = classify_card_to_category(card_tags, cat_tag_profiles)
        result = {
            'card': card_name.replace('.md', ''),
            'tags': card_tags,
            'matched_category': matched,
            'candidates': candidates,
            'existing_categories': list(cat_tag_profiles.keys()),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Normal build flow
    categories = discover_categories(wiki_dir)

    if not categories:
        print('No category subfolders found in wiki/')
        print('  Create wiki/{category-name}/ and add .md cards.')
        return

    # Determine which categories to rebuild
    if target_category:
        cat_dirs = {slug: path for slug, path in categories if slug == target_category}
        if not cat_dirs:
            print(f'Category not found: {target_category}')
            print(f'  Available: {", ".join(s for s, _ in categories)}')
            return
        cats_to_build = [(target_category, cat_dirs[target_category])]
    elif incremental:
        cats_to_build = []
        for slug, cat_path in categories:
            cat_meta = index_meta.get('categories', {}).get(slug, {})
            last_build = cat_meta.get('last_build', '')
            if not last_build:
                cats_to_build.append((slug, cat_path))
                continue
            # Check if any card is newer than last_build
            needs_rebuild = False
            for fname in os.listdir(cat_path):
                if not fname.endswith('.md') or fname in SKIP_FILES or is_category_file(fname):
                    continue
                fpath = os.path.join(cat_path, fname)
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d')
                if mtime > last_build:
                    needs_rebuild = True
                    break
            # Also check if category file itself is newer
            cat_file = os.path.join(cat_path, category_file_for(slug))
            if os.path.exists(cat_file):
                cat_mtime = datetime.fromtimestamp(os.path.getmtime(cat_file)).strftime('%Y-%m-%d')
                if cat_mtime > last_build:
                    needs_rebuild = True
            if needs_rebuild:
                cats_to_build.append((slug, cat_path))

        # Also rebuild categories marked dirty
        dirty = _kcfg(config).get('dirty_categories', [])
        for slug, cat_path in categories:
            if slug in dirty and (slug, cat_path) not in cats_to_build:
                cats_to_build.append((slug, cat_path))
        if dirty:
            _kcfg(config)['dirty_categories'] = []
            save_config(alaya_dir, config)
        if not cats_to_build:
            print('Incremental: no categories need rebuild')
            return
    else:
        # Full rebuild
        cats_to_build = categories

    # Phase 0: Migrate old _category.md files (first run after upgrade)
    migration_count = 0
    for slug, cat_path in cats_to_build:
        if migrate_old_category_file(cat_path, slug):
            migration_count += 1
    if migration_count:
        print(f'Migrated {migration_count} old _category.md file(s)')

    # Phase 1: Scan cards, inject metadata, extract descriptions
    category_data = {}
    injected_count = 0
    desc_generated_count = 0

    for slug, cat_path in cats_to_build:
        cards = scan_category_cards(cat_path, half_life)
        category_data[slug] = cards
        injected = sum(1 for c in cards if c.get('modified'))
        injected_count += injected
        # Count newly generated descriptions
        desc_generated_count += sum(1 for c in cards if c.get('description') and c.get('modified'))

    # Phase 2: Generate {cat}_category.md files
    stale_descriptions = list(index_meta.get('stale_descriptions', []))
    for slug in category_data:
        cat_path = os.path.join(wiki_dir, slug)
        cat_md_path = os.path.join(cat_path, category_file_for(slug))
        content = generate_category_md(slug, category_data[slug])
        write_with_auto_preserve(cat_md_path, content)

        # Update index metadata
        index_meta.setdefault('categories', {})[slug] = {
            'last_build': today,
            'card_count': len(category_data[slug]),
        }
        # Mark description as potentially stale if cards changed significantly
        old_count = index_meta.get('categories', {}).get(slug, {}).get('card_count', 0)
        if old_count and abs(len(category_data[slug]) - old_count) / max(old_count, 1) >= 0.3:
            if slug not in stale_descriptions:
                stale_descriptions.append(slug)

    index_meta['stale_descriptions'] = stale_descriptions

    # Phase 3: Generate wiki/index.md
    if not target_category:
        index_path = os.path.join(wiki_dir, 'index.md')
        index_content = generate_index_md(category_data)
        write_with_auto_preserve(index_path, index_content)
        index_meta['last_full_build'] = today
    elif incremental:
        # Rebuild full index to reflect all categories
        all_data = {}
        for slug, cat_path in categories:
            if slug in category_data:
                all_data[slug] = category_data[slug]
            else:
                all_data[slug] = scan_category_cards(cat_path, half_life)
        index_path = os.path.join(wiki_dir, 'index.md')
        index_content = generate_index_md(all_data)
        write_with_auto_preserve(index_path, index_content)

    # Save index metadata
    save_index_meta(alaya_dir, index_meta)

    # Report
    total_cards = sum(len(v) for v in category_data.values())
    built_cats = len(category_data)
    total_cats = len(categories)
    mode = 'full' if not target_category and not incremental else \
           f'single ({target_category})' if target_category else 'incremental'

    print(f'Build complete [{mode}]')
    print(f'  Categories built: {built_cats}/{total_cats}')
    print(f'  Cards processed: {total_cards}')
    print(f'  Metadata injected: {injected_count}')
    print(f'  Descriptions generated: {desc_generated_count}')
    if stale_descriptions:
        print(f'  Categories with stale descriptions: {", ".join(stale_descriptions)}')

    # BI hitchhiking: passive health check after index build
    try:
        health_items = bi_observer.check_health(alaya_dir, wiki_dir, config)
        if health_items:
            # Write to bi_notes.json (passive, no user-facing output unless severe)
            bi_notes_path = os.path.join(alaya_dir, 'bi_notes.json')
            existing_notes = []
            if os.path.exists(bi_notes_path):
                try:
                    with open(bi_notes_path, 'r', encoding='utf-8') as f:
                        existing_notes = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            record = {
                'date': today,
                'trigger': 'build_index',
                'system_health': health_items
            }
            existing_notes.append(record)
            existing_notes = existing_notes[-20:]
            with open(bi_notes_path, 'w', encoding='utf-8') as f:
                json.dump(existing_notes, f, ensure_ascii=False, indent=2)
            # Only print high-severity items
            high_items = [h for h in health_items if h.get('severity') == 'high']
            if high_items:
                print(f'\n  ⚠️ BI health: {len(high_items)} high-severity issue(s)')
                for h in high_items:
                    print(f'    • {h["detail"]}')
    except Exception:
        pass  # BI hitchhiking must never block the build

    print('Done.')


if __name__ == '__main__':
    main()
