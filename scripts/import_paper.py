# Alaya · Paper Import (v1.9)
# Import a single paper from arXiv URL or local file into wiki/{category}/.
# Three modes: info (default, outputs JSON metadata), full (extract + save).
# Mode summary is handled by LLM reading templates/ directly.
#
# Usage:
#   python scripts/import_paper.py <url_or_path> --mode info [--category cat] [--wiki dir]
#   python scripts/import_paper.py <url_or_path> --mode full [--category cat] [--wiki dir]

import json, os, re, sys, shutil, urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import slugify, extract_description_from_body
from lib.format_converter import detect_format, extract_text, extract_metadata, get_agent_template

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_TEMPLATE_DIR = os.path.join(PKG_ROOT, 'templates')


def parse_args():
    args = sys.argv[1:]
    source = None
    category = None
    wiki_dir = 'wiki'
    mode = 'info'           # info | full
    content_type = None     # paper | news | other
    max_chars = 2000
    template_dir = DEFAULT_TEMPLATE_DIR

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = args[i + 1]
            i += 2
        elif args[i] == '--mode' and i + 1 < len(args):
            mode = args[i + 1].lower()
            if mode not in ('info', 'full'):
                print(f'Invalid mode: {mode}. Use info or full.')
                sys.exit(1)
            i += 2
        elif args[i] == '--type' and i + 1 < len(args):
            content_type = args[i + 1].lower()
            if content_type not in ('paper', 'news', 'other'):
                print(f'Invalid type: {content_type}. Use paper, news, or other.')
                sys.exit(1)
            i += 2
        elif args[i] == '--max-chars' and i + 1 < len(args):
            try:
                max_chars = int(args[i + 1])
                if max_chars < 100:
                    print('Warning: max-chars < 100 may be too short. Using 100.')
                    max_chars = 100
            except ValueError:
                print(f'Invalid max-chars: {args[i+1]}')
                sys.exit(1)
            i += 2
        elif args[i] == '--template-dir' and i + 1 < len(args):
            template_dir = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            if source is None:
                source = args[i]
            i += 1
        else:
            i += 1

    if not source:
        print('Usage: python scripts/import_paper.py <arxiv_url_or_file> --mode info|full [--category cat] [--type paper|news|other] [--max-chars N] [--wiki dir]')
        print('')
        print('Modes:')
        print('  info    (default) Output JSON metadata about the file for LLM consumption')
        print('  full    Extract full text and save as wiki card (no truncation)')
        print('')
        print('Summary mode is handled by the LLM:')
        echo_llm_instructions(template_dir)
        sys.exit(1)

    return source, category, wiki_dir, mode, content_type, max_chars, template_dir


def echo_llm_instructions(template_dir):
    """Print LLM instruction block for summary-mode workflow."""
    templates = {
        'paper': os.path.join(template_dir, 'paper_summary.md'),
        'news': os.path.join(template_dir, 'news_summary.md'),
        'other': os.path.join(template_dir, 'other_summary.md'),
    }
    print('-' * 60)
    print('LLM Summary Workflow (for Agent guidance):')
    print('')
    print('1. Call: python scripts/import_paper.py <file> --mode info')
    print('   -> Get JSON metadata (title, char count, preview)')
    print('')
    print('2. Ask user: "Detected document (type_hint, N chars). (1) Summary (2) Full extract"')
    print('   If summary, ask: "Max chars? (default 2000)"')
    print('')
    print('3. Full mode: python scripts/import_paper.py <file> --mode full')
    print('   -> Script saves the complete card directly.')
    print('')
    print('4. Summary mode (LLM fills template):')
    print('   -> Read the appropriate template:')
    for tname, tpath in templates.items():
        exists = '[OK]' if os.path.exists(tpath) else '[--]'
        print(f'     {exists} templates/{tname}_summary.md')
    print('   -> Summarize extracted text into template structure')
    print('   -> Write wiki/{category}/{slug}.md with the filled content')
    print('   -> Run: python scripts/build_index.py --category {cat}')
    print('')
    print('Character limit: Align with user preference (default 2000)')
    print('  - User can say "3000 chars" -> set --max-chars 3000')
    print('  - User can say "full text" -> use --mode full instead')
    print('-' * 60)


