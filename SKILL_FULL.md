---
name: Alaya (Full)
name_zh: 识海（完整版）
description: "Complete merged skill definition for single-file agent platforms. Auto-generated from SKILL.md + SKILL_GUIDE.md + SKILL_REF.md."
version: 2.0.0
author: Liang Shao
license: Apache-2.0
source_files:
  - SKILL.md
  - SKILL_GUIDE.md
  - SKILL_REF.md
generated_by: scripts/build_skill_full.py
---

<!-- ============================================================ -->
<!--  SKILL_FULL.md — auto-generated merged file                  -->
<!--  Do not edit directly. Edit SKILL.md, SKILL_GUIDE.md, or    -->
<!--  SKILL_REF.md and re-run:                                   -->
<!--    python scripts/build_skill_full.py                       -->
<!-- ============================================================ -->

<!-- ###### CORE: SKILL.md ###### -->

---
name: Alaya
name_zh: 识海
description: "Personified multi-role knowledge memory system. Shared knowledge base, each persona sees it differently."
version: 2.0.0
author: Liang Shao
license: Apache-2.0
compatibility:
  - WorkBuddy
  - Claude Code
  - Codex
  - Cursor
  - OpenClaw
  - Hermes
  - Any LLM Agent with filesystem read/write access
skill_files:
  core: SKILL.md
  guide: SKILL_GUIDE.md
  reference: SKILL_REF.md
  merged: SKILL_FULL.md
dependencies:
  - Filesystem read/write permission
  - Optional: Python 3.8+ (for scripts, called automatically by Agent)
  - Optional: Obsidian (recommended for knowledge management)
  - Optional: PyMuPDF (for PDF import, pip install pymupdf)
---

# Alaya · 识海

> **One shared knowledge base. Each persona retrieves it differently.**
>
> The same question asked by an engineer, a philosopher, and a caregiver yields three different perspectives — from the same source.

---

## Natural Language Commands → Agent Actions

Users interact with Alaya through natural language. The Agent maps these to actions automatically.

### Self-Installation

When a user asks to install Alaya (e.g. "install this skill", "帮我安装这个skill", "add alaya to my agent", "装一下识海"), and this SKILL.md is NOT yet in the agent's context:

```
1. git clone https://github.com/DL-LEO/alaya.git {target_dir}
2. Read {target_dir}/SKILL.md into context — this IS the core skill definition
3. If your platform supports multiple instruction files, also read:
   - {target_dir}/SKILL_GUIDE.md — post-init operation guide
   - {target_dir}/SKILL_REF.md — detailed protocols and reference
   Otherwise, read {target_dir}/SKILL_FULL.md — complete merged version
4. Follow the "First Launch Detection" protocol below to complete setup
5. Inform user: "Alaya installed. Say 'alaya init' to configure your knowledge base."
   (setup_wizard.py will auto-save your knowledge base path to ~/.alaya_path for future sessions.)
```

For **Claude Code**: copy or symlink SKILL.md into the project's `.claude/` or add a reference in `CLAUDE.md`.
For **WorkBuddy**: copy SKILL.md to the agent's memory/skills directory.
For **Cursor / Codex**: include SKILL_FULL.md (merged file) in `.cursorrules` or project context config.

