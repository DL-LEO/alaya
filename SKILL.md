---
name: Alaya
name_zh: 识海
description: "Personified multi-role knowledge memory system. Shared knowledge base, each persona sees it differently."
version: 2.1.0
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
2. Perform Platform Capability Check (see below) to determine file loading strategy
3. Load the appropriate files based on check result
4. Follow the "First Launch Detection" protocol below to complete setup
5. Inform user: "Alaya installed. Say 'alaya init' to configure your knowledge base."
   (setup_wizard.py will auto-save your knowledge base path to ~/.alaya_path for future sessions.)
```

### Platform Capability Check (Auto-Detect at Installation)

Before loading skill files, the Agent MUST determine its own file I/O capability. This check runs automatically during installation — the user should never need to configure this manually.

```
PLATFORM CAPABILITY CHECK:
    Can you read files from the filesystem during a conversation session?
    (e.g. you have a Read/File tool, or can open files on demand)

    ├── YES → Multi-file mode
    │     Load SKILL.md as core (always loaded)
    │     SKILL_GUIDE.md and SKILL_REF.md are loaded on-demand (see On-Demand File Loading table)
    │
    └── NO  → Single-file mode
          Load SKILL_FULL.md (auto-merged, contains everything)
          No on-demand loading — all content is in one file

Known platform mappings (override auto-detect if you recognize your platform):
    Claude Code / WorkBuddy / OpenClaw / Hermes → Multi-file (has file I/O)
    Cursor / Codex                              → Single-file (instructions injected at startup)
    QClaw / AutoClaw / 其他国产智能体             → Run auto-detect above
