# Alaya · Paper Import (v1.7)
# Import a single paper from arXiv URL or local file into wiki/{category}/.
# Uses format_converter for PDF extraction (PyMuPDF optional).
#
# Usage:
#   python scripts/import_paper.py <url_or_path> [--category cat] [--wiki dir]

import os, re, sys, urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import slugify
from lib.format_converter import detect_format, extract_text, extract_metadata, get_agent_template


def parse_args():
    args = sys.argv[1:]
    source = None
    category = None
    wiki_dir = 'wiki'

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            if source is None:
                source = args[i]
            i += 1
        else:
            i += 1

    return source, category, wiki_dir


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


def main():
    source, category, wiki_dir = parse_args()

    if not source:
        print('Usage: python scripts/import_paper.py <arxiv_url_or_file> [--category cat]')
        sys.exit(1)

    today = datetime.now().strftime('%Y-%m-%d')
    title = None
    source_url = source

    # Check for arXiv URL
    arxiv_id = None
    m = re.search(r'arxiv\.org/abs/(\d+\.\d+)', source)
    if m:
        arxiv_id = m.group(1)
        print(f'arXiv ID: {arxiv_id}')
        title = fetch_arxiv_title(arxiv_id)
        source_url = f'https://arxiv.org/abs/{arxiv_id}'

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
            text = extract_text(source)
            if text is None:
                print(get_agent_template(source, today))
                return
        else:
            print(get_agent_template(source, today))
            return

    # Build wiki card
    if text:
        abstract_section = '\n## Abstract\n\n' + text[:2000] + '\n'
    else:
        abstract_section = '\n## Abstract\n\n(To be filled)\n'

    card_content = (
        f'---\ntitle: "{title}"\ntype: paper\n'
        f'created: {today}\nsource: "{source_url}"\n'
        f'tags: [imported]\nseed_type: REFINED\n'
        f'created_by: system\nstrength: 0.5\n'
        f'last_activated: {today}\nactivation_count: 0\nhalf_life: 30\n---\n\n'
        f'# {title}\n\n'
        f'> Imported from: {source_url}\n'
        f'{abstract_section}\n'
        f'## Notes\n\n'
    )

    with open(dest, 'w', encoding='utf-8') as f:
        f.write(card_content)

    print(f'Card created: {dest}')
    print(f'Source: {source_url}')
    print(f'\nNext: python scripts/build_index.py --category {cat_slug}')


if __name__ == '__main__':
    main()
