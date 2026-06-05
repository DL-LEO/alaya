# Alaya · Academic Batch Import
# Academic paper batch import with structured card generation.
# Supports PDF extraction, academic card template, and Alaya integration.
# 
# Usage:
#   python scripts/academic_import.py <source_dir> [--category cat] [--wiki dir] [--alaya dir]

import json, os, re, shutil, sys
from datetime import datetime
from pathlib import Path
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import (
    read_frontmatter, get_field, get_field_float, set_field,
    inject_metadata, rebuild_content, slugify, get_tags, extract_title,
    extract_description_from_body
)
from lib.format_converter import detect_format, extract_text


def parse_args():
    args = sys.argv[1:]
    source = None
    category = None
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'
    max_chars = None
    dry_run = False
    skip_existing = True
    parallel = False
    workers = None

    def _need_val(flag, val):
        if val is not None and val.startswith('--'):
            print(f"[academic_import] ERROR: {flag} requires a value, got '{val}'", file=sys.stderr)
            sys.exit(1)
        return val

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = _need_val('--category', args[i + 1]); i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = _need_val('--wiki', args[i + 1]); i += 2
        elif args[i] == '--alaya' and i + 1 < len(args):
            alaya_dir = _need_val('--alaya', args[i + 1]); i += 2
        elif args[i] == '--max-chars' and i + 1 < len(args):
            try:
                max_chars = int(args[i + 1])
            except ValueError:
                print(f'Invalid max-chars: {args[i+1]}')
                sys.exit(1)
            i += 2
        elif args[i] == '--dry-run':
            dry_run = True
            i += 1
        elif args[i] == '--force-all':
            skip_existing = False
            i += 1
        elif args[i] == '--parallel':
            parallel = True
            i += 1
        elif args[i] == '--workers' and i + 1 < len(args):
            try:
                workers = int(args[i + 1])
                if workers < 1:
                    print(f'Workers must be >= 1, got: {workers}')
                    sys.exit(1)
            except ValueError:
                print(f'Invalid workers: {args[i+1]}')
                sys.exit(1)
            i += 2
        elif not args[i].startswith('--'):
            if source is None:
                source = args[i]
            i += 1
        else:
            print(f"[academic_import] WARNING: unknown flag '{args[i]}' (ignored)", file=sys.stderr)
            i += 1

    return source, category, wiki_dir, alaya_dir, max_chars, dry_run, skip_existing, parallel, workers


