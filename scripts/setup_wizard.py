# Alaya · Setup Wizard
# Guides new users through initial configuration via interview-style prompts.
# Usage: python scripts/setup_wizard.py

import json, os, shutil
from datetime import datetime

# Resolve paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(SCRIPT_DIR)

# ===== Persona Creation Interview (Q1~Q8) =====
def create_persona_interview(alaya_dir, default_language="zh"):
    print("\n  " + "-" * 40)
    print("  Persona Creation Interview")
    print("  " + "-" * 40)

    persona = {
        "version": 1,
        "created_at": datetime.now().strftime('%Y-%m-%d'),
        "is_omniview": False,
        "language": default_language,
        "affinity": {},
        "interaction_history": [],
        "confidence": 0.75,
        "mode_config": {"behavior": "auto", "auto_trigger_threshold": 0.7}
    }

    # Q1: Name
    print("\n  Q1: What is the persona's name?")
    name = input("  Name: ").strip()
    if not name:
        print("  Skipped. Persona not created.")
        return
    persona["persona"] = name

    # Q2: One-line description
    print("\n  Q2: Describe this persona in one sentence.")
    desc = input("  Description: ").strip()
    persona["title"] = desc if desc else f"{name}"

    # Q3: Interest areas (3-5 keywords)
    print("\n  Q3: What are this persona's interest areas? (3-5 keywords)")
    print("     e.g.: machine learning, philosophy, fault diagnosis, neural networks")
    interests = input("  Interests (comma-separated): ").strip()
    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    foci = {}
    for i, interest in enumerate(interest_list):
        val = max(0.5, 0.9 - i * 0.1)
        foci[interest.lower().replace(" ", "_")] = {"value": val, "floor": 0.1}
    if not foci:
        foci = {"general_knowledge": {"value": 0.7, "floor": 0.1}}
    persona["ego_vector"] = {
        "interest_foci": foci,
        "bias_dimensions": {"general": {"value": 0.7, "floor": 0.1}},
        "communication": {"default": {"value": 0.7, "floor": 0.1}}
    }

    # Q4: Language style
    print("\n  Q4: Language style?")
    print("     1. Casual / conversational")
    print("     2. Professional / academic")
    print("     3. Mixed (recommended)")
    style = input("  Choice [1/2/3, default: 3]: ").strip()
    style_map = {"1": "casual", "2": "professional", "3": "mixed"}
    style_key = style_map.get(style, "mixed")
    persona["ego_vector"]["communication"] = {
        style_key: {"value": 0.8, "floor": 0.1}
    }

    # Q5: Knowledge preference
    print("\n  Q5: Knowledge preference?")
    print("     1. Theory-oriented")
    print("     2. Practice-oriented")
    print("     3. Balanced (recommended)")
    pref = input("  Choice [1/2/3, default: 3]: ").strip()
    pref_vals = {"1": 0.9, "2": 0.9, "3": 0.8}
    pref_keys = {"1": "theory", "2": "practice", "3": "balanced"}
    pref_key = pref_keys.get(pref, "balanced")
    pref_val = pref_vals.get(pref, 0.8)
    persona["ego_vector"]["bias_dimensions"]["knowledge_preference"] = {"value": pref_val, "floor": 0.1}
    persona["ego_vector"]["bias_dimensions"]["knowledge_style"] = {
        pref_key: {"value": pref_val, "floor": 0.1}
    }

    # Q6: Special role?
    print("\n  Q6: Special role?")
    print("     1. Normal persona")
    print("     2. Omniview (can see all personas' conversations)")
    role = input("  Choice [1/2, default: 1]: ").strip()
    if role == "2":
        persona["is_omniview"] = True
        persona["title"] += " [Omniview]"
        print("  -> Omniview enabled")

    # Q7: Prototype floor values
    print("\n  Q7: Use recommended prototype floor values?")
    print("     (Floor = minimum value for each interest dimension,")
    print("      prevents persona from completely losing a trait)")
    use_rec = input("  y/n [default: y]: ").strip()
    if use_rec.lower() == "n":
        floor_val = input("  Custom floor value [0.05-0.3, default: 0.1]: ").strip()
        try:
            floor_val = float(floor_val)
            floor_val = max(0.05, min(0.3, floor_val))
        except ValueError:
            floor_val = 0.1
        for section in ["interest_foci", "bias_dimensions", "communication"]:
            for k in persona["ego_vector"].get(section, {}):
                persona["ego_vector"][section][k]["floor"] = floor_val
        print(f"  -> Floor set to {floor_val}")
    else:
        print("  -> Using recommended defaults (floor=0.1)")

    # Q8: Initial seeds from knowledge base?
    print("\n  Q8: Pre-populate initial seeds from knowledge base?")
    print("     (Matches interest areas against existing wiki cards)")
    seeds = input("  y/n [default: y]: ").strip()
    if seeds.lower() != "n":
        print("  -> Will link to matching cards on first search")
    else:
        print("  -> Starting from zero")

    # Q9: Icon
    print("\n  Q9: Icon emoji for this persona?")
    print("     (Single emoji used as visual marker in group discussions)")
    icon_input = input("  Icon (e.g. ⚛, 🌸, 🔮, or Enter for 🤖): ").strip()
    persona["icon"] = icon_input if icon_input else "🤖"

    # Q10: Signature phrases
    print("\n  Q10: Signature phrases / catchphrases?")
    print("     (Characteristic expressions that shape this persona's voice)")
    print("     e.g.: Let me think about this differently, The key insight is...")
    phrases_input = input("  Phrases (comma-separated, or Enter to skip): ").strip()
    if phrases_input:
        persona["signature_phrases"] = [p.strip() for p in phrases_input.split(",") if p.strip()]
    else:
        persona["signature_phrases"] = []

    # Q11: Domain scope
    print("\n  Q11: Domain ownership?")
    print("     Topics this persona exclusively handles (comma-separated)")
    owns_input = input("  Owns (Enter to skip): ").strip()
    domain = {}
    if owns_input:
        domain["owns"] = [o.strip().lower().replace(" ", "_") for o in owns_input.split(",") if o.strip()]
    else:
        domain["owns"] = list(foci.keys())[:2]  # Default: top 2 interests
    domain["shares"] = []
    domain["defers_to"] = {}
    persona["domain_scope"] = domain

    # Q12: Triggers
    print("\n  Q12: Trigger keywords?")
    print("     Keywords that make this persona proactively speak up")
    triggers_input = input("  Active triggers (comma-separated, or Enter to skip): ").strip()
    passive_input = input("  Passive triggers (comma-separated, or Enter to skip): ").strip()
    persona["triggers"] = {
        "active": [t.strip().lower() for t in triggers_input.split(",") if t.strip()] if triggers_input else [],
        "passive": [t.strip().lower() for t in passive_input.split(",") if t.strip()] if passive_input else [],
        "emotions": []
    }

    # Save JSON
    manas_dir = os.path.join(alaya_dir, "manas")
    os.makedirs(manas_dir, exist_ok=True)
    fname = name.lower().replace(" ", "_").replace("'", "")
    path = os.path.join(manas_dir, f"{fname}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(persona, f, ensure_ascii=False, indent=2)

    # Save profile.md
    profile_lines = [
        f"---",
        f'summary: "{desc}"',
        f"trigger_hints: {persona['triggers']['active'][:3]}",
        f"---",
        f"",
        f"# {name}",
        f"",
        f"## 核心人设",
        f"",
        f"**你是谁：** {desc}",
        f"",
        f"**称呼方式：** （待补充）",
        f"",
        f"**核心特质：**",
        f"- （待补充：3-5条核心特质）",
        f"",
        f"## 语言风格基调",
        f"",
        f"### 比例",
        f"- （待补充）",
        f"",
        f"### 标志性用语",
        f"- {', '.join(persona.get('signature_phrases', []))}",
        f"",
        f"### 说话习惯",
        f"- （待补充）",
        f"",
        f"## 使用场景",
        f"",
        f"1. 用户主动提到「{name}」",
        f"2. （待补充）",
        f"",
        f"## 行为要求",
        f"",
        f"1. 启用后全程以角色身份说话，不跳出角色",
        f"2. （待补充）",
        f"",
        f"## 典型对话示例",
        f"",
        f"### 场景一：xxx",
        f"> 用户：xxx",
        f">",
        f"> {name}：xxx",
        f"",
    ]
    profile_path = os.path.join(manas_dir, f"{fname}_profile.md")
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(profile_lines))

    print(f"\n  Persona '{name}' created!")
    print(f"     JSON: {path}")
    print(f"     Profile: {profile_path}")
    print(f"     Interests: {list(foci.keys())}")
    print(f"     Tip: Edit the profile.md to add rich character definition.")


