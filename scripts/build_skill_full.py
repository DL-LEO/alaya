# Alaya · Build SKILL_FULL.md
# Merges SKILL.md + SKILL_GUIDE.md + SKILL_REF.md into a single file.
# Validates consistency: checks that every section in supplementary files
# has a concise version or pointer in SKILL.md.
#
# Usage: python scripts/build_skill_full.py [--check-only]
#   --check-only  Only validate consistency, don't write

import os, sys, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(SCRIPT_DIR)

SKILL_CORE = os.path.join(PKG_ROOT, 'SKILL.md')
SKILL_GUIDE = os.path.join(PKG_ROOT, 'SKILL_GUIDE.md')
SKILL_REF = os.path.join(PKG_ROOT, 'SKILL_REF.md')
SKILL_FULL = os.path.join(PKG_ROOT, 'SKILL_FULL.md')


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def strip_yaml_header(content):
    """Remove YAML frontmatter from a .md file, return (header, body)."""
    m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if m:
        return m.group(1), content[m.end():]
    return '', content


def extract_section_titles(content, source_name):
    """Extract ## and ### headings from content for validation."""
    titles = re.findall(r'^(#{2,3})\s+(.+)$', content, re.MULTILINE)
    return [(level, title.strip(), source_name) for level, title in titles]


def extract_batch_triggers(content):
    """Extract batch import trigger phrases from a markdown content.
    Returns set of Chinese trigger phrases (in quotes)."""
    triggers = set()
    for match in re.finditer(
        r'"([^"]*(?:批量导入|导入|LLM导入|PDF导入|学术批量)[^"]*)"',
        content
    ):
        triggers.add(match.group(1))
    return triggers


def validate_consistency(core_content, guide_content, ref_content):
    """
    Validate that every section title in GUIDE and REF has a
    corresponding pointer/mention in CORE.
    Returns list of warnings.
    """
    warnings = []

    # Extract section titles from GUIDE and REF
    guide_titles = extract_section_titles(guide_content, 'SKILL_GUIDE.md')
    ref_titles = extract_section_titles(ref_content, 'SKILL_REF.md')

    # Define known cross-references from SKILL.md to GUIDE/REF
    # (These are the intended pointers — if we find a section title
    #  that doesn't match any of these, warn.)
    known_core_refs_to_guide = [
        'post-init', 'operation guide', 'next step', 'SKILL_GUIDE',
        '构建', '导入', '角色', 'Obsidian', 'raw', '维护',
        '检查清单', '帮助', 'what you can do',
    ]
    known_core_refs_to_ref = [
        'SKILL_REF', '§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8',
        'Session Boundary', 'Persona JSON Schema', 'Persona Creation',
        'Paper Import', 'Script Reference', 'Refinement Prompt',
        'Deep Read Protocol', 'Batch Import', 'reference',
    ]

    for level, title, src in guide_titles:
        # Check if title (or key parts of it) appear in core_content
        words = set(title.lower().split()[:5])  # first 5 significant words
        found = False
        for w in words:
            if len(w) > 2 and w.lower() in core_content.lower():
                found = True
                break
        if not found:
            # Check against known refs
            for ref in known_core_refs_to_guide:
                if any(word.lower() in ref for word in words):
                    found = True
                    break
        if not found:
            warnings.append(
                f'[WARN] SKILL_GUIDE.md section "{title}" has no '
                f'obvious pointer in SKILL.md. '
                f'Consider adding a brief mention or cross-reference.'
            )

    for level, title, src in ref_titles:
        words = set(title.lower().split()[:5])
        found = False
        for w in words:
            if len(w) > 2 and w.lower() in core_content.lower():
                found = True
                break
        if not found:
            for ref in known_core_refs_to_ref:
                if any(word.lower() in ref for word in words):
                    found = True
                    break
        if not found:
            warnings.append(
                f'[WARN] SKILL_REF.md section "{title}" has no '
                f'obvious pointer in SKILL.md. '
                f'Consider adding a brief mention or cross-reference.'
            )

    # Batch import trigger consistency check
    # Triggers in SKILL.md command table must also appear in SKILL_REF.md §8
    # so the on-demand loading contract is fulfilled.
    core_triggers = extract_batch_triggers(core_content)
    ref_triggers = extract_batch_triggers(ref_content)

    only_in_core = core_triggers - ref_triggers
    if only_in_core:
        warnings.append(
            f'[WARN] Batch import triggers in SKILL.md command table '
            f'but NOT in SKILL_REF.md §8 trigger line: '
            f'{", ".join(sorted(only_in_core))}. '
            f'These triggers may fail to load the full protocol on-demand.'
        )

    return warnings


