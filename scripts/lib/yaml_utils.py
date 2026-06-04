# Alaya · YAML Frontmatter Utilities
# Shared functions for reading/writing YAML frontmatter in wiki cards.

import os, re


METADATA_DEFAULTS = {
    "seed_type": "REFINED",
    "created_by": "system",
    "strength": "0.5",
    "activation_count": "0",
    "half_life": "30",
}


def read_frontmatter(filepath):
    """Read a wiki card and return (content, yaml_str, dash_pos) or None."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return None
    dash = content.find("---", 3)
    if dash < 0:
        return None
    return content, content[3:dash], dash


def get_field(yaml_str, field):
    """Extract a field's string value from YAML frontmatter."""
    m = re.search(rf'^{re.escape(field)}:\s*(.+?)\s*$', yaml_str, re.MULTILINE)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return None


def get_field_float(yaml_str, field):
    """Extract a float field from YAML frontmatter."""
    m = re.search(rf'^{re.escape(field)}:\s*([0-9.]+)', yaml_str, re.MULTILINE)
    if m:
        return float(m.group(1))
    return None


def set_field(yaml_str, field, value):
    """Update a field in YAML frontmatter, or append if missing."""
    pattern = re.compile(rf'^{re.escape(field)}:\s*.*$', re.MULTILINE)
    replacement = f"{field}: {value}"
    new_yaml = pattern.sub(replacement, yaml_str)
    if new_yaml == yaml_str and f"{field}:" not in yaml_str:
        new_yaml = yaml_str.rstrip() + f"\n{replacement}\n"
    return new_yaml


