# Alaya · Health Check (v2.0)
# Checks two-layer knowledge network integrity:
# Layer 1: wiki/index.md links, AUTO markers
# Layer 2: {cat}_category.md links, card existence, orphans, descriptions
# Layer 3: Card metadata coverage + description field
# Layer 4: Memory system (history files, ambient state)
#
# Usage: python scripts/health_check.py [wiki_dir] [alaya_dir]

import json, os, re, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import is_category_file, category_file_for

SKIP_FILES = {'index.md', 'log.md'}


def _extract_cards_section(content):
    """Extract only the ## Cards section from a category file.

    Avoids treating [[wiki-links]] in ## Related Categories or other sections
    as card references during link validation and orphan detection.
    """
    cards_start = content.find('## Cards')
    if cards_start < 0:
        return ''
    section = content[cards_start:]
    # Stop at next ## heading or END-AUTO marker
    next_boundary = re.search(r'\n## |<!-- END-AUTO -->', section[8:])
    if next_boundary:
        section = section[:8 + next_boundary.start()]
    return section


def safe_read_text(filepath):
    """Read file content safely. Returns (content, None) on success, (None, error_msg) on failure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(), None
    except (IOError, OSError) as e:
        return None, f"Cannot read {filepath}: {e}"


def safe_read_json(filepath):
    """Read JSON file safely. Returns (data, None) on success, (None, error_msg) on failure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except (IOError, OSError) as e:
        return None, f"Cannot read {filepath}: {e}"
    except json.JSONDecodeError as e:
        return None, f"Corrupt JSON in {filepath}: {e}"

wiki_dir = sys.argv[1] if len(sys.argv) > 1 else 'wiki'
alaya_dir = sys.argv[2] if len(sys.argv) > 2 else 'alaya'

print('=' * 50)
print('  Alaya · Health Check')
print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('=' * 50)

issues = []

# 1. Persona check
print(f'\n[1] Persona Configurations')
manas_dir = os.path.join(alaya_dir, 'manas')
if os.path.exists(manas_dir):
    manas_files = [f for f in os.listdir(manas_dir) if f.endswith('.json')]
    print(f'  Active personas: {len(manas_files)}')
    for f in manas_files:
        data, err = safe_read_json(os.path.join(manas_dir, f))
        if err:
            issues.append(err)
            continue
        name = data.get('persona', f)
        has_foci = 'interest_foci' in data.get('ego_vector', {})
        print(f'    {name} — foci={has_foci}')
else:
    issues.append('manas/ directory not found')

# 2. Layer 1 — index.md checks
print(f'\n[2] Layer 1: index.md')
index_path = os.path.join(wiki_dir, 'index.md')
index_exists = os.path.exists(index_path)
if index_exists:
    index_content, err = safe_read_text(index_path)
    if err:
        issues.append(err)
        index_content = ""

    # Check AUTO markers
    has_auto_start = '<!-- AUTO -->' in index_content
    has_auto_end = '<!-- END-AUTO -->' in index_content
    if not has_auto_start or not has_auto_end:
        issues.append('index.md missing <!-- AUTO --> / <!-- END-AUTO --> markers')
        print('  AUTO markers: MISSING')
    else:
        print('  AUTO markers: OK')

    # Extract category links from index.md (v2.0 format: [[cat/cat_category|cat]])
    cat_links = re.findall(r'\[\[([^/\]]+)/[^\]]*_category[^\]]*\]\]', index_content)
    missing_cats = []
    for cat in cat_links:
        cat_path = os.path.join(wiki_dir, cat)
        cat_md = os.path.join(cat_path, category_file_for(cat))
        if not os.path.isdir(cat_path) or not os.path.exists(cat_md):
            missing_cats.append(cat)
    if missing_cats:
        issues.append(f'index.md references missing categories: {missing_cats[:5]}')
        for c in missing_cats[:5]:
            print(f'  [broken] index → [[{c}]]')
    else:
        print(f'  Category links: {len(cat_links)} OK')

    # Check for orphan categories (exist on disk but not in index.md)
    orphan_cats = []
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        if not os.path.exists(os.path.join(cat_path, category_file_for(entry))):
            continue
        if entry not in cat_links:
            orphan_cats.append(entry)
    if orphan_cats:
        issues.append(f'{len(orphan_cats)} categories not registered in index.md: {orphan_cats}')
        for c in orphan_cats:
            print(f'  [orphan_cat] {c}/')
