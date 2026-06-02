# Alaya · Format Converter
# Zero-dependency format conversion for wiki card import.
# Handles MD/TXT natively, PDF via PyMuPDF (optional).
# Unsupported formats return None with Agent guidance template.

import os, sys

AGENT_TEMPLATE = """\
Unsupported format: {filename}
Agent: Please read this file and output in the following format:

---
title: "(document title)"
type: paper
created: {date}
source: "{source}"
tags: [(3-5 topic tags)]
seed_type: REFINED
created_by: system
strength: 0.5
last_activated: {date}
activation_count: 0
half_life: 30
---

# (Title)

## Summary
(2-3 sentence summary)

## Key Points
- (point 1)
- (point 2)

## Content
(Core content, preserve original structure)

Save to: wiki/{{category}}/{{slug}}.md
Then run: python scripts/build_index.py --category {{category}}
"""


def detect_format(filepath):
    """Return format type string or None for unsupported formats."""
    ext = os.path.splitext(filepath)[1].lower()
    formats = {
        '.md': 'markdown',
        '.txt': 'text',
        '.pdf': 'pdf',
    }
    return formats.get(ext)


def extract_text(filepath, max_chars=None):
    """Extract text content from file. Returns str or None.

    When max_chars is None (default), reads the entire file.
    When set to a positive integer, limits extraction and prints a warning to stderr if truncated.
    """
    fmt = detect_format(filepath)
    if fmt in ('markdown', 'text'):
        text = _read_direct(filepath, max_chars)
    elif fmt == 'pdf':
        text = _read_pdf(filepath, max_chars)
    else:
        text = None

    if text is not None and max_chars is not None and len(text) >= max_chars:
        print(f"Warning: Content truncated at {max_chars} characters. "
              f"Use --max-chars N to increase or --mode full to extract entire file.",
              file=sys.stderr)
    return text


def extract_metadata(filepath):
    """Try to extract document metadata. Returns dict with available fields."""
    fmt = detect_format(filepath)
    meta = {
        'title': os.path.splitext(os.path.basename(filepath))[0],
        'source': filepath,
    }
    if fmt == 'pdf':
        return _pdf_metadata(filepath, meta)
    return meta


def get_agent_template(filepath, date_str=''):
    """Return Agent guidance template for unsupported formats."""
    from datetime import datetime
    return AGENT_TEMPLATE.format(
        filename=os.path.basename(filepath),
        date=date_str or datetime.now().strftime('%Y-%m-%d'),
        source=filepath,
    )


def _read_direct(filepath, max_chars):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read(max_chars) if max_chars is not None else f.read()
    except (UnicodeDecodeError, IOError):
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read(max_chars) if max_chars is not None else f.read()
        except IOError:
            return None


def _read_pdf(filepath, max_chars):
    try:
        import fitz
    except ImportError:
        return None
    try:
        doc = fitz.open(filepath)
        text_parts = []
        total = 0
        for page in doc:
            t = page.get_text()
            text_parts.append(t)
            total += len(t)
            if max_chars is not None and total >= max_chars:
                break
        doc.close()
        full = '\n'.join(text_parts)
        return full if max_chars is None else full[:max_chars]
    except Exception:
        return None


def _pdf_metadata(filepath, meta):
    try:
        import fitz
        doc = fitz.open(filepath)
        pdf_meta = doc.metadata or {}
        if pdf_meta.get('title'):
            meta['title'] = pdf_meta['title']
        if pdf_meta.get('author'):
            meta['author'] = pdf_meta['author']
        doc.close()
    except (ImportError, Exception):
        pass
    return meta