def extract_arxiv_id(source):
    m = re.search(r'arxiv\.org/abs/(\d+\.\d+)', source)
    if m:
        return m.group(1)
    # Only match arXiv ID patterns when preceded by arxiv context
    m = re.search(r'(?:arxiv\.org/abs/|arXiv:)(\d{4}\.\d{4,5})(?:v\d+)?', source)
    if m:
        return m.group(1)
    return None


def fetch_arxiv_title(arxiv_id):
    try:
        api_url = f'https://export.arxiv.org/api/query?id_list={arxiv_id}'
        req = urllib.request.urlopen(api_url, timeout=10)
        data = req.read().decode('utf-8')
        m = re.search(r'<title>(.+?)</title>', data)
        if m:
            title = m.group(1).strip()
            return re.sub(r'\s+', ' ', title)
    except Exception:
        pass
    return None


def heuristic_type(text, source):
    """Guess content type: paper, news, or other."""
    # arXiv source → paper
    if re.search(r'arxiv\.org', source) or re.search(r'\d{4}\.\d{4,5}', source):
        return 'paper'
    # Check for typical paper patterns: references, DOI, abstract keyword
    paper_signals = 0
    if re.search(r'references?\s*\[', text[:3000], re.IGNORECASE):
        paper_signals += 1
    if re.search(r'doi:\s*10\.\d{4,}', text[:2000], re.IGNORECASE):
        paper_signals += 1
    if re.search(r'^abstract\b', text[:500], re.IGNORECASE):
        paper_signals += 1
    if paper_signals >= 2:
        return 'paper'
    # News signals: dateline patterns
    news_signals = 0
    if re.search(r'(?:^|\n)[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)?\s*[—–-]\s*', text[:500]):
        news_signals += 1
    if re.search(r'(?:reported|announced|according to|said)\b', text[:2000], re.IGNORECASE):
        news_signals += 1
    if news_signals >= 2:
        return 'news'
    return 'other'


def mode_info(source, category, wiki_dir, content_type, max_chars, template_dir):
    """--mode info: Output JSON metadata about the file for LLM to act on."""
    today = datetime.now().strftime('%Y-%m-%d')
    title = None
    source_url = source

    # arXiv URL handling
    arxiv_id = extract_arxiv_id(source)
    if arxiv_id:
        source_url = f'https://arxiv.org/abs/{arxiv_id}'
        title = fetch_arxiv_title(arxiv_id)

    if not title:
        if os.path.exists(source):
            meta = extract_metadata(source)
            title = meta.get('title')
        else:
            title = os.path.splitext(os.path.basename(source))[0]

    # Extract text for analysis
    text = None
    text_preview = ''
    char_count = 0
    if os.path.exists(source):
        fmt = detect_format(source)
        if fmt:
            text = extract_text(source)
            if text:
                char_count = len(text)
                text_preview = text[:500]
        else:
            # Unsupported format — include agent template path
            info = {
                'title': title,
                'source': source_url,
                'type_hint': 'other',
                'chars': 0,
                'format': 'unsupported',
                'preview': '',
                'agent_template': get_agent_template(source, today),
            }
            print(json.dumps(info, ensure_ascii=False, indent=2))
            return

    # Heuristic type detection
    if not content_type and text:
        content_type = heuristic_type(text, source)

    # Recommendation
    if char_count == 0:
        recommendation = 'unsupported_format'
    elif char_count <= max_chars:
        recommendation = 'full'
    else:
        recommendation = 'summary'

    info = {
        'title': title or os.path.splitext(os.path.basename(source))[0],
        'source': source_url,
        'type_hint': content_type or 'other',
        'chars': char_count,
        'path': source,
        'preview': text_preview,
        'recommendation': recommendation,
        'date': today,
    }

    print(json.dumps(info, ensure_ascii=False, indent=2))