else:
    issues.append('wiki/index.md not found — run build_index.py')
    print('  index.md: NOT FOUND')

# 3. Layer 2 — category file checks
print(f'\n[3] Layer 2: Category Files')
all_cards = {}       # card_name -> category
card_files = set()   # all .md card paths
orphan_cards = []

if os.path.isdir(wiki_dir):
    for entry in sorted(os.listdir(wiki_dir)):
        if entry.startswith('.'):
            continue
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue

        cat_md_path = os.path.join(cat_path, category_file_for(entry))
        if not os.path.exists(cat_md_path):
            issues.append(f'Missing category file in: {entry}')
            print(f'  [missing] {entry}/{category_file_for(entry)}')
            continue

        cat_content, err = safe_read_text(cat_md_path)
        if err:
            issues.append(err)
            continue

        # Check AUTO markers
        if '<!-- AUTO -->' not in cat_content or '<!-- END-AUTO -->' not in cat_content:
            issues.append(f'{entry}/{category_file_for(entry)} missing AUTO markers')

        # Extract card links (only from ## Cards section)
        cards_section = _extract_cards_section(cat_content)
        linked_cards = re.findall(r'\[\[([^\]]+?)\]\]', cards_section)
        broken = []
        for card in linked_cards:
            card_file = os.path.join(cat_path, card + '.md')
            if not os.path.exists(card_file):
                broken.append(card)
        if broken:
            issues.append(f'{entry}/ category file broken links: {broken[:3]}')
            for b in broken[:3]:
                print(f'  [broken] {entry}/[[{b}]]')

        # Track all cards in this category
        for fname in os.listdir(cat_path):
            if fname.endswith('.md') and fname not in SKIP_FILES and not is_category_file(fname):
                card_name = fname[:-3]
                all_cards[card_name] = entry
                card_files.add(os.path.join(cat_path, fname))

    print(f'  Categories scanned: {len(os.listdir(wiki_dir))}')
    print(f'  Total cards: {len(all_cards)}')

    # 4. Orphan check
    print(f'\n[4] Orphan Cards')
    linked_names = set()
    for entry in os.listdir(wiki_dir):
        if entry.startswith('.'):
            continue
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        cat_md_path = os.path.join(cat_path, category_file_for(entry))
        if not os.path.exists(cat_md_path):
            continue
        cat_content, err = safe_read_text(cat_md_path)
        if err:
            issues.append(err)
            continue
        cards_section = _extract_cards_section(cat_content)
        for link in re.findall(r'\[\[([^\]]+?)\]\]', cards_section):
            linked_names.add(link)

    for card_name, cat in all_cards.items():
        if card_name not in linked_names:
            orphan_cards.append(f'{cat}/{card_name}')

    if orphan_cards:
        issues.append(f'{len(orphan_cards)} orphan cards not in category file')
        for o in orphan_cards[:5]:
            print(f'  [orphan] {o}')
    else:
        print(f'  Orphans: none')

# 5. Metadata coverage
print(f'\n[5] Metadata Coverage')
required_fields = ['seed_type', 'strength', 'last_activated', 'description']
missing_meta = 0
missing_desc = 0
if os.path.isdir(wiki_dir):
    for entry in os.listdir(wiki_dir):
        if entry.startswith('.'):
            continue
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        for fname in os.listdir(cat_path):
            if not fname.endswith('.md') or fname in SKIP_FILES or is_category_file(fname):
                continue
            fpath = os.path.join(cat_path, fname)
            content, err = safe_read_text(fpath)
            if err:
                issues.append(err)
                continue
            for field in required_fields:
                if f'{field}:' not in content:
                    if field == 'description':
                        missing_desc += 1
                    else:
                        missing_meta += 1
                        break

    if missing_meta:
        issues.append(f'{missing_meta} cards missing required metadata — run build_index.py')
    if missing_desc:
        print(f'  Cards missing description: {missing_desc}/{len(all_cards)}')
    print(f'  Cards with full metadata: {len(all_cards) - missing_meta}/{len(all_cards)}')

