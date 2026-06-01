# Alaya · Fix Links
# Detects and fixes broken [[wiki-links]] in knowledge cards (case-insensitive matching).
# Usage: python scripts/fix_links.py [wiki_dir]

import os, sys, re

wiki_dir = sys.argv[1] if len(sys.argv) > 1 else "wiki"

if not os.path.exists(wiki_dir):
    print(f"Directory not found: {wiki_dir}")
    sys.exit(1)

# Build card name index (case-insensitive) from category subfolders
SKIP_FILES_FIX = {"_category.md", "index.md", "log.md"}
card_names = {}
for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if fname.endswith(".md") and fname not in SKIP_FILES_FIX:
            name = fname.replace(".md", "")
            card_names[name.lower()] = name

fixed_count = 0
broken_links = []


def make_fix_link(file_card_names):
    count = [0]
    file_broken = []

    def fix_link(match):
        link = match.group(1)
        link_clean = link.split("|")[0].split("#")[0].strip()

        # Check if link target exists as-is (O(1) dict lookup)
        lower_link = link_clean.lower()
        if lower_link in file_card_names and file_card_names[lower_link] == link_clean:
            return match.group(0)

        # Try case-insensitive match
        if lower_link in file_card_names and file_card_names[lower_link] != link_clean:
            new_link = link.replace(link_clean, file_card_names[lower_link])
            count[0] += 1
            print(f"  Fixed: [[{link}]] -> [[{file_card_names[lower_link]}]]")
            return "[[" + new_link + "]]"

        file_broken.append(link_clean)
        return match.group(0)

    return fix_link, count, file_broken


for root, dirs, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith(".md") or fname in SKIP_FILES_FIX:
            continue

        fpath = os.path.join(root, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        fix_link, count, file_broken = make_fix_link(card_names)
        new_content = re.sub(r'\[\[([^\]]+?)\]\]', fix_link, content)

        if new_content != content:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)

        fixed_count += count[0]
        broken_links.extend(file_broken)

print(f"Links fixed (case-mismatch): {fixed_count}")
print(f"Broken links remaining: {len(broken_links)}")
if broken_links:
    print("First 10 broken links:")
    for link in broken_links[:10]:
        print(f"  [[{link}]]")