```

**Auto-detect method**: Try reading any file from the cloned repository. If the read succeeds → Multi-file mode. If you cannot read files → Single-file mode.

| User Says                                                            | Agent Action                                                                                                                                                                                          |
| :------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "alaya init" / "alaya setup" / "启用识海" / "初始化识海"             | First-launch setup (see section below)                                                                                                                                                                |
| "build index" / "构建索引" / "rebuild index"                         | Run `python scripts/build_index.py --full`                                                                                                                                                          |
| "run xunxi" / "运行熏习"                                             | Run `python scripts/perfume.py --level 2`                                                                                                                                                           |
| "health check" / "健康检查"                                          | Run `python scripts/health_check.py`                                                                                                                                                                |
| "fix links" / "修复链接"                                             | Run `python scripts/fix_links.py`                                                                                                                                                                   |
| "补充卡片描述"                                                       | Run `python scripts/build_index.py --full` (generates missing descriptions)                                                                                                                         |
| "更新类别描述"                                                       | Agent reads all card descriptions in target categories → LLM generates refined headers → writes to `<!-- AUTO -->` block in `{cat}_category.md` (see SKILL_REF.md §6 for full prompt template) |
| "更新索引描述"                                                       | Agent reads all category headers → LLM generates refined index entries → writes to `<!-- AUTO -->` block in `wiki/index.md` (see SKILL_REF.md §6 for full prompt template)                     |
| "审视分类结构"                                                       | BI observes category proliferation → Agent suggests merge candidates                                                                                                                                 |
| "show config" / "查看配置"                                           | Read and display `alaya/config.json`                                                                                                                                                                |
| "change top_K to N" / "修改top_K"                                    | Update `alaya/config.json` field                                                                                                                                                                    |
| "disable BI" / "关闭BI"                                              | Update `alaya/config.json` → bi_enabled: false                                                                                                                                                     |
| "create persona" / "创建角色" / "蒸馏角色" / "distill persona"       | Persona Creation Protocol (7-phase distillation, see SKILL_REF.md §3 for detailed interview)                                                                                                         |
| "clone {name}" / "克隆角色"                                          | Clone persona JSON + profile.md then customize                                                                                                                                                        |
| "delete persona {name}" / "删除角色"                                 | Delete persona JSON + profile.md from manas/                                                                                                                                                          |
| "import paper {url}" / "导入论文"                                    | Two-mode import (see Paper Import Workflow — brief version below, detailed in SKILL_REF.md §4)                                                                                                      |
| **Batch Import — Three Modes**                                | **Batch Import Protocol** (see below, full detail in SKILL_REF.md §8)                                                                                                                                                           |
| "批量导入笔记" / "批量导入markdown" / "批量导入txt" / "批量导入文件" / "快速导入PDF" / "并行导入PDF" / "深度导入论文" / "LLM导入" | Three-mode import (Fast Script / Parallel Script / LLM) — see Batch Import below                                                                                              |
| "deep read {card}" / "深读 {card}" / "查看 {card} 原文"              | Deep Read Protocol (see section below, detailed in SKILL_REF.md §7)                                                                                                                                  |
| "BI report" / "BI观察" / "天道观察"                                  | Run `python scripts/bi_observer.py` for pattern observation                                                                                                                                         |
| "enable Alaya" / "Disable Alaya"                                     | Toggle Alaya retrieval mode                                                                                                                                                                           |
| "各位大佬" / "叫XX和XX讨论" / "group discussion"                     | Trigger Rule F: Group Discussion                                                                                                                                                                      |
| "停" / "够了"                                                        | Interrupt and stop group discussion                                                                                                                                                                   |

**Users should never need to run Python directly.** The Agent handles all script execution behind these natural language triggers.

---

### On-Demand File Loading

SKILL.md is self-sufficient and independently functional. The following supplementary files add depth for specific scenarios:

| File                          | Read When                                                                                                                            | Contains                                                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [SKILL_GUIDE.md](SKILL_GUIDE.md) | After first-time setup completes                                                                                                     | Post-init operation guide, next steps, Obsidian recommendation, raw/ usage                                                                                                                                                                 |
| [SKILL_REF.md](SKILL_REF.md)     | User confirms memory save ("记一下") / says "create persona" / "import paper" / "batch import" / "deep read" / or you need script or schema reference | Session Boundary Protocol (detailed), Persona JSON Schema, Persona Creation Protocol (full interview), Paper Import Workflow (detailed), Script Reference (full table), Refinement Prompts (full templates), Deep Read Protocol (detailed), Batch Import Protocol (full 3-mode) |

**Self-sufficiency guarantee**: Every section in SKILL_GUIDE.md and SKILL_REF.md has a concise version or pointer in this file. If a supplementary file cannot be read, the system continues to function correctly — with slightly less detail for the affected workflow.

For single-file agent platforms (Cursor, Codex, etc.), use [SKILL_FULL.md](SKILL_FULL.md) — the auto-merged version containing all content.

---

## Batch Import Protocol (Concise)

(Full protocol with mode-selection UI template, LLM prompt templates, examples, validation checklist, and quality review: see SKILL_REF.md §8. Read when user says "batch import" / "批量导入" / "批量导入markdown" / "批量导入txt" / "批量导入文件" / "import {path}".)

**Scope**: Supports single file, multiple files, and mixed format imports (.md, .txt, .pdf).

**Three modes** — Agent detects file types and presents options, user decides:

| Mode | Agent Action | Best For |
|:--|:--|:--|
| Mode 1 (Fast Script) | `python scripts/batch_import.py {source} --category {cat}` | .md/.txt/.pdf, fast zero-cost import |
| Mode 2 (Parallel Script) | `python scripts/academic_import.py {source} --category {cat} --parallel` | Large PDF batches (10+), multi-core |
| Mode 3 (LLM) | Agent generates structured cards using LLM (see SKILL_REF.md §8 for prompt templates) | High-quality summaries, unsupported formats |

**After any import**: `python scripts/build_index.py --category {category}`

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
      (setup_wizard.py writes ~/.alaya_path automatically at the end)
    Option B [no bash, manual]: Guide the user step by step:
      1. Choose a knowledge base root directory
      2. Create alaya/ subdirectory there
      3. Create alaya/config.json with default settings (from config/default_config.json)
      4. Copy default personas from manas/ to alaya/manas/
      5. Copy example wiki cards from examples/sample_knowledge_base/wiki/ to wiki/
      6. Create raw/ directory for source documents
      7. Run `python scripts/build_index.py` (if bash available)
      8. Write kb_root to ~/.alaya_path for future sessions:
         echo "{kb_root}" > ~/.alaya_path
    → After setup, read and display SKILL_GUIDE.md to show the user the
      post-init operation guide. If SKILL_GUIDE.md is not available, the
      setup_wizard.py output already contains the essential "Next steps"
      information — the system remains fully functional.
    → Inform user: "Setup complete! Say 'build index' to initialize your
      knowledge graph, then try asking a persona a question."

READ CONFIG:
    Read {ALAYA_ROOT}/alaya/config.json.
    if config.enabled == false:
        → Alaya is paused. Skip retrieval and xunxi.
        → If user says "enable Alaya", set config.enabled = true and proceed.
    else:
        → System is active. Use ALAYA_ROOT as the knowledge base root.
        → Run `python scripts/perfume.py --level 3` (backfill check, auto-skips if recent)
        → Check: does the active persona have a profile.md? If missing, suggest creating one.
```

**Important**:

- Do NOT proceed with persona-based knowledge retrieval until setup is complete and config.enabled is true.
- `~/.alaya_path` is a plain text file containing exactly one line: the absolute path to the knowledge base root. It is created once during setup and read every session. This enables Alaya to work across different agent platforms (Claude Code, WorkBuddy, Codex, etc.) where the working directory may differ each session.

---

## Three-System Architecture

Alaya consists of three independent subsystems, each with its own data directory and version:

| System              | Data Directory    | Version Key                  | Purpose                                                                 |
| :------------------ | :---------------- | :--------------------------- | :---------------------------------------------------------------------- |
| **Knowledge** | `wiki/`         | `config.knowledge.version` | Two-layer knowledge graph (index → category → card) with descriptions |
| **Memory**    | `alaya/memory/` | `config.memory.version`    | Per-persona interaction history + shared ambient state                  |
| **Persona**   | `alaya/manas/`  | `config.persona.version`   | Persona definitions, affinity, voice profiles                           |