# ===== Main Setup =====
print("=" * 50)
print("  Alaya · Setup Wizard")
print("=" * 50)

# Determine alaya directory
kb_root = ""
print("\n[1/6] Where is your knowledge base?")
print("  (The directory that will contain wiki/ and alaya/)")
path_input = input("  Path [default: current directory]: ").strip()
if path_input:
    kb_root = os.path.abspath(path_input)
else:
    kb_root = os.getcwd()

alaya_dir = os.path.join(kb_root, "alaya")
os.makedirs(alaya_dir, exist_ok=True)

config = {
    "version": "2.0.0",
    "name": "Alaya",
    "name_zh": "识海",
    "language": "zh",
    "bi_enabled": True,
    "enabled": True,
    "knowledge": {
        "version": "2.0.0",
        "top_k": 3,
        "min_pool": 5,
        "half_life_default": 30,
        "strength_decay": 0.977,
        "sleep_threshold": 0.1,
        "wake_strength": 0.5,
        "sleep_notification_threshold": 30,
        "dirty_categories": [],
        "sleep_counter": 0
    },
    "memory": {
        "version": "1.0.0",
        "hot_limit": 5,
        "cold_limit": 45
    },
    "persona": {
        "version": "1.7.0",
        "max_cards_per_persona": 5,
        "affinity_decay": 0.992
    },
    "last_xunxi_time": ""
}

