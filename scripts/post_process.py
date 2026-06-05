# Alaya · Post-Process for Academic Import
# Adapter layer that converts workbuddy academic cards to Alaya format.
# Handles PDF copying to raw/, YAML format conversion, and Alaya metadata injection.
# 
# Usage:
#   python scripts/post_process.py <card_path> [--category cat] [--wiki dir] [--alaya dir]

import json, os, re, shutil, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import (
    read_frontmatter, get_field, get_field_float, set_field,
    inject_metadata, rebuild_content, slugify, get_tags, extract_title,
    is_category_file,
)


def parse_args():
    args = sys.argv[1:]
    card_path = None
    category = None
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'
    dry_run = False

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
        elif args[i] == '--dry-run':
            dry_run = True
            i += 1
        elif not args[i].startswith('--'):
            if card_path is None:
                card_path = args[i]
            i += 1
        else:
            i += 1

    return card_path, category, wiki_dir, alaya_dir, dry_run


def copy_pdf_to_raw(pdf_source_path, slug, raw_dir='raw'):
    """
    Copy PDF from source path to raw/ directory.
    Returns relative path for YAML frontmatter (e.g. "raw/paper.pdf").
    Returns None if copy fails.
    """
    if not pdf_source_path or not os.path.exists(pdf_source_path):
        return None

    try:
        os.makedirs(raw_dir, exist_ok=True)
        ext = os.path.splitext(pdf_source_path)[1]
        raw_dest = os.path.join(raw_dir, slug + ext)

        if not os.path.exists(raw_dest):
            shutil.copy2(pdf_source_path, raw_dest)

        return raw_dest
    except (IOError, OSError) as e:
        print(f'  ⚠️  Could not copy PDF: {e}')
        return None


def adapt_card_format(card_path, category, wiki_dir='wiki', alaya_dir='alaya', dry_run=False):
    """
    Convert workbuddy academic card to Alaya format.
    Returns (success, target_path, message).
    """
    if not os.path.exists(card_path):
        return False, None, f'Card not found: {card_path}'

    result = read_frontmatter(card_path)
    if not result:
        return False, None, f'No YAML frontmatter in: {card_path}'

    content, yaml_str, dash = result
    today = datetime.now().strftime('%Y-%m-%d')

    # Extract existing fields
    title = get_field(yaml_str, 'title')
    tags = get_tags(yaml_str)
    pdf_path = get_field(yaml_str, 'source_pdf')

    # Generate slug from filename
    slug = os.path.basename(card_path).replace('.md', '')

    # Copy PDF to raw/
    raw_file_path = None
    if pdf_path:
        raw_file_path = copy_pdf_to_raw(pdf_path, slug)
        if raw_file_path:
            print(f'  ✅ PDF copied: {raw_file_path}')

    # Build new Alaya YAML frontmatter
    new_yaml_parts = [
        f'title: "{title or slug}"',
        f'seed_type: REFINED',
        f'created_by: academic_import',
        f'strength: 0.5',
        f'last_activated: {today}',
        f'activation_count: 0',
        f'half_life: 30',
    ]

    # Add source fields
    if raw_file_path:
        new_yaml_parts.append(f'source_file: "{raw_file_path}"')
        new_yaml_parts.append(f'source_type: pdf')
    elif pdf_path:
        # Fallback to original PDF path if copy failed
        new_yaml_parts.append(f'source_pdf: "{pdf_path}"')
        new_yaml_parts.append(f'source_type: pdf')

    # Add tags if present
    if tags:
        tags_str = str(tags).replace("'", '"')
        new_yaml_parts.append(f'tags: {tags_str}')

    # Preserve description if exists
    desc = get_field(yaml_str, 'description')
    if desc:
        new_yaml_parts.append(f'description: "{desc}"')

    # Preserve type if exists (e.g. 'type: paper')
    card_type = get_field(yaml_str, 'type')
    if card_type:
        new_yaml_parts.append(f'type: {card_type}')

    # Preserve created/updated if exist
    created = get_field(yaml_str, 'created')
    if created:
        new_yaml_parts.append(f'created: {created}')
    updated = get_field(yaml_str, 'updated')
    if updated:
        new_yaml_parts.append(f'updated: {updated}')

    new_yaml = '---\n' + '\n'.join(new_yaml_parts) + '\n---'

    # Preserve original body content
    body = content[dash + 3:].lstrip('\n')
    new_content = new_yaml + '\n\n' + body

    # Determine target path
    cat_slug = slugify(category or 'uncategorized')
    target_dir = os.path.join(wiki_dir, cat_slug)
    target_path = os.path.join(target_dir, slug + '.md')

    if dry_run:
        print(f'  [DRY-RUN] Would write: {target_path}')
        return True, target_path, 'Dry run successful'

    # Create target directory
    os.makedirs(target_dir, exist_ok=True)

    # Write adapted card
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  ✅ Card adapted: {target_path}')
        return True, target_path, 'Success'
    except (IOError, OSError) as e:
        return False, None, f'Write failed: {e}'


def batch_adapt_cards(card_paths, category, wiki_dir='wiki', alaya_dir='alaya', dry_run=False):
    """
    Adapt multiple cards in batch.
    Returns (success_count, fail_count, results).
    """
    results = []
    success_count = 0
    fail_count = 0

    for card_path in card_paths:
        success, target_path, message = adapt_card_format(
            card_path, category, wiki_dir, alaya_dir, dry_run
        )
        results.append({
            'source': card_path,
            'target': target_path,
            'success': success,
            'message': message
        })
        if success:
            success_count += 1
        else:
            fail_count += 1

    return success_count, fail_count, results


def main():
    card_path, category, wiki_dir, alaya_dir, dry_run = parse_args()

    if not card_path:
        print('Usage: python scripts/post_process.py <card_path> [--category cat] [--wiki dir] [--alaya dir] [--dry-run]')
        print('')
        print('Adapt workbuddy academic cards to Alaya format.')
        print('  <card_path>: Path to card or directory containing cards')
        print('  --category: Category slug for wiki organization')
        print('  --wiki: Wiki directory (default: wiki)')
        print('  --alaya: Alaya directory (default: alaya)')
        print('  --dry-run: Show what would be done without writing')
        sys.exit(1)

    if not os.path.exists(card_path):
        print(f'Error: Path not found: {card_path}')
        sys.exit(1)

    # If directory, batch process
    if os.path.isdir(card_path):
        card_paths = []
        for root, dirs, files in os.walk(card_path):
            for f in files:
                if f.endswith('.md') and f not in ('index.md', 'log.md') and not is_category_file(f):
                    card_paths.append(os.path.join(root, f))

        if not card_paths:
            print(f'No cards found in: {card_path}')
            sys.exit(0)

        print(f'Found {len(card_paths)} cards to adapt')
        success, fail, results = batch_adapt_cards(
            card_paths, category, wiki_dir, alaya_dir, dry_run
        )
        print(f'\nBatch adaptation complete:')
        print(f'  Success: {success}')
        print(f'  Failed: {fail}')
        if fail > 0:
            print('\nFailed cards:')
            for r in results:
                if not r['success']:
                    print(f'  - {r["source"]}: {r["message"]}')
    else:
        # Single card
        success, target_path, message = adapt_card_format(
            card_path, category, wiki_dir, alaya_dir, dry_run
        )
        if success:
            print(f'\n✅ Success: {target_path}')
        else:
            print(f'\n❌ Failed: {message}')
            sys.exit(1)


if __name__ == '__main__':
    main()