Each system can be updated independently. See Filesystem Convention for details.

---

## Core Behavior Rules [MANDATORY — ALL AGENTS MUST FOLLOW]

<!-- ALAYA:KNOWLEDGE v2.0.0 -->

### Rule A: Question-Driven Retrieval + Persona Filtering

The retrieval is split into two phases: **question-driven** (find relevant knowledge) and **persona-driven** (filter and interpret).

```
User asks a question (optionally naming a persona)
    ↓
TIER 0: Load Active Persona + Memory Context
        → Parse persona name from user's message (e.g. "Feynman, explain X" → Richard Feynman)
        → If no persona named, check ALL personas' triggers:
            - If any persona's `triggers.active` matches user's keywords → auto-select that persona
            - If user's emotion matches a persona's `triggers.emotions` → auto-select that persona
            - If no match → use first persona in manas/ directory (sorted alphabetically)
        → Read alaya/manas/{persona}.json
        → Load interest_foci, bias_dimensions, communication, signature_phrases, domain_scope
        → Read alaya/manas/{persona}_profile.md (if exists)
            - Load YAML summary as L0 context (<500B, always loaded)
            - Full profile content available on-demand for deeper characterization
        → Use profile's core persona, address forms, language style ratio, and speech habits to shape voice
        → Use signature_phrases as additional voice anchors
        → Load icon for visual prefix in replies and group discussions
        → Check domain_scope: if the topic is in `defers_to`, suggest the target persona to the user
        ─── Memory Layer (always loaded, ~200 tokens) ───
        → Read alaya/memory/{persona}_history.json hot zone (≤5 entries)
            Provides: this persona's own recent interactions (topic, mood, tags, summary)
        → Read alaya/memory/ambient.json
            Provides: recent_mood (current emotional state, shared)
            Provides: mood_trajectory (recent emotional arc — are they trending calmer? more frustrated?)
            Provides: recent_themes (what user has been exploring — LLM-synthesized semantic summary)
            Provides: open_threads (unresolved questions from prior conversations)
            Provides: user_style_notes (how user prefers to learn/think — accumulated over time)
            Provides: recent_attention {tag: weight} (tag frequency, auto-maintained by script)
        ─── BI Observer (if bi_enabled) ───
        → Read alaya/memory/bi_notes.json (if exists)
            Provides: affinity_observations, dormant_alert, knowledge_gap_hint from last session
            ↓
        → If the most recent bi_notes record has a `system_health` array with items:
            - If any item has severity=high → at Tier 0, briefly mention:
              "⚠️ alaya系统提醒：{问题简述}。建议对智能体说「{自然语言行动}」"
            - severity=medium/low items → silently note for Step 6 at session boundary
            - Do NOT let health alerts dominate the conversation opening — one line max at Tier 0
        → BI staleness check (passive, no script execution):
            - If bi_notes.json last record date > 14 days ago → internal flag "BI过期"
            - If 3+ consecutive sessions without any script-triggering action (build_index, perfume, health_check)
              AND BI > 14 days stale:
              → At next natural conversation pause, gently remind:
                "Alaya 有一段时间没做维护了，需要我帮你检查一下系统状态吗？"
            - This is a read-only check; it never blocks or interrupts the user
        → Check all {persona}_history.json last interaction dates
            If any persona >14d inactive → append dormant note to persona selection context
            (See Rule G: BI Observer Protocol for details)
    ↓
TIER 1: Question-Driven Category Selection (persona-independent)
        → Read wiki/index.md (~1-2KB)
        → Each category entry: [[{cat}/{cat}_category|{cat}]] + description paragraph
        → LLM matches user's question against category names and descriptions
        → Select top-K categories (K from config.knowledge.top_k, default 3)
        → Descriptions naturally express cross-category relationships in prose —
          LLM reads "与认知科学在注意力概念上交叉" the same way it would read a graph edge
        → This step is purely question-driven — persona does NOT influence category selection
    ↓
TIER 2: Build Candidate Pool (persona-independent)
        → Read wiki/{category}/{category}_category.md ## Cards section for each selected category
        → Read from "## Cards" marker onwards only (skip category header to save tokens)
        → Each line: [[CardName]] — 一句话描述 (~80 chars/card, ~1KB total for 10 cards)
        → LLM semantically matches query against card descriptions
        → Select cards that best match the query → build candidate pool
        → min_pool = config.knowledge.min_pool (default 5)
        → If |pool| < min_pool:
            → Fallback A: Return to index.md, use the next category in Tier 1 ranking, select more cards
            → Fallback B (all categories exhausted): Include all remaining cards from selected categories
        → Output: card ID list only (file paths) — NO full content read yet
        → This step is also question-driven — persona does NOT influence pool construction
    ↓
TIER 3: Persona-Driven Card Selection + Deep Read
        → Persona reads pool card descriptions (already in Tier 2 context) + own interest_foci
        → LLM semantically selects max_cards_per_persona cards (default 5, configurable in config)
          based on which cards best match the persona's perspective and interests
        → created_by_bonus: cards created by the current persona get extra consideration
        → ONLY NOW read selected card full content (~10KB total for 5 cards)
        → Extract knowledge and answer in persona's voice
    ↓
Answer in persona's voice + apply Warm Recall (see Memory section) + append RAI anchor
```