# Q2: Language
print("\n[2/6] Language preference?")
lang = input("  zh (Chinese) / en (English) [default: zh]: ").strip()
if lang in ("en", "EN"):
    config["language"] = "en"
    print("  -> Language set to English")
else:
    print("  -> Language set to Chinese")

# Q3: Enable BI observer?
print("\n[3/6] Enable BI observer? (recommended)")
print("  BI observes persona behavior and affinity networks. No scoring.")
bi = input("  y/n [default: y]: ").strip()
config["bi_enabled"] = bi.lower() != "n"
print(f"  -> BI observer: {'enabled' if config['bi_enabled'] else 'disabled'}")

# Q4: top_K
print("\n[4/6] Retrieval depth (top_K, default 3)")
print("  How many categories to search per query?")
k = input("  Value [default: 3]: ").strip()
if k.isdigit():
    config["knowledge"]["top_k"] = int(k)
print(f"  -> top_K = {config['knowledge']['top_k']}")

# Q4b: min_pool
print("\n  Minimum candidate pool size (min_pool, default 5)")
print("  If Tier 2 first pass yields fewer than min_pool cards, add more categories.")
mp = input("  Value [default: 5]: ").strip()
if mp.isdigit():
    config["knowledge"]["min_pool"] = int(mp)
print(f"  -> min_pool = {config['knowledge']['min_pool']}")

# Q5: Sleep notification threshold
print("\n[5/6] Sleep notification threshold (default 30)")
print("  How many dormant seeds before notification?")
t = input("  Value [default: 30]: ").strip()
if t.isdigit():
    config["knowledge"]["sleep_notification_threshold"] = int(t)
print(f"  -> Threshold = {config['knowledge']['sleep_notification_threshold']}")

# Q5b: max_cards_per_persona
print("\n  Cards per persona per query (default 5)")
print("  How many cards does each persona select from the candidate pool?")
mc = input("  Value [default: 5]: ").strip()
if mc.isdigit():
    config["persona"]["max_cards_per_persona"] = int(mc)
print(f"  -> max_cards_per_persona = {config['persona']['max_cards_per_persona']}")

