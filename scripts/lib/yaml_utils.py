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


def get_all_cards(wiki_dir):
    """Walk wiki/{category}/*.md and return [(category, card_name, fpath)].

    Skips _category.md, index.md, log.md and non-directory entries.
    Category is the subfolder name (e.g. 'deep-learning').
    """
    skip = {'_category.md', 'index.md', 'log.md'}
    cards = []
    if not os.path.isdir(wiki_dir):
        return cards
    for entry in sorted(os.listdir(wiki_dir)):
        cat_path = os.path.join(wiki_dir, entry)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if fname.endswith('.md') and fname not in skip:
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
