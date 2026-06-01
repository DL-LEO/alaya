# Alaya · Build Index (v1.7)
# Generates three-layer knowledge graph from wiki/{category}/ subfolders.
#
# Layer 1: wiki/index.md — category overview + Concept Network (tag-overlap cross-links)
# Layer 2: wiki/{category}/_category.md — card list + Card Relations (tag-overlap intra-links)
# Layer 3: wiki/{category}/*.md — knowledge cards (leaf nodes)
#
# Also injects missing Alaya metadata into cards (merges scan_cards.py).
# Supports incremental rebuild via --category or --incremental flags.
#
# Usage:
#   python scripts/build_index.py [wiki_dir] [alaya_dir]          # full rebuild
#   python scripts/build_index.py --category {cat} [wiki_dir]     # single category
#   python scripts/build_index.py --incremental [wiki_dir]        # only changed categories

import json, os, re, sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import (
    read_frontmatter, get_field, get_field_float, set_field,
    inject_metadata, rebuild_content, extract_title, get_tags,
    slugify, get_all_cards,
)

SKIP_FILES = {'_category.md', 'index.md', 'log.md'}
CORE_THRESHOLD = 0.5


def parse_args():
    args = sys.argv[1:]
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'
    category = None
    incremental = False

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == '--incremental':
            incremental = True
            i += 1
        elif args[i] == '--alaya' and i + 1 < len(args):
            alaya_dir = args[i + 1]
            i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            if wiki_dir == 'wiki':
                wiki_dir = args[i]
            elif alaya_dir == 'alaya':
                alaya_dir = args[i]
            i += 1
        else:
            i += 1

    return wiki_dir, alaya_dir, category, incremental


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
    return {'last_full_build': '', 'categories': {}}


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
        cat_path = os.path.join(wiki_dir, entry)
        if os.path.isdir(cat_path):
            # Check if it has at least one .md card (not just _category.md)
            has_cards = any(
                f.endswith('.md') and f not in SKIP_FILES
                for f in os.listdir(cat_path)
            )
            if has_cards:
                categories.append((entry, cat_path))
    return categories


def scan_category_cards(cat_path, half_life_default=30):
    """Scan a category folder, inject missing metadata, return card data."""
    cards = []
    today = datetime.now().strftime('%Y-%m-%d')

    for fname in sorted(os.listdir(cat_path)):
        if not fname.endswith('.md') or fname in SKIP_FILES:
            continue

        fpath = os.path.join(cat_path, fname)
        result = read_frontmatter(fpath)
        if result is None:
            # No YAML at all — wrap with full frontmatter
            with open(fpath, 'r', encoding='utf-8') as f:
                body = f.read()
            card_name = fname[:-3]
            new_content = (
                f'---\nseed_type: REFINED\ncreated_by: system\n'
                f'strength: 0.5\nlast_activated: {today}\n'
                f'activation_count: 0\nhalf_life: {half_life_default}\n---\n\n{body}'
            )
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            cards.append({
                'name': card_name,
                'created_by': 'system',
                'strength': 0.5,
                'tags': [],
                'modified': True,
            })
            continue

        content, yaml_str, dash = result
        card_name = fname[:-3]

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

        cards.append({
            'name': card_name,
            'created_by': get_field(yaml_str, 'created_by') or '',
            'strength': get_field_float(yaml_str, 'strength') or 0.5,
            'tags': get_tags(yaml_str),
            'modified': needs_inject,
        })

    return cards


def compute_tag_overlaps(category_data):
    """Compute tag overlap between categories for Concept Network links."""
    # Build per-category tag sets
    cat_tags = {}
    for cat, cards in category_data.items():
        tag_set = set()
        for card in cards:
            for tag in card['tags']:
                tag_set.add(tag.lower().replace(' ', '-'))
        cat_tags[cat] = tag_set

    # Find overlapping tag pairs
    overlaps = []
    cats = sorted(cat_tags.keys())
    for i, cat_a in enumerate(cats):
        for cat_b in cats[i + 1:]:
            shared = cat_tags[cat_a] & cat_tags[cat_b]
            if len(shared) >= 2:
                overlaps.append((cat_a, cat_b, sorted(shared)))
    return overlaps