| User Says | Agent Action |
|:--|:--|
| "alaya init" / "alaya setup" / "启用识海" / "初始化识海" | First-launch setup (see section below) |
| "build index" / "构建索引" / "rebuild index" | Run `python scripts/build_index.py --full` |
| "run xunxi" / "运行熏习" | Run `python scripts/perfume.py --level 2` |
| "health check" / "健康检查" | Run `python scripts/health_check.py` |
| "fix links" / "修复链接" | Run `python scripts/fix_links.py` |
| "补充卡片描述" | Run `python scripts/build_index.py --full` (generates missing descriptions) |
| "更新类别描述" | Agent reads all card descriptions → LLM generates refined headers → writes to `<!-- AUTO -->` block in `{cat}_category.md` |
| "更新索引描述" | Agent reads all category headers → LLM generates refined index entries → writes to `<!-- AUTO -->` block in `wiki/index.md` |
| "审视分类结构" | BI observes category proliferation → Agent suggests merge candidates |
| "show config" / "查看配置" | Read and display `alaya/config.json` |
| "change top_K to N" / "修改top_K" | Update `alaya/config.json` field |
| "disable BI" / "关闭BI" | Update `alaya/config.json` → bi_enabled: false |
| "create persona" / "创建角色" / "蒸馏角色" / "distill persona" | Persona Creation Protocol (7-phase distillation) |
| "clone {name}" / "克隆角色" | Clone persona JSON + profile.md then customize |
| "delete persona {name}" / "删除角色" | Delete persona JSON + profile.md from manas/ |
| "import paper {url}" / "导入论文" | Two-mode import (info/full, detailed workflow below) |
| "batch import {path}" / "批量导入" / "import {path}" | Run `python scripts/batch_import.py {path}` |
| "deep read {card}" / "深读 {card}" / "查看 {card} 原文" | Deep Read Protocol — locate source_file/source_url in card frontmatter and provide original document access |
| "BI report" / "BI观察" / "天道观察" | Run `python scripts/bi_observer.py` for pattern observation |
| "enable Alaya" / "Disable Alaya" | Toggle Alaya retrieval mode |
| "各位大佬" / "叫XX和XX讨论" / "group discussion" | Trigger Rule F: Group Discussion |
| "停" / "够了" | Interrupt and stop group discussion |

**Users should never need to run Python directly.** The Agent handles all script execution behind these natural language triggers.

---

## First Launch Detection [MANDATORY — CHECK AT SESSION START]

At the start of every session, before doing anything else, locate the Alaya knowledge base:

```
STEP 1 — Try ~/.alaya_path (cross-platform path file):
    If ~/.alaya_path EXISTS:
        Read kb_root from file.
        Set ALAYA_ROOT = kb_root.
        If {ALAYA_ROOT}/alaya/config.json EXISTS:
            → Found via path file. Proceed to READ CONFIG below.

STEP 2 — Fallback: current directory (backward compat):
    If ALAYA_ROOT not set yet and alaya/config.json EXISTS:
        Set ALAYA_ROOT = current directory.
        → Found via fallback. Proceed to READ CONFIG below.

STEP 3 — Not found → First-time setup:
    → This is a first-time setup.
    → Inform the user: "Alaya is not configured yet. Let's set it up."
    Option A [bash available]: Run `python scripts/setup_wizard.py`
    Option B [no bash, manual]: Guide the user step by step
    → After setup, display the operation guide below.
    → Inform user: "Setup complete! Say 'build index' to initialize."

READ CONFIG:
    Read {ALAYA_ROOT}/alaya/config.json.
    if config.enabled == false:
        → Alaya is paused.
    else:
        → System is active. Use ALAYA_ROOT as the knowledge base root.
        → Run `python scripts/perfume.py --level 3` (backfill check)
```

---

## Three-System Architecture

| System | Data Directory | Version Key | Purpose |
|:--|:--|:--|:--|
| **Knowledge** | `wiki/` | `config.knowledge.version` | Two-layer knowledge graph (index → category → card) with descriptions |
| **Memory** | `alaya/memory/` | `config.memory.version` | Per-persona interaction history + shared ambient state |
| **Persona** | `alaya/manas/` | `config.persona.version` | Persona definitions, affinity, voice profiles |

---

## Core Behavior Rules [MANDATORY]

### Rule A: Question-Driven Retrieval + Persona Filtering