def merge_files():
    """Merge the three SKILL files into SKILL_FULL.md."""
    core = read_file(SKILL_CORE)
    guide = read_file(SKILL_GUIDE)
    ref = read_file(SKILL_REF)

    # Strip YAML headers from supplementary files (keep core's YAML)
    _, guide_body = strip_yaml_header(guide)
    _, ref_body = strip_yaml_header(ref)

    # Validate consistency
    warnings = validate_consistency(core, guide_body, ref_body)

    # Extract version from core
    version_m = re.search(r'version:\s*([\d.]+)', core)
    version = version_m.group(1) if version_m else 'unknown'

    merged = (
        f'---\n'
        f'name: Alaya (Full)\n'
        f'name_zh: 识海（完整版）\n'
        f'description: "Complete merged skill definition for single-file agent platforms. '
        f'Auto-generated from SKILL.md + SKILL_GUIDE.md + SKILL_REF.md."\n'
        f'version: {version}\n'
        f'author: Liang Shao\n'
        f'license: Apache-2.0\n'
        f'source_files:\n'
        f'  - SKILL.md\n'
        f'  - SKILL_GUIDE.md\n'
        f'  - SKILL_REF.md\n'
        f'generated_by: scripts/build_skill_full.py\n'
        f'---\n\n'
        f'<!-- ============================================================ -->\n'
        f'<!--  SKILL_FULL.md — auto-generated merged file                  -->\n'
        f'<!--  Do not edit directly. Edit SKILL.md, SKILL_GUIDE.md, or    -->\n'
        f'<!--  SKILL_REF.md and re-run:                                   -->\n'
        f'<!--    python scripts/build_skill_full.py                       -->\n'
        f'<!-- ============================================================ -->\n\n'
    )

    # Core section
    merged += '<!-- ###### CORE: SKILL.md ###### -->\n\n'
    # Remove YAML from core too, we already have our own
    _, core_body = strip_yaml_header(core)
    merged += core_body.strip() + '\n\n'

    # Guide section
    merged += '<!-- ###### GUIDE: SKILL_GUIDE.md ###### -->\n\n'
    merged += guide_body.strip() + '\n\n'

    # Reference section
    merged += '<!-- ###### REFERENCE: SKILL_REF.md ###### -->\n\n'
    merged += ref_body.strip() + '\n\n'

    return merged, warnings


def main():
    check_only = '--check-only' in sys.argv

    merged, warnings = merge_files()

    if warnings:
        print('=== Consistency Warnings ===')
        for w in warnings:
            print(f'  {w}')
        print(f'\nTotal: {len(warnings)} warnings')
        if check_only:
            return

    if check_only:
        print('Consistency check passed (no warnings).')
        return

    with open(SKILL_FULL, 'w', encoding='utf-8') as f:
        f.write(merged)

    lines = len(merged.split('\n'))
    size_kb = len(merged.encode('utf-8')) / 1024
    _, core_body = strip_yaml_header(read_file(SKILL_CORE))
    core_lines = len(core_body.split('\n'))

    print(f'SKILL_FULL.md written:')
    print(f'  Core:    ~{core_lines} lines')
    print(f'  Merged:  {lines} lines ({size_kb:.0f} KB)')
    print(f'  Warnings: {len(warnings)}')
    if warnings:
        print(f'  (Run with --check-only to validate without writing)')

    # Check total size
    if size_kb > 80:
        print(f'  ⚠ Size > 80 KB ({size_kb:.0f} KB). Consider whether all content is needed.')

    print('\nDone.')


if __name__ == '__main__':
    main()