def compute_card_relations(cards):
    """Compute tag-overlap card relations within a category."""
    relations = []
    for i, card_a in enumerate(cards):
        tags_a = {t.lower().replace(' ', '-') for t in card_a['tags']}
        if not tags_a:
            continue
        for card_b in cards[i + 1:]:
            tags_b = {t.lower().replace(' ', '-') for t in card_b['tags']}
            shared = tags_a & tags_b
            if len(shared) >= 1 and len(shared) >= min(len(tags_a), len(tags_b)) * 0.3:
                relations.append((card_a['name'], card_b['name'], sorted(shared)))
    return relations


def generate_category_md(cat_slug, cards):
    """Generate _category.md content for a category."""
    cards_sorted = sorted(cards, key=lambda c: c['strength'], reverse=True)
    core = [c for c in cards_sorted if c['strength'] >= CORE_THRESHOLD]
    peripheral = [c for c in cards_sorted if 0.1 <= c['strength'] < CORE_THRESHOLD]
    dormant = [c for c in cards_sorted if c['strength'] < 0.1]

    relations = compute_card_relations(cards_sorted)

    lines = [
        f'# {cat_slug}\n',
        f'Generated: {datetime.now().strftime("%Y-%m-%d")}\n',
        '\n',
        '<!-- AUTO -->\n',
    ]

    # Core section
    lines.append(f'## Core ({len(core)} cards, strength >= {CORE_THRESHOLD})\n\n')
    lines.append('| Card | Created By | Strength |\n|:--|:--|:--|\n')
    for c in core:
        lines.append(f'| [[{c["name"]}]] | {c["created_by"]} | {c["strength"]:.2f} |\n')

    # Peripheral section
    if peripheral:
        lines.append(f'\n## Peripheral ({len(peripheral)} cards)\n\n')
        lines.append('| Card | Created By | Strength |\n|:--|:--|:--|\n')
        for c in peripheral:
            lines.append(f'| [[{c["name"]}]] | {c["created_by"]} | {c["strength"]:.2f} |\n')

    # Dormant section
    if dormant:
        lines.append(f'\n## Dormant ({len(dormant)} cards)\n\n')
        lines.append(', '.join(f'[[{c["name"]}]]' for c in dormant) + '\n')

    # Card Relations
    if relations:
        lines.append('\n## Card Relations\n\n')
        for a, b, shared in relations:
            lines.append(f'- [[{a}]] <-> [[{b}]] (shared: {", ".join(shared)})\n')

    lines.append('<!-- END-AUTO -->\n')
    return ''.join(lines)


def generate_index_md(category_data, overlaps):
    """Generate wiki/index.md content."""
    today = datetime.now().strftime('%Y-%m-%d')

    lines = [
        f'# Knowledge Index\n',
        f'Generated: {today}\n',
        '\n',
    ]

    # Preserve any manual content between <!-- MANUAL --> markers if file exists
    # (We'll handle this in the caller; here we generate the AUTO section only)

    lines.append('<!-- AUTO -->\n')
    lines.append('## Categories\n\n')
    lines.append('| Category | Core | Peripheral | Total |\n|:--|--:|--:|--:|\n')

    for cat in sorted(category_data.keys()):
        cards = category_data[cat]
        core = sum(1 for c in cards if c['strength'] >= CORE_THRESHOLD)
        peripheral = sum(1 for c in cards if 0.1 <= c['strength'] < CORE_THRESHOLD)
        total = len(cards)
        lines.append(f'| [[{cat}/_category|{cat}]] | {core} | {peripheral} | {total} |\n')

    if overlaps:
        lines.append('\n## Concept Network\n\n')
        for cat_a, cat_b, shared in overlaps:
            lines.append(f'- [[{cat_a}/_category|{cat_a}]] <-> [[{cat_b}/_category|{cat_b}]] (shared: {", ".join(shared)})\n')

    lines.append('<!-- END-AUTO -->\n')
    return ''.join(lines)