def inject_metadata(yaml_str, overrides=None):
    """Inject missing Alaya metadata fields into YAML frontmatter."""
    defaults = METADATA_DEFAULTS.copy()
    if overrides:
        defaults.update(overrides)

    yaml_lines = yaml_str.rstrip().split("\n")
    need_separator = False
    for line in reversed(yaml_lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or (line.startswith("  ") and stripped):
            need_separator = True
        break

    additions = []
    if need_separator:
        additions.append("")
    for key, val in defaults.items():
        if f"{key}:" not in yaml_str:
            additions.append(f"{key}: {val}")

    if additions:
        return yaml_str.rstrip() + "\n" + "\n".join(additions) + "\n"
    return yaml_str


def rebuild_content(yaml_str, dash_pos, original):
    """Rebuild file content from updated yaml_str."""
    return "---" + yaml_str + original[dash_pos:]


def extract_title(yaml_str, fallback=""):
    """Extract title from YAML frontmatter."""
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', yaml_str, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return fallback


def slugify(name):
    """Create a filesystem-safe slug from a name."""
    import re as _re
    s = name.lower().strip()
    s = _re.sub(r'[：，。、（）\[\]{}]', '-', s)
    s = _re.sub(r'[\\/:*?"<>|]', '-', s)
    s = _re.sub(r'[\s_]+', '-', s)
    s = _re.sub(r'-+', '-', s)
    s = s.strip('-')
    return s or 'untitled'


def persona_key(manas_dir, name):
    """Resolve any persona identifier to the canonical key (JSON filename base).

    Accepts: filename base, display name, Chinese name, slugified name.
    Resolution order:
      1. Filename match (case-insensitive): list manas/ and find matching .json
      2. Display name / Chinese name search across all persona JSONs
      3. Fallback: return slugified name

    Returns the canonical key (e.g. "feynman" for all of "Richard Feynman",
    "richard_feynman", "Feynman", "费曼").
    Uses os.listdir + case-insensitive comparison to return the ACTUAL filename
    base, not the input — correct on case-insensitive filesystems (Windows/macOS).
    """
    import json as _json

    if not name:
        return name

    slug = name.lower().replace(" ", "_").replace("'", "")
    name_lower = name.lower()

    if os.path.isdir(manas_dir):
        for f in os.listdir(manas_dir):
            if not f.endswith(".json") or f.endswith("_history.json"):
                continue
            key = f.replace(".json", "")
            key_lower = key.lower()

            # 1. Filename match (case-insensitive): "Feynman" matches "feynman.json"
            if key_lower == name_lower or key_lower == slug:
                return key

            # 2. Display name / Chinese name match (read JSON content)
            try:
                with open(os.path.join(manas_dir, f), "r", encoding="utf-8") as fp:
                    data = _json.load(fp)
                display = data.get("persona", "")
                display_zh = data.get("persona_zh", "")
                display_slug = display.lower().replace(" ", "_").replace("'", "")
                if display_slug == slug or display_zh == name:
                    return key
            except (_json.JSONDecodeError, IOError):
                pass

    # 3. Fallback: return slugified name
    return slug


def is_category_file(fname):
    """Check if a filename is a category file: {name}_category.md"""
    return fname.endswith('_category.md')


def category_file_for(cat_slug):
    """Return the category filename for a given category slug."""
    return f'{cat_slug}_category.md'


def get_all_cards(wiki_dir):
    """Walk wiki/{category}/*.md and return [(category, card_name, fpath)].

    Skips category files, index.md, log.md and non-directory entries.
    Category is the subfolder name (e.g. 'deep-learning').
    """
    cards = []
    if not os.path.isdir(wiki_dir):
        return cards
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith('.md') and fname != 'index.md' and fname != 'log.md' and not is_category_file(fname):
                card_name = fname[:-3]
                cards.append((entry, card_name, os.path.join(cat_path, fname)))
    return cards


def find_card(wiki_dir, card_name):
    """Search all category subfolders for a card. Returns fpath or None."""
    md_name = card_name if card_name.endswith('.md') else card_name + '.md'
    if not os.path.isdir(wiki_dir):
        return None
    for entry in os.listdir(wiki_dir):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        candidate = os.path.join(cat_path, md_name)
        if os.path.exists(candidate):
            return candidate
    return None


def get_description(yaml_str):
    """Extract description field from YAML frontmatter. Returns str or None."""
    return get_field(yaml_str, 'description')


def set_description(yaml_str, description):
    """Set description field in YAML frontmatter. Returns updated yaml_str."""
    return set_field(yaml_str, 'description', description)


def extract_description_from_body(body_text, max_length=120):
    """Extract a one-line description from card body text.

    Tries: 1) first blockquote line, 2) first non-empty non-heading paragraph.
    Returns empty string if nothing usable found.

    Args:
        body_text: The full body text of a card.
        max_length: Maximum character length for the extracted description (default 120).
    """
    lines = body_text.split('\n')

    # Try blockquote
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('> '):
            desc = stripped[2:].strip()
            if len(desc) > 10:
                return desc[:max_length]

    # Try first non-heading, non-empty paragraph
    para_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            if para_lines:
                desc = ' '.join(para_lines)
                if len(desc) > 10:
                    return desc[:max_length]
                para_lines = []
            continue
        para_lines.append(stripped)

    if para_lines:
        desc = ' '.join(para_lines)
        if len(desc) > 10:
            return desc[:max_length]

    return ''


def get_tags(yaml_str):
    """Extract tags from YAML frontmatter as a list of strings."""
    # Inline array: tags: [tag1, tag2]
    m = re.search(r'^tags:\s*\[(.+?)\]', yaml_str, re.MULTILINE)
    if m:
        return [t.strip().strip('"').strip("'") for t in m.group(1).split(",") if t.strip()]

    # Block array: tags:\n  - tag1\n  - tag2
    m = re.search(r'^tags:\s*$', yaml_str, re.MULTILINE)
    if m:
        tags = []
        for line in yaml_str[m.end():].split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip().strip('"').strip("'"))
            elif stripped and not line.startswith(" ") and not line.startswith("\t"):
                break
        return tags

    # Single value: tags: tag1
    m = re.search(r'^tags:\s*(\S+)', yaml_str, re.MULTILINE)
    if m:
        return [m.group(1).strip('"').strip("'")]

    return []