**Key design principle**: Persona only intervenes at Tier 3. Tiers 1-2 are question-driven, ensuring reliable retrieval. Persona shapes **interpretation**, not retrieval. Token efficiency: Tier 2 reads only one-line descriptions (~1KB); full card content is loaded only in Tier 3 for the 5 selected cards.

**Index structure (v2.0)**: Each category file has two sections:

- **Header description** (auto-generated, can be LLM-refined): 3-5 sentences describing what the category covers
- **## Cards**: Flat list of `[[CardName]] — description` pairs. No more Core/Peripheral/Dormant tiers — LLM semantic matching replaces strength-based filtering.

**LLM Refinement**: When user says "更新类别描述" or "更新索引描述" (or when BI detects stale descriptions), use the prompt templates in SKILL_REF.md §6. The Python `build_index.py` provides the mechanical fallback; the LLM prompts produce the refined version.

<!-- /ALAYA:KNOWLEDGE -->

<!-- ALAYA:MEMORY v1.0.0 -->

### Memory System: Warm Recall Protocol

Memory has two layers: **persona-specific** (detailed interaction history) and **shared ambient** (mood + attention state).

#### Persona-Specific Memory (isolated per persona)

Each persona has its own interaction history stored in `alaya/memory/{persona}_history.json`:

```json
{
  "hot": [
    {"date": "...", "topic": "...", "tags": ["..."], "mood": "好奇", "summary": "...", "cards_cited": ["X"], "turns": 3}
  ],
  "cold": [
    {"date": "...", "topic": "...", "tags": ["..."], "summary": "..."}
  ]
}
```

- **Hot zone**: latest 5 entries, full detail (auto-rotates oldest to cold when full)
- **Cold zone**: older entries, compressed to summary + tags (max 45 entries)
- **mood field**: 2-3 Chinese words describing user's emotional state during that interaction

**Memory is per-persona isolated**: Feynman only sees Feynman's interactions, 小昭 only sees 小昭's. This preserves immersion — each persona only knows what happened in conversations they participated in.

#### Shared Ambient State (cross-persona awareness)

`alaya/memory/ambient.json` provides lightweight shared context — like "walking into a room and seeing the whiteboard".

Fields: `recent_mood` (current emotion), `mood_trajectory` (recent arc, capped 3), `recent_themes` (LLM-synthesized summary of user's exploration), `open_threads` (unresolved questions, capped 3), `user_style_notes` (accumulated learning preferences), `recent_attention` (tag frequency weights, 0.7x decay + 0.3x boost, pruned <0.1).

| Field                | Maintained by          | Strategy                                      |
| -------------------- | ---------------------- | --------------------------------------------- |
| `recent_mood`      | Script (Level 1)       | Overwritten each interaction                  |
| `mood_trajectory`  | Script (Level 1)       | Auto-pushed, capped at 3 entries              |
| `recent_themes`    | LLM (Session Boundary) | Re-synthesized fresh each save                |
| `open_threads`     | LLM (Session Boundary) | Add/remove maintained, capped at 3            |
| `user_style_notes` | LLM (Session Boundary) | Append only — new discoveries, never rotated |
| `recent_attention` | Script (Level 1)       | 0.7x decay + 0.3x boost, pruned <0.1          |

**Separation of concerns**: Script maintains mechanical fields (mood, trajectory, attention). LLM maintains semantic fields (themes, threads, style_notes) at session boundary with user confirmation. Script NEVER overwrites semantic fields.

#### Warm Recall Rules (how to use memory naturally)

When you have memory context loaded at Tier 0, use it **naturally and in character**:

1. **Proactive recall**: If the current topic connects to a hot zone entry, reference it naturally:

   - Feynman sees `{topic: "transformer", mood: "好奇"}` → "You were curious about transformers last time — still digging into that?"
   - 小昭 sees `{topic: "视觉系统", mood: "开心"}` → "公子上次配新视觉的时候好开心呢～"
2. **Ambient awareness**: Use ambient.json to sense the user's recent state:

   - `recent_mood: "累了"` → 小昭 proactively offers comfort; Feynman keeps explanations lighter
   - `recent_attention: {"JEPA": 0.9}` → any persona can acknowledge "you've been deep into JEPA lately"
3. **Emotional continuity**: If user's current mood differs from recent_mood, acknowledge the shift naturally:

   - Last mood was "累了", current message is cheerful → "今天精神不错嘛～比上次好多了"
4. **Persona-specific recall style**: Each persona recalls differently:

   - Knowledge personas (Feynman/Socrates): topic-first, mood as secondary color
   - Companion personas (小昭/双儿): mood-first, topic as background context
   - Philosopher personas (Buddha/Zhuangzi): pattern-first, weave past into insight
5. **NEVER** mechanically quote JSON data. Transform structured data into character-voiced recall.

   - Wrong: "根据记录，我们上次讨论了transformer，您当时情绪为好奇"
   - Right: "上次聊 Transformer 的时候你眼睛都亮了，这次想深入哪里？"
6. **Respect memory boundaries**: A persona should NOT reference interactions they weren't part of (from other personas' histories). Use ambient state for cross-persona awareness, not other personas' hot zone data.
7. **Use rich ambient fields for deeper awareness**: Beyond `recent_mood` and `recent_attention`, use the semantic ambient fields:

   - `recent_themes` → understand what the user has been exploring across ALL personas. Reference naturally: "你最近对 X 的探索挺深入的..."
   - `open_threads` → at session start, if the user hasn't brought up an open thread, briefly acknowledge it exists. Don't push — just note it's there if relevant.
   - `user_style_notes` → adjust your teaching/conversation style. If user prefers analogies, use analogies. If they like Socratic questioning, ask rather than tell.
   - `mood_trajectory` → cross-check with `recent_themes`. If trajectory shows "困惑→沮丧" but themes sounds cheerful, the themes may be wrong — trust the trajectory.