def write_with_auto_preserve(filepath, new_auto_content):
    """Write file. Preserves content in <!-- MANUAL --> blocks, replaces everything else."""
    manual_blocks = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = f.read()
        # Extract manual blocks
        i = 0
        while True:
            start = existing.find('<!-- MANUAL -->', i)
            if start < 0:
                break
            end = existing.find('<!-- END-MANUAL -->', start)
            if end < 0:
                break
            manual_blocks.append(existing[start + len('<!-- MANUAL -->'):end])
            i = end + len('<!-- END-MANUAL -->')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_auto_content)
        for block in manual_blocks:
            f.write('\n<!-- MANUAL -->')
            f.write(block)
            f.write('<!-- END-MANUAL -->\n')


def main():
    wiki_dir, alaya_dir, target_category, incremental = parse_args()
    config = load_config(alaya_dir)
    index_meta = load_index_meta(alaya_dir)
    half_life = _kcfg(config).get('half_life_default', 30)
    today = datetime.now().strftime('%Y-%m-%d')

    categories = discover_categories(wiki_dir)

    if not categories:
        print('No category subfolders found in wiki/')
        print('  Create wiki/{category-name}/ and add .md cards.')
        return

    # Determine which categories to rebuild
    if target_category:
        # Level 0: single category
        cat_dirs = {slug: path for slug, path in categories if slug == target_category}
        if not cat_dirs:
            print(f'Category not found: {target_category}')
            print(f'  Available: {", ".join(s for s, _ in categories)}')
            return
        cats_to_build = [(target_category, cat_dirs[target_category])]
    elif incremental:
        # Level 2: only categories with newer files
        cats_to_build = []
        for slug, cat_path in categories:
            cat_meta = index_meta.get('categories', {}).get(slug, {})
            last_build = cat_meta.get('last_build', '')
            if not last_build:
                cats_to_build.append((slug, cat_path))
                continue
            # Check if any card is newer than last_build
            for fname in os.listdir(cat_path):
                fpath = os.path.join(cat_path, fname)
                if fname.endswith('.md') and fname not in SKIP_FILES:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d')
                    if mtime > last_build:
                        cats_to_build.append((slug, cat_path))
                        break
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

    # Phase 1: Scan cards, inject metadata, collect data
    category_data = {}
    injected_count = 0

    for slug, cat_path in cats_to_build:
        cards = scan_category_cards(cat_path, half_life)
        category_data[slug] = cards
        injected = sum(1 for c in cards if c.get('modified'))
        injected_count += injected

    # Phase 2: Compute tag overlaps for Concept Network
    overlaps = compute_tag_overlaps(category_data)

    # Phase 3: Generate _category.md files
    for slug in category_data:
        cat_path = os.path.join(wiki_dir, slug)
        cat_md_path = os.path.join(cat_path, '_category.md')
        content = generate_category_md(slug, category_data[slug])
        write_with_auto_preserve(cat_md_path, content)

        # Update index metadata
        index_meta.setdefault('categories', {})[slug] = {
            'last_build': today,
            'card_count': len(category_data[slug]),
        }

    # Phase 4: Generate wiki/index.md (only on full rebuild or when overlaps change)
    if not target_category:
        index_path = os.path.join(wiki_dir, 'index.md')
        index_content = generate_index_md(category_data, overlaps)
        write_with_auto_preserve(index_path, index_content)
        index_meta['last_full_build'] = today
    elif incremental:
        # Rebuild full index to reflect changes
        all_data = {}
        for slug, cat_path in categories:
            if slug in category_data:
                all_data[slug] = category_data[slug]
            else:
                # Load existing cards without re-scanning
                all_data[slug] = scan_category_cards(cat_path, half_life)
        all_overlaps = compute_tag_overlaps(all_data)
        index_path = os.path.join(wiki_dir, 'index.md')
        index_content = generate_index_md(all_data, all_overlaps)
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
    print(f'  Cross-category links: {len(overlaps)}')
    print('Done.')


if __name__ == '__main__':
    main()