def slug_from_filename(filename):
    """
    Generate a clean URL-friendly slug from a PDF filename.
    Adapted from wiki-card-batch-generator logic.
    """
    # Remove .pdf extension
    name = filename
    if name.lower().endswith('.pdf'):
        name = name[:-4]

    # Remove common prefixes
    prefixes = ["A ", "A_", "An ", "The ", "the "]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break

    # Replace Chinese/special chars with hyphens
    replacements = {
        '：': '-', '，': '-', '。': '-', '、': '-',
        '（': '-', '）': '-', '《': '', '》': '',
        ' ': '-', '_': '-', '--': '-',
        ':': '-', ',': '-', '.': '-',
        '?': '', '!': '', ';': '-',
        '"': '', "'": '', '(': '-', ')': '-',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Collapse multiple hyphens
    while '--' in name:
        name = name.replace('--', '-')

    # Remove leading/trailing hyphens
    name = name.strip('-')

    # Keep short slug (max 6 meaningful words)
    parts = [p for p in name.split('-') if p]
    short_words = {'for', 'and', 'the', 'of', 'in', 'on', 'by', 'to', 'a', 'an', 'is', 'as', 'at', 'with', 'from'}
    filtered = []
    for p in parts:
        if p.lower() in short_words and len(parts) > 5:
            continue
        filtered.append(p)

    # Truncate to max 6 words
    if len(filtered) > 6:
        filtered = filtered[:6]

    slug = '-'.join(filtered)

    # Handle edge case: empty slug after processing
    if not slug:
        slug = "paper"

    return slug


def collect_pdf_files(source_dir):
    """Recursively collect all PDF files from source directory."""
    pdfs = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    return sorted(pdfs)


def get_existing_slugs(wiki_dir):
    """Collect all existing card slugs from wiki directory."""
    slugs = set()
    if not os.path.isdir(wiki_dir):
        return slugs

    for entry in os.listdir(wiki_dir):
        cat_path = os.path.join(wiki_dir, entry)
        if os.path.isdir(cat_path):
            for f in os.listdir(cat_path):
                if f.endswith('.md') and f not in ('index.md', 'log.md'):
                    slugs.add(f[:-3])  # Remove .md
    return slugs


def generate_academic_card(title, text, pdf_path, slug, tags=None, created=None):
    """
    Generate academic card content using structured template.
    Template adapted from wiki-card-batch-generator.
    """
    today = created or datetime.now().strftime('%Y-%m-%d')
    tags_str = ', '.join(tags or ['paper', 'imported'])

    card_content = f'''---
title: "{title}"
type: paper
created: {today}
updated: {today}
source_pdf: "{pdf_path}"
tags: [{tags_str}]
---

# {title}

## Abstract
[PDF文本提取的摘要内容]

## Key Points
- [从PDF中提取的关键点1]
- [从PDF中提取的关键点2]

## Content
{text[:2000]}...

## 原始PDF
[📄 打开原始PDF](file:///{pdf_path})
'''
    return card_content


def process_single_pdf(pdf_data):
    """
    Worker function for parallel processing.
    Processes a single PDF and returns result dict.
    """
    pdf_path, slug, category, wiki_dir, alaya_dir, max_chars, skip_existing, existing_slugs = pdf_data

    try:
        # Check if exists
        if skip_existing and slug in existing_slugs:
            return {'slug': slug, 'status': 'skipped', 'reason': 'already exists'}

        # Extract text
        text = extract_text(pdf_path, max_chars=max_chars)
        if text is None:
            return {'slug': slug, 'status': 'error', 'reason': 'PDF extraction failed'}

        if not text or len(text.strip()) < 50:
            return {'slug': slug, 'status': 'error', 'reason': 'Extracted text too short'}

        # Generate title
        title = os.path.splitext(os.path.basename(pdf_path))[0]
        today = datetime.now().strftime('%Y-%m-%d')

        # Generate academic card
        card_content = generate_academic_card(
            title=title,
            text=text,
            pdf_path=pdf_path,
            slug=slug,
            tags=['paper', category],
            created=today
        )

        # Write to temp file
        temp_card_path = os.path.join(alaya_dir, f'.temp_{slug}.md')
        with open(temp_card_path, 'w', encoding='utf-8') as f:
            f.write(card_content)

        # Adapt card using post_process
        from post_process import adapt_card_format
        success, target_path, message = adapt_card_format(
            temp_card_path, category, wiki_dir, alaya_dir
        )

        # Clean up temp file
        try:
            os.remove(temp_card_path)
        except:
            pass

        if success:
            return {'slug': slug, 'status': 'success', 'target': target_path}
        else:
            return {'slug': slug, 'status': 'error', 'reason': message}

    except Exception as e:
        return {'slug': slug, 'status': 'error', 'reason': str(e)}


def generate_checkpoint_data(source_dir, category, total_pdfs, new_pdfs, skipped_pdfs):
    """Generate checkpoint data for academic import."""
    return {
        'source': os.path.abspath(source_dir),
        'category': category,
        'total': total_pdfs,
        'new': new_pdfs,
        'skipped': skipped_pdfs,
        'last_updated': datetime.now().isoformat(),
        'completed': []
    }


def save_checkpoint(alaya_dir, checkpoint_data):
    """Save checkpoint to alaya directory."""
    checkpoint_path = os.path.join(alaya_dir, '.academic_import_checkpoint.json')
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError):
        return False


def load_checkpoint(alaya_dir):
    """Load checkpoint from alaya directory."""
    checkpoint_path = os.path.join(alaya_dir, '.academic_import_checkpoint.json')
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, OSError, json.JSONDecodeError):
            pass
    return None


def clear_checkpoint(alaya_dir):
    """Clear checkpoint from alaya directory."""
    checkpoint_path = os.path.join(alaya_dir, '.academic_import_checkpoint.json')
    if os.path.exists(checkpoint_path):
        try:
            os.remove(checkpoint_path)
        except (IOError, OSError):
            pass