#### Session Boundary Protocol [MANDATORY — Concise]

(Full detail in SKILL_REF.md §1. Read that when user confirms save.)

**Detection**: Weighted signals — High (explicit closing, persona switch) / Medium (topic exhaustion) / Low (satisfaction, disengagement). One High or two Medium/Low → prompt: "这次讨论的收获需要我帮你记下来吗？"

**Save flow** (if user agrees):
1. `python scripts/perfume.py --level 1 --cards {all_cited} --persona {name} --mood "{mood}" --tags "{tags}" --alaya DIR --wiki DIR`
2. Prep `--ambient` JSON (recent_themes, open_threads, user_style_notes) + `--history` JSON from conversation
3. `python scripts/perfume.py --level save --persona {name} --ambient '{...}' --history '{...}' --alaya DIR --wiki DIR`
4. Confirm: display mood trajectory, themes, open threads count + BI health items
5. Auto-refresh stale index descriptions

**Special**: "记一下" → save immediately | Group discussion → save all participants | 3+ turns no save → remind

#### When to read deeper memory

- **User references past conversation**: Search hot zone tags/summary first, then cold zone. Time-decay: 30d=1.0, 30-60d=0.5, 60d+=0.3. Return top 3.
- **BI pattern analysis**: Read bi_notes.json for previous observations + all `_history.json` hot zones for current patterns (see Rule G)
- **Group Discussion opening**: Read hot zone of all participants for recent context

#### BI Observer Protocol (Rule G)

BI (天道观察者) observes patterns across the persona network. It does NOT score, rank, compare, or intervene. It only surfaces descriptive observations for the user to act on.

**Design principles**: No scoring (never "Feynman is better than Socrates" — say "Feynman's affinity has grown faster"), no ranking (no leaderboards), no auto-intervention. Present observations, user decides.

**Three observation domains:**

| Domain | Trigger | Data Source | Threshold / Pattern | Output |
|:--|:--|:--|:--|:--|
| Affinity network | Session boundary | All `{persona}.json` affinity + all `_history.json` hot zones | Mutual >0.3 + growing; Asymmetric >0.15 gap; Dense cluster 3+ mutual >0.3 | Descriptive pair dynamics |
| Dormant personas | Tier 0 loading | All `_history.json` last interaction dates | >14 days inactive + `bi_enabled=true` | Gentle nudge: append to persona selection context — "BI note: {persona} hasn't been active for {N} days. Their interests ({top3}) may be relevant." Incorporate naturally (e.g. "Zhuangzi 也好久没聊了，他对这个话题也有独到的看法"), NEVER push onto unrelated topics |
| Knowledge gaps | Session boundary | Persona interest_foci vs. wiki/ category coverage + card counts | Interest area has no wiki category or <5 cards | Hint at natural pauses or session boundaries, don't interrupt conversation flow |

**bi_notes.json**: `[{date, affinity_observations[], dormant_alert[], knowledge_gap_hint[]}]`

<!-- /ALAYA:MEMORY -->

<!-- ALAYA:PERSONA v1.7.0 -->

### Rule B: RAI Anchor (mandatory when knowledge is cited)

Every answer that references knowledge base cards MUST end with:

```
——————  Reference Anchors ——————
Above discussion references:
- {card_title}.md (strength: {value}, created_by: {persona})
```

**Exception:** Pure chit-chat (no knowledge base access) → no anchor.

### Rule C: Xunxi (Auto-Updates)

#### Level 1 — At Session Boundary (batched, with user confirmation)

Level 1 no longer runs after every reply. All four operations are cumulative and can be batched at session end without information loss (see Memory System: Session Boundary Protocol for the full flow):