def mode_full(source, category, wiki_dir, content_type, max_chars, template_dir):
    """--mode full: Extract full text and save as wiki card (no truncation)."""
    today = datetime.now().strftime('%Y-%m-%d')
    title = None
    source_url = source

    # arXiv
    arxiv_id = extract_arxiv_id(source)
    if arxiv_id:
        source_url = f'https://arxiv.org/abs/{arxiv_id}'
        title = fetch_arxiv_title(arxiv_id)

    if not title:
        title = os.path.splitext(os.path.basename(source))[0]

    slug = slugify(title)
    if not category:
        category = slugify(os.path.dirname(os.path.abspath(source)) or 'uncategorized')
        print(f'Auto-detected category: {category}')

    cat_slug = slugify(category)
    cat_dir = os.path.join(wiki_dir, cat_slug)
    os.makedirs(cat_dir, exist_ok=True)

    dest = os.path.join(cat_dir, slug + '.md')

    # Check existing
    if os.path.exists(dest):
        print(f'Card already exists: {dest}')
        return

    # Try to extract text
    text = None
    if os.path.exists(source):
        fmt = detect_format(source)
        if fmt:
            text = extract_text(source, max_chars=None)  # full mode: always read entire file
            if text is None:
                print(get_agent_template(source, today))
                return
        else:
            print(get_agent_template(source, today))
            return
    else:
        # Remote source without local file — can't extract
        print(f'File not found: {source}')
        return

    # Heuristic type detection
    if not content_type:
        content_type = heuristic_type(text, source)

    # Detect content type for frontmatter
    fm_type = {'paper': 'paper', 'news': 'news', 'other': 'note'}.get(content_type, 'note')

    # Build wiki card with FULL text
    body = (
        f'# {title}\n\n'
        f'> Imported from: {source_url}\n'
        f'\n'
        f'## Content\n\n'
        f'{text}\n'
    )

    # Determine source type and handle file copy for local sources
    source_file_val = ''
    source_url_val = source_url
    source_type_val = 'url'

    if os.path.exists(source):
        # Local file — determine type by extension
        ext = os.path.splitext(source)[1].lower()
        if ext in ('.pdf',):
            source_type_val = 'pdf'
        elif ext in ('.md',):
            source_type_val = 'md'
        elif ext in ('.txt',):
            source_type_val = 'txt'
        else:
            source_type_val = 'local'

        # Copy to raw/ directory for persistent storage and deep read
        raw_dir = 'raw'
        os.makedirs(raw_dir, exist_ok=True)
        raw_dest = os.path.join(raw_dir, slug + ext)
        try:
            shutil.copy2(source, raw_dest)
            source_file_val = raw_dest  # e.g. "raw/my-paper.pdf"
            print(f'  Source file saved: {raw_dest}')
        except (IOError, OSError) as e:
            print(f'  (Note: could not copy source file: {e})')
    elif arxiv_id:
        source_url_val = f'https://arxiv.org/abs/{arxiv_id}'
        source_type_val = 'url'

    # Extract description from body text (v2.0 requirement)
    desc = extract_description_from_body(body)
    desc_line = f'\ndescription: "{desc}"' if desc else ''

    # Build source fields for frontmatter
    source_file_line = f'source_file: "{source_file_val}"\n' if source_file_val else ''
    source_type_line = f'source_type: {source_type_val}\n' if source_type_val else ''

    card_content = (
        f'---\n'
        f'title: "{title}"\n'
        f'type: {fm_type}\n'
        f'created: {today}\n'
        f'source: "{source_url_val}"\n'
        f'{source_file_line}'
        f'{source_type_line}'
        f'tags: [imported]\n'
        f'seed_type: REFINED\n'
        f'created_by: system\n'
        f'strength: 0.5\n'
        f'last_activated: {today}\n'
        f'activation_count: 0\n'
        f'half_life: 30{desc_line}\n'
        f'---\n\n'
        f'{body}'
    )

    with open(dest, 'w', encoding='utf-8') as f:
        f.write(card_content)

    print(f'Card created: {dest}')
    print(f'Source: {source_url}')
    print(f'Content: {len(text)} characters')
    print(f'\nNext: python scripts/build_index.py --category {cat_slug}')


def main():
    source, category, wiki_dir, mode, content_type, max_chars, template_dir = parse_args()

    if mode == 'info':
        mode_info(source, category, wiki_dir, content_type, max_chars, template_dir)
    elif mode == 'full':
        mode_full(source, category, wiki_dir, content_type, max_chars, template_dir)


if __name__ == '__main__':
    main()
