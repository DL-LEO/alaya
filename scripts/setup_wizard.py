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
print("")
print("  Options:")
print("    1. Current directory (default)")
print("    2. Recommended: Use your Obsidian Vault directory")
print("       (Wiki cards will appear in Obsidian's Graph View automatically)")
print("    3. Custom path")
print("")
print("  💡 If you use Obsidian, strongly recommend choosing option 2,")
print("     so all wiki cards are visible in your Obsidian knowledge graph.")
print("")
choice = input("  Choose [1/2/3, default: 1]: ").strip()

if choice == "2":
    vault = input("  Enter your Obsidian Vault path: ").strip()
    if vault:
        kb_root = os.path.abspath(vault)
        print(f"  -> Using Obsidian Vault: {kb_root}")
    else:
        kb_root = os.getcwd()
        print(f"  -> No path entered, using current directory: {kb_root}")
elif choice == "3":
    path_input = input("  Enter custom path: ").strip()
    if path_input:
        kb_root = os.path.abspath(path_input)
    else:
        kb_root = os.getcwd()
        print(f"  -> No path entered, using current directory: {kb_root}")
else:
    kb_root = os.getcwd()
    print(f"  -> Using current directory: {kb_root}")

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
print("\n[2/6] System default language?")
print("  This sets the default language for new personas and system messages.")
print("")
print("  1. Chinese (中文) — default")
print("  2. English")
print("")
lang = input("  Choose [1/2, default: 1]: ").strip()
if lang == "2":
    config["language"] = "en"
    print("  -> Language set to English")
else:
    config["language"] = "zh"
    print("  -> Language set to Chinese (中文)")
print("  -> Note: Each persona can have its own language — this is just the default.")

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

# Create raw/ directory for source documents
raw_dir = os.path.join(kb_root, "raw")
os.makedirs(raw_dir, exist_ok=True)
print(f"\n  ✅ Source documents directory: {raw_dir}/")
print("     Put PDFs, papers, and raw notes here, then say \"批量导入 raw/\"")
print("     to import them into your wiki knowledge base.")

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

        # Override default persona language to match user's choice (first install)
        chosen_lang = config.get("language", "zh")
        for f in os.listdir(dest_manas):
            if not f.endswith(".json") or f.endswith("_history.json"):
                continue
            p = os.path.join(dest_manas, f)
            try:
                with open(p, "r", encoding="utf-8") as fp:
                    pdata = json.load(fp)
                if pdata.get("language") != chosen_lang:
                    pdata["language"] = chosen_lang
                    with open(p, "w", encoding="utf-8") as fp:
                        json.dump(pdata, fp, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, IOError):
                pass

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

# Language-aware guide
if config.get("language") == "en":
    print("""
  Use natural language to talk to your Agent — no commands to memorize.
  Here are a few things you can try right away:

  1. Chat with a persona
     "Feynman, explain quantum entanglement in simple terms"
     "Buddha, how should I understand 'all is mind'?"
     "Ask Feynman and Socrates to discuss the limits of AI"

  2. Import knowledge
     "Import this paper into the knowledge base"  (send a PDF or link)
     "Batch import documents from raw/"

  3. Build the knowledge graph
     "Build index"
     -> This scans your wiki and builds the retrieval index.
     -> Personas can only answer from the knowledge base after indexing.

  -- Advanced (explore later) --
     "Run xunxi"        -> Knowledge decay maintenance
     "Health check"     -> Verify system integrity
     "Create persona"   -> Create a custom persona
     "Alaya help"       -> Full operation guide

  Re-configure anytime: say "alaya init"
""")
else:
    print("""
  用自然语言直接跟你的 Agent 说话就行，不需要记命令。
  以下是你可以立刻尝试的几件事：

  1. 和角色聊天
     "费曼，用大白话解释一下量子纠缠"
     "佛祖，怎么理解'万法唯识'？"
     "叫费曼和苏格拉底讨论 AI 的局限性"

  2. 导入知识
     "帮我把这篇论文导入知识库"  (发一个 PDF 或链接)
     "批量导入 raw/ 文件夹里的文档"

  3. 构建知识图谱
     "帮我构建索引"
     -> 这一步会扫描你的 wiki 知识库，建立检索索引
     -> 索引建好后，角色才能基于知识库回答问题

  -- 进阶操作（之后慢慢探索）--
     "运行熏习"    -> 知识衰减维护
     "健康检查"    -> 检查系统完整性
     "创建角色"    -> 自定义一个新角色
     "识海帮助"    -> 查看完整操作指南

  💡 推荐配合 Obsidian 使用，可以可视化知识图谱。
     下载 obsidian.md -> Open folder as vault -> 选择此目录

  重新配置：说 "alaya init"
""")