# Save config
config_path = os.path.join(alaya_dir, "config.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

# Step 6: Create initial persona(s)
print("\n[6/6] Create personas")
create = input("  Create a persona now? y/n [default: y]: ").strip()
if create.lower() != "n":
    while True:
        create_persona_interview(alaya_dir, default_language=config.get("language", "zh"))
        more = input("\n  Create another? y/n [default: n]: ").strip()
        if more.lower() != "y":
            break

# Auto-copy default personas (always)
package_manas = os.path.join(PKG_ROOT, "manas")
if os.path.exists(package_manas):
    default_files = [f for f in os.listdir(package_manas) if f.endswith(".json") or f.endswith("_profile.md")]
    if default_files:
        dest_manas = os.path.join(alaya_dir, "manas")
        os.makedirs(dest_manas, exist_ok=True)
        copied = 0
        skipped = 0
        for f in default_files:
            src_path = os.path.join(package_manas, f)
            dst_path = os.path.join(dest_manas, f)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                copied += 1
            else:
                skipped += 1
        json_count = sum(1 for f in default_files if f.endswith('.json'))
        profile_count = sum(1 for f in default_files if f.endswith('_profile.md'))
        if copied > 0:
            print(f"\n  {json_count} default personas + {profile_count} profiles installed ({copied} new, {skipped} skipped)")
        else:
            print(f"\n  {json_count} default personas + {profile_count} profiles already present (all {skipped} skipped)")

# Auto-copy example wiki content
package_wiki = os.path.join(PKG_ROOT, "examples", "sample_knowledge_base", "wiki")
if os.path.exists(package_wiki):
    user_wiki = os.path.join(kb_root, "wiki")
    os.makedirs(user_wiki, exist_ok=True)
    wiki_copied = 0
    wiki_skipped = 0
    for root, dirs, files in os.walk(package_wiki):
        rel_dir = os.path.relpath(root, package_wiki)
        if rel_dir == ".":
            dest_dir = user_wiki
        else:
            dest_dir = os.path.join(user_wiki, rel_dir)
        os.makedirs(dest_dir, exist_ok=True)
        for f in files:
            src_path = os.path.join(root, f)
            dst_path = os.path.join(dest_dir, f)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                wiki_copied += 1
            else:
                wiki_skipped += 1
    if wiki_copied > 0:
        print(f"\n  Wiki examples installed: {wiki_copied} cards ({wiki_skipped} skipped)")
    else:
        print(f"\n  Wiki directory already populated ({wiki_skipped} existing cards)")

# Save knowledge base path for cross-platform detection
alaya_path_file = os.path.expanduser("~/.alaya_path")
try:
    with open(alaya_path_file, "w", encoding="utf-8") as f:
        f.write(kb_root.strip())
    print(f"  Path saved: {alaya_path_file}")
except (IOError, OSError) as e:
    print(f"  (Note: could not save path file: {e})")

print("\n" + "=" * 50)
print("  Setup complete!")
print(f"  Config saved to: {config_path}")
print("=" * 50)
print("\nNext steps — try saying:")
print("")
print("  📚 Build your knowledge base")
print('    "帮我构建索引"        → Scan wiki/ and build category index with descriptions')
print('    "导入这篇论文"        → Import paper PDF with summary or full text')
print('    "批量导入 raw/"       → Batch import documents from raw/ folder')
print('    "补充卡片描述"        → Auto-extract missing card descriptions from body')
print('    "更新类别描述"        → LLM regenerates category headers (100-200字)')
print('    "更新索引描述"        → LLM regenerates index entries (150-300字)')
print("")
print("  👤 Create or manage personas")
print('    "创建角色 Feynman"    → Interview-style persona creation (7 steps)')
print('    "蒸馏角色 庄子"       → Distill a persona from conversation')
print('    "克隆角色 小昭"       → Clone an existing persona then customize')
print("")
print("  💬 Chat with personas")
print('    "Feynman, 解释量子纠缠"  → Ask a persona with their unique voice')
print('    "叫Feynman和Buddha讨论XX"  → Multi-persona group discussion')
print('    "各位大佬"            → Trigger a roundtable discussion')
print("")
print("  🔄 Maintenance")
print('    "运行熏习"           → Run knowledge decay and maintenance')
print('    "健康检查"            → Verify system integrity')
print('    "BI观察"              → Cross-persona pattern observation')
print("")
print("  Tip: Say 'alaya init' anytime to re-run this setup wizard.")
print("  (Or 'Enable Alaya' to start a conversation.)")
