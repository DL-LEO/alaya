# Alaya · Batch Import
# Import files from a directory into wiki/{category}/ with checkpoint/resume.
# Supports .md, .txt, and .pdf (via format_converter, PyMuPDF optional).
#
# Usage:
#   python scripts/batch_import.py <source_dir> [--category cat] [--wiki dir] [--alaya dir]

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import read_frontmatter, inject_metadata, rebuild_content, extract_title, get_tags, slugify
from lib.format_converter import detect_format, extract_text, get_agent_template


def parse_args():
    args = sys.argv[1:]
    source = None
    category = None
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = args[i + 1]
            i += 2
        elif args[i] == '--alaya' and i + 1 < len(args):
            alaya_dir = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            if source is None:
                source = args[i]
            i += 1
        else:
            i += 1

    return source, category, wiki_dir, alaya_dir


def load_checkpoint(alaya_dir):
    path = os.path.join(alaya_dir, '.import_checkpoint.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_checkpoint(alaya_dir, cp):
    path = os.path.join(alaya_dir, '.import_checkpoint.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)


def clear_checkpoint(alaya_dir):
    path = os.path.join(alaya_dir, '.import_checkpoint.json')
    if os.path.exists(path):
        os.remove(path)


def collect_files(source):
    """Collect all importable files from source path."""
    files = []
    if os.path.isfile(source):
        if detect_format(source) is not None:
            files.append(source)
    elif os.path.isdir(source):
        for root, dirs, fnames in os.walk(source):
            for f in sorted(fnames):
                fpath = os.path.join(root, f)
                if detect_format(fpath) is not None:
                    files.append(fpath)
    return files


def slug_from_filename(filename):
    """Generate a clean slug from a filename."""
    name = os.path.splitext(filename)[0]
    return slugify(name)


def check_existing(wiki_dir, slug):
    """Check if a card with this slug already exists in any category."""
    if not os.path.isdir(wiki_dir):
        return False
    for entry in os.listdir(wiki_dir):
        cat_path = os.path.join(wiki_dir, entry)
        if os.path.isdir(cat_path):
            candidate = os.path.join(cat_path, slug + '.md')
            if os.path.exists(candidate):
                return True
    return False


def main():
    source, category, wiki_dir, alaya_dir = parse_args()

    if not source:
        print('Usage: python scripts/batch_import.py <source_dir_or_file> [--category cat]')
        sys.exit(1)

    if not os.path.exists(source):
        print(f'Not found: {source}')
        sys.exit(1)

    today = datetime.now().strftime('%Y-%m-%d')

    # Collect files
    files = collect_files(source)
    if not files:
        print(f'No importable files found in: {source}')
        print('  Supported: .md, .txt, .pdf')
        sys.exit(0)

    # Determine category
    if not category:
        # Guess from source directory name
        category = slugify(os.path.basename(os.path.abspath(source)))
        print(f'Auto-detected category: {category}')

    cat_slug = slugify(category)
    cat_dir = os.path.join(wiki_dir, cat_slug)
    os.makedirs(cat_dir, exist_ok=True)

    # Load checkpoint for resume
    cp = load_checkpoint(alaya_dir)
    if cp and cp.get('source') == os.path.abspath(source):
        completed = set(cp.get('completed', []))
        print(f'Resuming from checkpoint: {len(completed)} already imported')
    else:
        cp = {'source': os.path.abspath(source), 'category': cat_slug, 'completed': [], 'total': len(files)}
        completed = set()

    imported = 0
    skipped = 0
    unsupported = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        slug = slug_from_filename(fname)

        # Idempotent skip
        if slug in completed:
            skipped += 1
            continue

        # Dedup against existing cards
        if check_existing(wiki_dir, slug):
            skipped += 1
            cp['completed'].append(slug)
            continue

        # Extract text
        text = extract_text(fpath)
        if text is None:
            print(f'  [unsupported] {fname}')
            print(get_agent_template(fpath, today))
            unsupported += 1
            continue

        # Build wiki card
        result = read_frontmatter(fpath)
        if result:
            # Source file has YAML — inject Alaya fields
            content, yaml_str, dash = result
            title = extract_title(yaml_str, slug)
            tags = get_tags(yaml_str)
            new_yaml = inject_metadata(yaml_str, {'last_activated': today, 'created_by': 'system'})
            card_content = rebuild_content(new_yaml, dash, content)
        else:
            # No YAML — create card with full frontmatter
            title = slug
            tags = []
            card_content = (
                f'---\ntitle: "{title}"\nseed_type: REFINED\ncreated_by: system\n'
                f'strength: 0.5\nlast_activated: {today}\n'
                f'activation_count: 0\nhalf_life: 30\n---\n\n{text}'
            )

        # Write to wiki/{category}/{slug}.md
        dest = os.path.join(cat_dir, slug + '.md')
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(card_content)

        imported += 1
        cp['completed'].append(slug)

        # Save checkpoint after each file (crash-safe)
        cp['total'] = len(files)
        save_checkpoint(alaya_dir, cp)

    # Clear checkpoint on success
    clear_checkpoint(alaya_dir)

    print(f'\nImport complete:')
    print(f'  Category: {cat_slug}')
    print(f'  Imported: {imported}')
    print(f'  Skipped (existing): {skipped}')
    print(f'  Unsupported: {unsupported}')
    if imported > 0:
        print(f'\nNext: python scripts/build_index.py --category {cat_slug}')


if __name__ == '__main__':
    main()
