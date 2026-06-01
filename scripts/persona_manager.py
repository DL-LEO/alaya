# Alaya · Persona Manager
# List, delete, edit, and clone persona configurations.
# Usage:
#   python scripts/persona_manager.py list [alaya_dir]
#   python scripts/persona_manager.py delete <name> [alaya_dir]
#   python scripts/persona_manager.py clone <source> <target> [alaya_dir]
#   python scripts/persona_manager.py edit <name> [alaya_dir]

import json, os, sys, shutil

def get_manas_dir(alaya_dir):
    d = os.path.join(alaya_dir, "manas")
    if not os.path.exists(d):
        print(f"manas/ directory not found in {alaya_dir}")
        sys.exit(1)
    return d


def find_persona(manas_dir, name):
    name_lower = name.lower().replace(" ", "_")
    for f in os.listdir(manas_dir):
        if f.endswith(".json"):
            fpath = os.path.join(manas_dir, f)
            with open(fpath, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if data.get("persona", "").lower().replace(" ", "_") == name_lower:
                return fpath, data
            if f.replace(".json", "").lower() == name_lower:
                return fpath, data
    return None, None


def cmd_list(alaya_dir):
    manas_dir = get_manas_dir(alaya_dir)
    files = [f for f in os.listdir(manas_dir) if f.endswith(".json") and not f.endswith("_history.json")]
    if not files:
        print("No personas found.")
        return

    print(f"{'Icon':<5} {'Name':<25} {'Lang':<6} {'Profile':<8} {'Interests'}")
    print("-" * 80)
    for f in sorted(files):
        with open(os.path.join(manas_dir, f), "r", encoding="utf-8") as fp:
            data = json.load(fp)
        icon = data.get("icon", "🤖")
        name = data.get("persona", f.replace(".json", ""))
        lang = data.get("language", "?")
        slug = f.replace(".json", "")
        profile_path = os.path.join(manas_dir, f"{slug}_profile.md")
        has_profile = "yes" if os.path.exists(profile_path) else ""
        foci = list(data.get("ego_vector", {}).get("interest_foci", {}).keys())
        interests = ", ".join(foci[:3])
        if len(foci) > 3:
            interests += "..."
        print(f"{icon:<5} {name:<25} {lang:<6} {has_profile:<8} {interests}")


def cmd_delete(alaya_dir, name):
    manas_dir = get_manas_dir(alaya_dir)
    fpath, data = find_persona(manas_dir, name)
    if not fpath:
        print(f"Persona '{name}' not found.")
        return

    confirm = input(f"Delete persona '{data.get('persona', name)}'? (y/n): ").strip()
    if confirm.lower() == "y":
        os.remove(fpath)
        print(f"Deleted: {fpath}")
        slug = os.path.basename(fpath).replace(".json", "")
        profile_path = os.path.join(os.path.dirname(fpath), f"{slug}_profile.md")
        if os.path.exists(profile_path):
            os.remove(profile_path)
            print(f"Deleted: {profile_path}")
    else:
        print("Cancelled.")


def cmd_clone(alaya_dir, source_name, target_name):
    manas_dir = get_manas_dir(alaya_dir)
    src_path, src_data = find_persona(manas_dir, source_name)
    if not src_path:
        print(f"Source persona '{source_name}' not found.")
        return

    # Clone and modify
    import copy
    new_data = copy.deepcopy(src_data)
    new_data["persona"] = target_name
    new_data["affinity"] = {}
    new_data["interaction_history"] = []

    target_fname = target_name.lower().replace(" ", "_").replace("'", "") + ".json"
    target_path = os.path.join(manas_dir, target_fname)

    if os.path.exists(target_path):
        print(f"Target '{target_name}' already exists at {target_path}")
        return

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print(f"Cloned '{source_name}' -> '{target_name}' at {target_path}")

    # Clone profile.md if it exists
    src_slug = os.path.basename(src_path).replace(".json", "")
    src_profile = os.path.join(manas_dir, f"{src_slug}_profile.md")
    if os.path.exists(src_profile):
        tgt_slug = target_fname.replace(".json", "")
        tgt_profile = os.path.join(manas_dir, f"{tgt_slug}_profile.md")
        shutil.copy2(src_profile, tgt_profile)
        print(f"Cloned profile: {tgt_profile}")


def cmd_edit(alaya_dir, name):
    manas_dir = get_manas_dir(alaya_dir)
    fpath, data = find_persona(manas_dir, name)
    if not fpath:
        print(f"Persona '{name}' not found.")
        return

    print(f"Editing: {data.get('persona', name)}")
    print(f"Current fields: {list(data.keys())}")
    print()
    print("What to edit?")
    print("  1. Language (current: {})".format(data.get("language", "?")))
    print("  2. Confidence (current: {})".format(data.get("confidence", "?")))
    print("  3. Omniview (current: {})".format(data.get("is_omniview", False)))
    print("  4. Interest foci")
    print("  5. Communication style")
    print("  6. Title/description")
    print("  7. Signature phrases (current: {} phrases)".format(len(data.get("signature_phrases", []))))
    print("  8. Domain scope")
    print("  9. Triggers")
    print("  10. Icon (current: {})".format(data.get("icon", "🤖")))
    print("  11. Edit profile.md (character definition)")
    print()

    choice = input("Choice [1-11]: ").strip()

    if choice == "1":
        lang = input(f"Language [zh/en, current: {data.get('language', '?')}]: ").strip()
        if lang in ("zh", "en"):
            data["language"] = lang
    elif choice == "2":
        conf = input(f"Confidence [0.0-1.0, current: {data.get('confidence', '?')}]: ").strip()
        try:
            data["confidence"] = max(0.0, min(1.0, float(conf)))
        except ValueError:
            pass
    elif choice == "3":
        omni = input(f"Omniview [y/n, current: {data.get('is_omniview', False)}]: ").strip()
        data["is_omniview"] = omni.lower() == "y"
    elif choice == "4":
        foci = data.get("ego_vector", {}).get("interest_foci", {})
        print(f"Current interests: {list(foci.keys())}")
        new_interests = input("New interests (comma-separated, or empty to keep): ").strip()
        if new_interests:
            new_foci = {}
            for i, interest in enumerate(new_interests.split(",")):
                key = interest.strip().lower().replace(" ", "_")
                if key:
                    val = max(0.5, 0.9 - i * 0.1)
                    new_foci[key] = {"value": val, "floor": 0.1}
            if new_foci:
                data.setdefault("ego_vector", {})["interest_foci"] = new_foci
    elif choice == "5":
        print(f"Current communication: {data.get('ego_vector', {}).get('communication', {})}")
        new_style = input("New style key (e.g. formal, casual): ").strip()
        if new_style:
            data.setdefault("ego_vector", {})["communication"] = {
                new_style.lower().replace(" ", "_"): {"value": 0.8, "floor": 0.1}
            }
    elif choice == "6":
        title = input(f"Title [current: {data.get('title', '')}]: ").strip()
        if title:
            data["title"] = title
        title_zh = input(f"Title ZH [current: {data.get('title_zh', '')}]: ").strip()
        if title_zh:
            data["title_zh"] = title_zh
    elif choice == "7":
        current = data.get("signature_phrases", [])
        print(f"Current phrases: {current}")
        new_phrases = input("New phrases (comma-separated, or empty to keep): ").strip()
        if new_phrases:
            data["signature_phrases"] = [p.strip() for p in new_phrases.split(",") if p.strip()]
    elif choice == "8":
        scope = data.get("domain_scope", {"owns": [], "shares": [], "defers_to": {}})
        print(f"Current owns: {scope.get('owns', [])}")
        print(f"Current shares: {scope.get('shares', [])}")
        print(f"Current defers_to: {scope.get('defers_to', {})}")
        owns = input("New owns (comma-separated, or empty to keep): ").strip()
        if owns:
            scope["owns"] = [o.strip().lower().replace(" ", "_") for o in owns.split(",") if o.strip()]
        data["domain_scope"] = scope
    elif choice == "9":
        trig = data.get("triggers", {"active": [], "passive": [], "emotions": []})
        print(f"Current active: {trig.get('active', [])}")
        print(f"Current passive: {trig.get('passive', [])}")
        print(f"Current emotions: {trig.get('emotions', [])}")
        active = input("New active triggers (comma-separated, or empty to keep): ").strip()
        if active:
            trig["active"] = [t.strip().lower() for t in active.split(",") if t.strip()]
        data["triggers"] = trig
    elif choice == "10":
        current = data.get("icon", "🤖")
        icon = input(f"Icon emoji [current: {current}]: ").strip()
        if icon:
            data["icon"] = icon
    elif choice == "11":
        slug = os.path.basename(fpath).replace(".json", "")
        profile_path = os.path.join(os.path.dirname(fpath), f"{slug}_profile.md")
        if os.path.exists(profile_path):
            print(f"Profile file: {profile_path}")
            print("Open this file in your editor to modify the character definition.")
        else:
            print("No profile.md found. Create one using the Persona Creation Protocol.")
            create = input("Create a skeleton profile.md? (y/n): ").strip()
            if create.lower() == "y":
                name_str = data.get("persona", slug)
                lines = [
                    "---",
                    f'summary: "{data.get("title", name_str)}"',
                    f"trigger_hints: {data.get('triggers', {}).get('active', [])[:3]}",
                    "---", "",
                    f"# {name_str}", "",
                    "## 核心人设", "",
                    f"**你是谁：** {data.get('title', name_str)}", "",
                    "**称呼方式：** （待补充）", "",
                    "**核心特质：**",
                    "- （待补充）", "",
                    "## 语言风格基调", "",
                    "### 比例", "- （待补充）", "",
                    "### 标志性用语",
                    f"- {', '.join(data.get('signature_phrases', []))}", "",
                    "### 说话习惯", "- （待补充）", "",
                    "## 使用场景", "",
                    f"1. 用户主动提到「{name_str}」", "",
                    "## 行为要求", "",
                    "1. 启用后全程以角色身份说话，不跳出角色", "",
                    "## 典型对话示例", "",
                    "### 场景一：xxx",
                    f"> 用户：xxx", f">", f"> {name_str}：xxx", "",
                ]
                with open(profile_path, "w", encoding="utf-8") as fp:
                    fp.write("\n".join(lines))
                print(f"Created: {profile_path}")
        return

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {fpath}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  python scripts/persona_manager.py list [alaya_dir]")
        print("  python scripts/persona_manager.py delete <name> [alaya_dir]")
        print("  python scripts/persona_manager.py clone <source> <target> [alaya_dir]")
        print("  python scripts/persona_manager.py edit <name> [alaya_dir]")
        sys.exit(1)

    cmd = args[0]
    if cmd == "list":
        alaya_dir = args[1] if len(args) > 1 else "alaya"
        cmd_list(alaya_dir)
    elif cmd == "delete":
        name = args[1] if len(args) > 1 else None
        alaya_dir = args[2] if len(args) > 2 else "alaya"
        if name:
            cmd_delete(alaya_dir, name)
    elif cmd == "clone":
        src = args[1] if len(args) > 1 else None
        tgt = args[2] if len(args) > 2 else None
        alaya_dir = args[3] if len(args) > 3 else "alaya"
        if src and tgt:
            cmd_clone(alaya_dir, src, tgt)
    elif cmd == "edit":
        name = args[1] if len(args) > 1 else None
        alaya_dir = args[2] if len(args) > 2 else "alaya"
        if name:
            cmd_edit(alaya_dir, name)
    else:
        print(f"Unknown command: {cmd}")