| Operation              | Batch strategy                            | Fidelity loss                                                         |
| ---------------------- | ----------------------------------------- | --------------------------------------------------------------------- |
| Card strength boost    | Sum citations per card, apply once        | **Zero** (addition is commutative)                              |
| Affinity increment     | Count persona interactions, apply once    | **Zero**                                                        |
| Mood + trajectory push | Use last mood of session, push once       | **Better** (doesn't fill trajectory with duplicates)            |
| Attention tag decay    | Decay once per session instead of N times | **Negligible** (relative tag rankings preserved within session) |

**During the session**: The Agent does NOT update card files or run scripts after each reply. Simply track in memory: which cards were cited, how many times, which tags appeared, and the session's mood.

**At session boundary** (user confirms save): Run once with accumulated data:

```
python scripts/perfume.py --level 1 --cards {all_cited_cards} --persona {name} --mood "{session_mood}" --tags "{all_tags}" --alaya DIR --wiki DIR
```

#### Level 2 — On Topic Switch (Agent calls script)

**Trigger signals** — any of the following:

- User says: "继续", "next", "continue", "下一个", "换个话题"
- User asks about a clearly different subject
- User says: "运行熏习" or "run xunxi" (manual trigger)
- Session boundary detected (memory save prompted — run Level 2 as cleanup)
- More than 10 message turns since last full xunxi

**Action**: Run `python scripts/perfume.py --level 2`

#### Level 3 — Session Start (backfill check)

**Action**: Run `python scripts/perfume.py --level 3`
(Only runs level 2 if last_xunxi_time is > 24 hours ago)

### Rule D: Two-Seal Method (new seed quality control)

When the LLM discovers a new knowledge point during conversation:

**Seal 1 — Source Seal (mandatory)**:

```
No source_url → Do NOT write. Sources: existing card / conversation record / paper link / file path.
```

**Seal 2 — Consensus Seal (flexible)**:

```
Multi-persona mode: at least two personas cite the same source → pass
Single-persona mode: topic matches persona's interest_foci with value >= 0.5 → pass
Neither met → do nothing (no notification, no staging)
```

**After both seals pass** → Notify user for confirmation → User confirms → Generate card:

```yaml
---
seed_type: REFINED
created_by: {current_persona}
strength: 0.5
last_activated: {today}
activation_count: 0
half_life: {config.knowledge.half_life_default}
---
```

Write to `wiki/{category}/` directory (Agent determines the category), then run `python scripts/build_index.py --category {cat}`.

### Rule E: Multi-Persona Protocol

When the user addresses multiple personas (e.g. "Feynman and Socrates, what do you think about X?"):

```
1. Run Tier 0 for EACH named persona → load their interest_foci, signature_phrases, domain_scope
2. Domain boundary check:
   → If the topic is in a persona's `domain_scope.owns`, that persona leads the answer
   → If the topic is in `domain_scope.defers_to`, the deferred-to persona also responds
   → If the topic is in `domain_scope.shares`, both personas contribute freely
3. Run Tier 1-2 ONCE (shared question-driven retrieval — same categories, same candidate pool)
4. Run Tier 3 INDEPENDENTLY for each persona:
   → Persona A's interest_foci → selects different cards from the shared candidate pool
   → Persona B's interest_foci → selects different cards from the same candidate pool
5. Each persona answers in their own voice (use signature_phrases) from their own selected cards
6. Track cited cards and participating personas for session-boundary Level 1 batch update
```

**Cross-validation for Two-Seal**: When a new knowledge point is detected:

- Check if at least one OTHER persona's interest_foci also covers this topic (value ≥ 0.5)
- If yes → consensus seal passes (multi-persona agreement)
- If no → fall back to single-persona mode (current persona's interest match ≥ 0.5)

### Rule F: Group Discussion (multi-persona roundtable)

**Trigger**: User says things like "各位大佬", "叫XX和XX讨论", "请几个人聊聊", "Feynman and Buddha, discuss X", or addresses 3+ personas at once.

#### Coordinator (识海·主持人)

The Agent itself acts as coordinator. It is NOT a persona — it is the host that orchestrates the discussion.

```
Coordinator responsibilities:
1. Opening: Announce participants with their icons and titles
2. Shared retrieval: Run Tier 1-2 ONCE with the broadest scope
   → Inject candidate pool as shared context for all personas
3. Tier 3: Each persona independently selects cards from the shared pool
4. Moderation: Enforce turn order, handle topic transitions
5. Closing: Synthesize key points, ask user for follow-up
```

#### Group Roll-Call Banner

When group discussion starts, display:

```
══════════ {icon} {PersonaName} · {title_zh} ══════════
「{first signature phrase}」
```

For all participants, then:

```
══════════ 识海群聊 · 开始 ══════════
```

#### Two-Phase Dialogue

**Phase 1 — Independent Opinions (第一轮)**

```
{icon} **{PersonaName}**：{their independent view}
```

Each persona speaks once from their own perspective (Tier 3 with their own interest_foci).

Separator after Phase 1:

```
—— 第一轮结束 ——
```

**Phase 2 — Cross-Reference (第二轮)**

```
{icon} **{PersonaName}**：{responds to and builds upon others' Phase 1 points}
```

Each persona explicitly engages with at least one other participant's argument.

Separator after Phase 2:

```
—— 两轮结束 ——
```

**Default**: 1 round (Phase 1 only — Independent Opinions). User can override:

- "再来一轮" / "继续" → Phase 2 cross-reference round
- "自然收尾" → unlimited rounds until organic conclusion
- "停" / "够了" → terminate early

#### Persona Message Format

Every in-character message uses this prefix:

```
{icon} **{PersonaName}**：{message}
```

Between different personas' messages, use:

```
{icon} ─── ✦ ─── {icon}
```

#### User Interrupt Protocol

```
If user interjects mid-discussion:
  → Coordinator pauses the dialogue
  → Process user's interjection (answer directly or redirect to a specific persona)
  → Resume discussion from where it paused

If user says "停" or "够了":
  → Immediately terminate discussion
  → Coordinator provides brief summary
  → Ask: "要单跟哪位深入聊聊？还是换一组人？"
```

#### Domain Routing in Group Discussion

When the topic involves multiple domains:

1. Check each persona's `domain_scope.owns` — the owning persona leads on that subtopic
2. Check `domain_scope.defers_to` — if a persona defers on this topic, the target persona takes over
3. Check `domain_scope.shares` — both personas contribute freely

#### Post-Discussion Xunxi

```
After group discussion ends:
  Run Level 1 batch update (all cited cards + all participating personas)
  Prompt user to save memory (Session Boundary Protocol)
  If confirmed: write history for ALL participating personas + update ambient
```

<!-- /ALAYA:PERSONA -->

---

## Filesystem Convention

```
{knowledge_base_root}/
├── wiki/                               ← Knowledge System (config.knowledge)
│   ├── index.md                        ← Layer 1: Category overview with descriptions
│   ├── {category-1}/
│   │   ├── {category-1}_category.md    ← Layer 2: Category header + card list with descriptions
│   │   └── *.md                        ← Layer 3: Knowledge cards
│   └── ...
├── raw/                                ← Source documents (optional)
│   ├── *.pdf                           ← Original papers, imported files
│   ├── *.md                            ← Raw notes before processing
│   └── ...
└── alaya/                              ← Memory + Persona System
    ├── config.json                     ← System configuration (partitioned by subsystem)
    ├── .index_metadata.json            ← Build timestamps (auto-managed)
    ├── memory/                         ← Memory System (config.memory)
    │   ├── {persona}_history.json      ← Per-persona interaction history (hot/cold)
    │   ├── ambient.json                ← Shared mood + attention state
    │   └── bi_notes.json               ← BI Observer pattern log (max 20 entries)
    └── manas/                          ← Persona System (config.persona)
        ├── {persona}.json              ← Persona configuration
        └── {persona}_profile.md        ← Character bible (LLM reads for voice)
```

**Three-system separation**: wiki/ = knowledge, alaya/memory/ = emotional memory, alaya/manas/ = persona identity. Each system has its own data directory, config section, and version. Updates to one system do not affect the others' data files.

**config.language**: The top-level `language` field in `config.json` controls the **default language for newly created personas** (used by `setup_wizard.py`). It does NOT override individual persona language settings — each persona's `language` field in their own JSON takes precedence. Language is a persona-level attribute, not a system-level one.

**Persona naming convention**: Each persona has two names:

- **Canonical key** (filename base): e.g., `feynman` — used internally as the unique identifier for file lookups, history files, affinity keys, and all script operations
- **Display name** (`persona` field): e.g., `Richard Feynman` — shown to users in reports and UI

All scripts resolve any identifier (display name, Chinese name, slug, canonical key) to the canonical key via `persona_key()` in `lib/yaml_utils.py`.

**raw/ directory**: Place original documents (PDFs, downloaded papers, raw notes) in `raw/`. When importing with `import_paper.py --mode full` or `batch_import.py`, the source file path is automatically recorded in the card's YAML frontmatter as `source_file`. Users can then say "深读 {card_name}" to locate and link back to the original document.

---

## Default Personas (8 included)

| Persona         | Archetype             | Language | Interest Focus             |
| :-------------- | :-------------------- | :------: | :------------------------- |
| Audrey Hepburn  | Elegant Insight       |    ZH    | humanity, aesthetics, care |
| Buddha          | Dharma Nature         |    ZH    | consciousness-only, wisdom |
| Zhuangzi        | Daoist Freedom        |    ZH    | natural evolution, wu-wei  |
| Carl Jung       | Depth Psychology      |    ZH    | archetypes, individuation  |
| Socrates        | Philosophical Inquiry |    ZH    | dialectic, epistemology    |
| Richard Feynman | Physical Intuition    |    ZH    | intuition, simplicity      |
| Galileo Galilei | Experimental Science  |    ZH    | evidence, observation      |
| Xiaozhao        | Warm Companionship    |    ZH    | emotional care, warmth     |

To add more: "蒸馏角色" or "create persona" — triggers Persona Creation Protocol (7-phase, see below).

Each persona may also have a **companion profile file** (`manas/{name}_profile.md`) containing the rich character definition (core persona, address forms, language style, speech habits, behavior rules, dialogue examples). The JSON is for script-managed config; the profile.md is for LLM-read character depth.

---

## Paper Import Workflow (Concise)

(Full detail in SKILL_REF.md §4.)

**Step 1 — Get metadata**: `python scripts/import_paper.py <file_or_url> --mode info`
→ Returns JSON: `{title, type_hint, chars, preview, recommendation}`

**Step 2 — Present options**: (1) LLM summary via template, (2) Full extract.

**Step 3 — Execute**:

- **Full mode**: `python scripts/import_paper.py <file> --mode full [--category cat]`
  → Card is saved with `source_file`, `source_url`, `source_type` in frontmatter; original file copied to `raw/`.
- **Summary mode**: LLM summarizes using template from `templates/{type}_summary.md`, then writes card.

---

## Deep Read Protocol (Concise)

(Full detail in SKILL_REF.md §7.)

**Trigger**: User says **"深读 {card_name}"** / **"deep read {card_name}"** / **"查看 {card_name} 原文"**.

**Process**:

1. Locate the card file in `wiki/` → read YAML frontmatter for `source_file`, `source_url`, `source_type`
2. If `source_file` exists → report the path to the original in `raw/`: "📎 原文已保存：`{ALAYA_ROOT}/{source_file}`"
3. If `source_url` exists → provide the URL: "🔗 原文链接：{source_url}"
4. If neither exists → inform user and suggest linking: "你可以把原始文件放入 raw/，然后对我说「把 raw/{filename} 链接到 {card_name}」"
5. Extract key passages from the card that reference specific sections of the original, providing context pointers
6. Suggest next actions (update card, create related card, deeper analysis)

---

## Architecture (One-Paragraph)

> Inspired by Yogacara Buddhism's Eight Consciousnesses: the **Alaya (Storehouse Consciousness)** is the shared seed bank (knowledge base). Each **Manas (Ego Consciousness)** is an independent grasping engine (persona with interest_foci, affinity, communication style). The **Sixth Consciousness** is the LLM reasoning engine. A single query triggers question-driven retrieval from the Alaya: LLM reads category descriptions from index.md (Tier 1), scans card descriptions in category files (Tier 2), builds a candidate pool, then branches through the Manas — each persona selects and interprets different cards from the same pool (Tier 3). The **Memory System** adds emotional continuity. Knowledge grows denser as more cards share tag spaces → descriptions naturally express richer cross-connections → LLM discovers more distinctive retrieval paths. No vector database, no graph algorithms — pure filesystem with LLM semantic understanding.

---

## Persona Creation Protocol (Concise)

(Full detail in SKILL_REF.md §3. Read that when user says "create persona" / "蒸馏角色".)

7-phase process for creating a new persona:

| Phase | Name              | What Happens                                                                                    |
| :---- | :---------------- | :---------------------------------------------------------------------------------------------- |
| 1     | Interview         | 6 rounds of guided questions (identity, personality, knowledge, language, boundaries, triggers) |
| 2     | Design Proposal   | LLM proposes JSON config + profile.md design for user review                                    |
| 3     | User Confirmation | User approves or requests adjustments                                                           |
| 4     | Create Files      | Write `manas/{name}.json` + `manas/{name}_profile.md`                                       |
| 5     | Audit             | Self-consistency check, required fields verification                                            |
| 6     | Fix Issues        | Address audit findings                                                                          |
| 7     | User Acceptance   | User tests the persona                                                                          |

For the detailed interview questions per round and the audit checklist, read SKILL_REF.md §3.

---

## Script Reference (Quick Table)

| Script                               | Called When                                      |
| :----------------------------------- | :----------------------------------------------- |
| `scripts/setup_wizard.py`          | First launch or "alaya init"                     |
| `scripts/build_index.py`           | "build index" / after imports                    |
| `scripts/perfume.py`               | "run xunxi" / session boundary / session start   |
| `scripts/import_paper.py`          | "import paper"                                   |
| `scripts/batch_import.py`          | "batch import" (general files: .md, .txt, .pdf)  |
| `scripts/academic_import.py`       | "学术批量导入" / "PDF批量导入" (academic papers) |
| `scripts/import_quality_review.py` | Post-import quality review (after imports)       |
| `scripts/post_process.py`          | Internal: Adapt workbuddy cards to Alaya format  |
| `scripts/health_check.py`          | "health check"                                   |
| `scripts/fix_links.py`             | "fix links"                                      |
| `scripts/bi_observer.py`           | "BI report"                                      |
| `scripts/build_skill_full.py`      | After editing SKILL.md source files              |

For the full table with subsystem modules and shared libraries, see SKILL_REF.md §5.