```
User asks a question (optionally naming a persona)
    ↓
TIER 0: Load Active Persona + Memory Context
        → Parse persona name, load their interest_foci, bias_dimensions, etc.
        → Read memory hot zone + ambient state + BI notes
    ↓
TIER 1: Question-Driven Category Selection (persona-independent)
        → Read wiki/index.md → LLM matches question against category descriptions
        → Select top-K categories
    ↓
TIER 2: Build Candidate Pool (persona-independent)
        → Read ## Cards section of selected category files
        → LLM semantically matches card descriptions → candidate pool
        → min_pool = 5, fallback if insufficient
    ↓
TIER 3: Persona-Driven Card Selection
        → Persona filters candidate pool by interest_foci
        → Read selected card full content
        → Answer in persona's voice
    ↓
Answer + Warm Recall + RAI Anchor
```

### Rule B: RAI Anchor
Every answer referencing knowledge base cards MUST end with:
```
—————— Reference Anchors ——————
Above discussion references:
- {card_title}.md (strength: {value}, created_by: {persona})
```

### Rule C: Xunxi (Auto-Updates)
- Level 1: At session boundary — batched mechanical updates
- Level 2: On topic switch — strength/affinity decay
- Level 3: Session start — backfill check (if >24h since last)

### Rule D: Two-Seal Method
Source seal (source_url required) + Consensus seal (multi-persona agreement or interest match ≥0.5)

### Rule E: Multi-Persona Protocol
Multiple personas: shared Tiers 1-2 retrieval, independent Tier 3 selection

### Rule F: Group Discussion
Coordinator-hosted roundtable: Phase 1 (independent opinions) + Phase 2 (cross-reference)

### Rule G: BI Observer Protocol
Three domains: affinity network, dormant personas, knowledge gaps. No scoring/ranking.

---

## Filesystem Convention

```
{knowledge_base_root}/
├── wiki/                     ← Knowledge cards (index → category → card)
│   ├── index.md
│   └── {category-1}/
│       ├── {category-1}_category.md
│       └── *.md
├── raw/                      ← Source documents (PDF, original papers, notes)
└── alaya/                    ← System config + memory + personas
    ├── config.json
    ├── memory/               ← Persona histories + ambient state + BI notes
    └── manas/                ← Persona JSON + profile.md files
```

---

## Default Personas (8 included)

Audrey Hepburn, Buddha, Zhuangzi, Carl Jung, Socrates, Richard Feynman, Galileo Galilei, Xiaozhao

---

## Paper Import Workflow

**Step 1**: `python scripts/import_paper.py <file_or_url> --mode info` → JSON metadata
**Step 2**: Present options: summary (LLM template) or full extract
**Step 3**: Execute (--mode full saves card with source_file/source_url/source_type)

---

## Deep Read Protocol

When user says "深读 {card_name}":
1. Read card frontmatter for `source_file` / `source_url` / `source_type`
2. Report file path (raw/), URL, or suggest linking
3. Extract key passages with original-context pointers
4. Suggest next actions

---

## Persona Creation Protocol (7-Phase)

1. Interview → 2. Design Proposal → 3. Confirmation → 4. Create Files → 5. Audit → 6. Fix → 7. Accept

---

## Script Reference

| Script | Called When |
|:--|:--|
| `scripts/setup_wizard.py` | "alaya init" |
| `scripts/build_index.py` | "build index" |
| `scripts/perfume.py` | "run xunxi" / session boundary |
| `scripts/import_paper.py` | "import paper" |
| `scripts/batch_import.py` | "batch import" |
| `scripts/health_check.py` | "health check" |
| `scripts/fix_links.py` | "fix links" |
| `scripts/bi_observer.py` | "BI report" |
| `scripts/build_skill_full.py` | After editing SKILL files |

<!-- ###### GUIDE: SKILL_GUIDE.md ###### -->

# Alaya · 识海 — 操作指南

> 初始化完成！以下是你可以用识海做的所有事情。

---

## 📚 构建与充实知识库