# 6. Dirty categories
print(f'\n[6] Dirty Categories')
config_path = os.path.join(alaya_dir, 'config.json')
if os.path.exists(config_path):
    cfg, err = safe_read_json(config_path)
    if err:
        issues.append(err)
    else:
        dirty = cfg.get('knowledge', {}).get('dirty_categories', [])
        if dirty:
            issues.append(f'{len(dirty)} categories need rebuild: {dirty}')
            for d in dirty:
                print(f'  [dirty] {d}')
        else:
            print('  None')
else:
    issues.append('config.json not found')

# 7. Version + Config check
print(f'\n[7] Configuration')
if os.path.exists(config_path):
    cfg, err = safe_read_json(config_path)
    if err:
        issues.append(err)
    else:
        print(f'  Version: {cfg.get("version", "unknown")}')
        print(f'  Language: {cfg.get("language", "not set")}')
        # Nested config (v1.8+) or flat (migrated)
        kcfg = cfg.get('knowledge', {})
        pcfg = cfg.get('persona', {})
        mcfg = cfg.get('memory', {})
        print(f'  Knowledge:')
        print(f'    top_k: {kcfg.get("top_k", "not set")}')
        print(f'    dirty_categories: {len(kcfg.get("dirty_categories", []))}')
        print(f'    sleep_counter: {kcfg.get("sleep_counter", 0)}')
        print(f'  Memory:')
        print(f'    version: {mcfg.get("version", "not set")}')
        print(f'    hot_limit: {mcfg.get("hot_limit", "not set")}')
        print(f'  Persona:')
        print(f'    max_cards_per_persona: {pcfg.get("max_cards_per_persona", "not set")}')
        print(f'    affinity_decay: {pcfg.get("affinity_decay", "not set")}')

# 8. Memory system check
print(f'\n[8] Memory System')
memory_dir = os.path.join(alaya_dir, 'memory')
if os.path.exists(memory_dir):
    history_files = [f for f in os.listdir(memory_dir) if f.endswith('_history.json')]
    print(f'  History files: {len(history_files)}')
    for hf in history_files:
        hp = os.path.join(memory_dir, hf)
        hist, err = safe_read_json(hp)
        if err:
            issues.append(err)
            continue
        hot = hist.get('hot', [])
        cold = hist.get('cold', [])
        has_mood = any(e.get('mood') for e in hot)
        print(f'    {hf}: hot={len(hot)}, cold={len(cold)}, mood_tracked={has_mood}')
    ambient_path = os.path.join(memory_dir, 'ambient.json')
    if os.path.exists(ambient_path):
        ambient, err = safe_read_json(ambient_path)
        if err:
            issues.append(err)
        else:
            mood = ambient.get("recent_mood", "")
            attention = len(ambient.get("recent_attention", {}))
            trajectory = len(ambient.get("mood_trajectory", []))
            themes = ambient.get("recent_themes", "")
            threads = len(ambient.get("open_threads", []))
            style = ambient.get("user_style_notes", "")
            print(f'  Ambient: mood="{mood}", trajectory={trajectory}, attention={attention}')
            print(f'    themes={bool(themes)}, open_threads={threads}, style_notes={bool(style)}')

            # Check for old-format ambient (missing semantic fields)
            missing_fields = []
            for field in ['mood_trajectory', 'recent_themes', 'open_threads', 'user_style_notes']:
                if field not in ambient:
                    missing_fields.append(field)
            if missing_fields:
                issues.append(f'ambient.json missing fields: {missing_fields} — LLM will auto-init on first save')
                for mf in missing_fields:
                    print(f'  [upgrade] ambient.json missing field: {mf}')
    else:
        print(f'  Ambient: not found')
else:
    print(f'  memory/ directory not found (will be created on first interaction)')

# Summary
print(f'\n' + '=' * 50)
if issues:
    print(f'  Issues found: {len(issues)}')
    for i, issue in enumerate(issues, 1):
        print(f'  {i}. {issue}')
    print('  Run "build index" to fix index-related issues.')
else:
    print('  All checks passed!')
print('=' * 50)
sys.exit(1 if issues else 0)