def main():
    source, category, wiki_dir, alaya_dir, max_chars, dry_run, skip_existing, parallel, workers = parse_args()

    if not source:
        print('Usage: python scripts/academic_import.py <source_dir> [--category cat] [--wiki dir] [--alaya dir] [--max-chars N] [--dry-run] [--force-all] [--parallel] [--workers N]')
        print('')
        print('Academic paper batch import with structured card generation.')
        print('  <source_dir>: Directory containing PDF files')
        print('  --category: Category for wiki organization (default: auto-detected)')
        print('  --wiki: Wiki directory (default: wiki)')
        print('  --alaya: Alaya directory (default: alaya)')
        print('  --max-chars: Maximum characters to extract from PDF (default: full)')
        print('  --dry-run: Show what would be done without writing')
        print('  --force-all: Process all PDFs, skip existing check')
        print('  --parallel: Enable parallel processing (multiprocessing)')
        print('  --workers N: Number of parallel workers (default: auto-detect)')
        sys.exit(1)

    if not os.path.exists(source):
        print(f'Error: Source directory not found: {source}')
        sys.exit(1)

    today = datetime.now().strftime('%Y-%m-%d')

    # Collect PDF files
    pdfs = collect_pdf_files(source)
    if not pdfs:
        print(f'No PDF files found in: {source}')
        sys.exit(0)

    print(f'Found {len(pdfs)} PDF files')

    # Determine category
    if not category:
        category = slugify(os.path.basename(os.path.abspath(source)))
        print(f'Auto-detected category: {category}')

    cat_slug = slugify(category)
    cat_dir = os.path.join(wiki_dir, cat_slug)
    os.makedirs(cat_dir, exist_ok=True)

    # Get existing slugs for deduplication
    existing_slugs = get_existing_slugs(wiki_dir)

    # Load checkpoint for resume
    checkpoint = load_checkpoint(alaya_dir)
    completed = set()
    if checkpoint and checkpoint.get('source') == os.path.abspath(source):
        completed = set(checkpoint.get('completed', []))
        print(f'Resuming from checkpoint: {len(completed)} already processed')

    # Initialize checkpoint
    checkpoint_data = generate_checkpoint_data(source, cat_slug, len(pdfs), 0, 0)

    # Process each PDF
    imported = 0
    skipped = 0
    errors = 0

    # Prepare PDF data for processing
    pdf_data_list = []
    for pdf_path in pdfs:
        filename = os.path.basename(pdf_path)
        slug = slug_from_filename(filename)

        # Skip if already completed
        if slug in completed:
            skipped += 1
            continue

        # Skip if exists and skip_existing is True
        if skip_existing and slug in existing_slugs:
            print(f'  ⏭  {slug}: already exists in wiki')
            skipped += 1
            checkpoint_data['skipped'] += 1
            continue

        pdf_data_list.append((pdf_path, slug, cat_slug, wiki_dir, alaya_dir, max_chars, skip_existing, existing_slugs))

    if not pdf_data_list:
        print('No new PDFs to process')
    elif parallel:
        # Parallel processing
        num_workers = workers or min(cpu_count(), 4)
        print(f'Processing {len(pdf_data_list)} PDFs with {num_workers} parallel workers...')

        results = []
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            for result in executor.map(process_single_pdf, pdf_data_list):
                results.append(result)
                # Print progress
                status_symbol = {'success': '✅', 'error': '❌', 'skipped': '⏭'}.get(result['status'], '•')
                print(f'  {status_symbol} {result["slug"]}: {result.get("reason", result["status"])}')

        # Process results
        for result in results:
            if result['status'] == 'success':
                imported += 1
                checkpoint_data['completed'].append(result['slug'])
                checkpoint_data['new'] += 1
            elif result['status'] == 'skipped':
                skipped += 1
            else:
                errors += 1
    else:
        # Sequential processing (original behavior)
        print(f'Processing {len(pdf_data_list)} PDFs sequentially...')

        for pdf_data in pdf_data_list:
            pdf_path = pdf_data[0]
            filename = os.path.basename(pdf_path)
            slug = pdf_data[1]

            print(f'  → Processing: {filename}')

            result = process_single_pdf(pdf_data)

            status_symbol = {'success': '✅', 'error': '❌', 'skipped': '⏭'}.get(result['status'], '•')
            print(f'    {status_symbol} {result["slug"]}: {result.get("reason", result["status"])}')

            if result['status'] == 'success':
                imported += 1
                checkpoint_data['completed'].append(slug)
                checkpoint_data['new'] += 1
            elif result['status'] == 'skipped':
                skipped += 1
            else:
                errors += 1

            # Save checkpoint after each import
            if not dry_run and result['status'] == 'success':
                save_checkpoint(alaya_dir, checkpoint_data)

    # Clear checkpoint on success
    if errors == 0:
        clear_checkpoint(alaya_dir)
        print('\n✅ All PDFs processed successfully, checkpoint cleared')
    else:
        print(f'\n⚠️  Completed with {errors} errors, checkpoint preserved for resume')

    # Summary
    print(f'\n📊 Import Summary:')
    print(f'  Category: {cat_slug}')
    print(f'  Imported: {imported}')
    print(f'  Skipped: {skipped}')
    print(f'  Errors: {errors}')
    print(f'  Total: {len(pdfs)}')

    if imported > 0:
        print(f'\n📝 Next steps:')
        print(f'  1. Review generated cards in: {cat_dir}/')
        print(f'  2. Build index: python scripts/build_index.py --category {cat_slug}')
        print(f'  3. Run perfume: python scripts/perfume.py')


if __name__ == '__main__':
    main()