```
"帮我构建索引"         → 扫描 wiki/ 并构建三层知识图谱
"导入这篇论文"         → 导入论文 PDF 或 arXiv 链接
"批量导入 raw/"        → 从 raw/ 文件夹批量导入文档
"补充卡片描述"         → 自动从正文提取缺失的卡片描述
"更新类别描述"         → LLM 重新生成类别头部描述
"更新索引描述"         → LLM 重新生成 index.md 各分类的入口描述
"审视分类结构"         → BI 检查分类是否需要合并
```

> **💡 小贴士：** 把下载的论文、PDF 或任何原始文档放到 `raw/` 目录下，
> 然后让 Agent 批量导入或逐篇导入。导入后 Agent 会自动建立指向原文的链接，
> 方便你后续「深读」时快速回查原文。

---

## 👤 角色管理

```
"创建角色"             → 7 阶段访谈式角色创建
"蒸馏角色 {名字}"      → 从对话中蒸馏新角色
"克隆角色 {名字}"      → 克隆现有角色再微调
"删除角色 {名字}"      → 删除角色及其配置
```

默认已安装 8 个角色。你可以随时创建自己的角色。

---

## 💬 对话示例

```
"Feynman, 解释量子纠缠"         → ⚛ 费曼用物理直觉回答
"Socrates, 你怎么看 attention？" → 🏛️ 苏格拉底用哲学追问
"叫Feynman和Buddha讨论意识"      → ⚛☸ 多角色圆桌讨论
```

---

## 📂 准备原始文档

```
{your_kb_root}/
├── raw/                      ← 原始文档（你放入，Agent 导入）
├── wiki/                     ← 知识卡片（Agent 自动管理）
└── alaya/                    ← 系统配置（Agent 自动管理）
```

放入 `raw/` 后说 **"批量导入 raw/"** 自动导入到 wiki。

---

## 🔗 配合 Obsidian 可视化（强烈推荐）

1. 下载 [Obsidian](https://obsidian.md/download)（免费）
2. **"Open folder as vault"** → 选择知识库根目录（包含 `wiki/` 的目录）
3. 点击 **Graph View** → 所有卡片以节点图呈现

---

## 🩺 维护命令

```
"运行熏习"       → 知识衰减和强度更新
"健康检查"        → 系统完整性检查
"修复链接"        → 修复 wiki 链接大小写
"BI观察"          → 跨角色模式观察
```

---

## ✅ 首次配置检查清单

- [ ] `alaya/config.json` 存在
- [ ] `alaya/manas/` 下有至少一个角色
- [ ] `wiki/` 下有类别子文件夹和知识卡片
- [ ] `wiki/index.md` 已生成
- [ ] `raw/` 文件夹已创建
- [ ] 运行了 **"构建索引"**

---

## ❓ 需要帮助？

随时说 "识海帮助"、"健康检查"、"查看配置"、"alaya init"

<!-- ###### REFERENCE: SKILL_REF.md ###### -->

# Alaya · 识海 — Reference

> **On-demand reference content.** Read when triggering Session Boundary, creating personas, importing papers, or needing schema details.

---

## Session Boundary Protocol (Detailed)

### Trigger Signals

| Signal | Weight | Examples |
|---|---|---|
| Explicit closing | **High** | "今天就到这里", "bye" |
| Persona switch | **High** | "我去问问Feynman" |
| Topic exhaustion | Medium | Core question answered, no follow-up |
| Satisfaction | Low | "明白了", "原来如此" |
| Disengaged | Low | "嗯", "好", "ok" (2 consecutive) |

One High or two Medium/Low → prompt:
> 这次讨论的收获需要我帮你记下来吗？

### Save Protocol

**Step 1 — Mechanical**: `python scripts/perfume.py --level 1 --cards {cited} --persona {name} --mood "{mood}" --tags "{tags}" --alaya DIR --wiki DIR`

**Step 2 — Semantic prep**: Prepare `--ambient` JSON and `--history` JSON

**Step 3-5 — Atomic save**:
```
python scripts/perfume.py --level save --persona {name} \
  --ambient '{"recent_themes":"...","open_threads":[...],"user_style_notes":"..."}' \
  --history '{"topic":"...","tags":[...],"mood":"...","summary":"...","key_insights":[...],"cards_cited":[...],"turns":N}' \
  --alaya DIR --wiki DIR
```

**Step 6 — Confirm**: Display saved summary + BI health items

### Special Cases
- "记一下" mid-conversation → save immediately
- Group discussion → save ALL participants
- Save fails → "保存失败，你可以稍后让我重试"
- 3+ interactions no save → proactive reminder

---

## Persona JSON Schema

```json
{
  "persona": "PersonaName",
  "persona_zh": "角色中文名",
  "title": "One-line archetype",
  "ego_vector": {
    "interest_foci": {"area": {"value": 0.9, "floor": 0.15}},
    "bias_dimensions": {"dim": {"value": 0.8, "floor": 0.1}},
    "communication": {"style": {"value": 0.8, "floor": 0.1}}
  },
  "affinity": {},
  "interaction_history": [],
  "confidence": 0.75,
  "mode_config": {"behavior": "auto", "auto_trigger_threshold": 0.7},
  "signature_phrases": ["phrase1", "phrase2"],
  "icon": "⚛",
  "domain_scope": {"owns": [], "shares": [], "defers_to": {}},
  "triggers": {"active": [], "passive": [], "emotions": []}
}
```

### Source File Fields (for Deep Read)
- `source_file`: relative path to original in raw/ (e.g. "raw/my-paper.pdf")
- `source_url`: URL of source
- `source_type`: "pdf" / "url" / "local" / "md" / "txt"

---

## Persona Creation Protocol (Full Interview)

**Phase 1 — Interview** (6 rounds):
- R1 Identity: Name, address forms
- R2 Personality: 3-5 core traits, emotional tone
- R3 Knowledge: Domains they know / don't know
- R4 Language: Catchphrases, speech habits, style ratio
- R5 Boundaries: Topics to avoid, behaviors to prevent
- R6 Triggers: Keywords, emotions, contexts for activation

**Phase 2 — Design Proposal**: JSON config + Profile.md design
**Phase 3 — Confirmation**: User approves or adjusts
**Phase 4 — Create Files**: Write JSON + profile.md
**Phase 5 — Audit**: Self-consistency + required fields check
**Phase 6 — Fix**: Address findings
**Phase 7 — Accept**: User tests the persona

---

## Deep Read Protocol (Detailed)

When user says "深读 {card_name}":
1. Read card frontmatter for source_file/source_url/source_type
2. source_file exists → "📎 原文已保存：raw/{filename}" + suggest Obsidian
3. source_url exists → "🔗 原文链接：{url}"
4. Neither → suggest linking: "把 raw/{filename} 链接到 {card_name}"
5. Extract key passages with original-context pointers
6. Suggest next actions

---

## Script Reference (Full)

| Script | Purpose | Trigger |
|:--|:--|:--|
| `setup_wizard.py` | Interview config + persona creation | "alaya init" |
| `build_index.py` | Two-layer index + metadata | "build index" |
| `import_paper.py` | Two-mode paper import | "import paper" |
| `batch_import.py` | Batch import with checkpoint | "batch import" |
| `perfume.py` | Three-level xunxi orchestrator | "run xunxi" |
| `perfume_knowledge.py` | Card strength/decay/sleep | via perfume.py |
| `perfume_memory.py` | History write/ambient state | via perfume.py |
| `perfume_persona.py` | Affinity increment/decay | via perfume.py |
| `health_check.py` | Network integrity check | "health check" |
| `fix_links.py` | Wiki-link case fixing | "fix links" |
| `bi_observer.py` | Cross-persona patterns | "BI report" |
| `build_skill_full.py` | Merge SKILL files | After editing sources |
| `lib/yaml_utils.py` | YAML parsing/metadata | (shared library) |
| `lib/format_converter.py` | Format detection/extraction | (shared library) |
