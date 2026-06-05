---
name: Alaya Reference
description: "Deep reference for Alaya · 识海 — detailed protocols, schemas, workflows, scripts. Read on demand."
version: 2.1.0
trigger: "Read when user triggers Session Boundary (save), create persona, import paper, or needs script/schema reference."
---

# Alaya · 识海 — Reference

> **On-demand reference file.** SKILL.md contains the concise versions of everything below.
> Read this file only when the trigger condition is met for each section.

---

## Table of Contents

1. [Session Boundary Protocol (Detailed)](#1-session-boundary-protocol-detailed)
2. [Persona JSON Schema (Complete)](#2-persona-json-schema-complete)
3. [Persona Creation Protocol (Full Interview)](#3-persona-creation-protocol-full-interview)
4. [Paper Import Workflow (Detailed)](#4-paper-import-workflow-detailed)
5. [Script Reference (Full Table)](#5-script-reference-full-table)
6. [Category/Index Refinement Prompts (Full Templates)](#6-categoryindex-refinement-prompts-full-templates)
7. [Deep Read Protocol (Detailed)](#7-deep-read-protocol-detailed)
8. [Batch Import Protocol (Full)](#8-batch-import-protocol-full)

---

## 1. Session Boundary Protocol (Detailed)

### Trigger Signals — Weighted Detection

| Signal | Weight | Examples |
|---|---|---|
| Explicit closing | **High** | "今天就到这里", "先这样", "谢谢很有帮助", "bye", "goodbye" |
| Persona switch intent | **High** | "我去问问Feynman", "换个人聊聊", "让XX也来说说" |
| Topic exhaustion | Medium | Core question answered, user expresses understanding, no follow-up questions |
| Satisfaction expression | Low | "明白了", "原来如此", "清楚了", "有意思" |
| Disengaged replies | Low | Two consecutive very short replies ("嗯", "好", "ok") |

### Save Prompt

When boundary is detected, prompt the user lightly (one line, non-intrusive):

> 这次讨论的收获需要我帮你记下来吗？

Three response paths:
- **User agrees** ("好", "记一下吧", "yes", "save it") → Execute Save Protocol below
- **User declines** ("不用", "算了", "no") → Skip. Previous confirmed state remains unchanged.
- **User ignores / closes window** → Skip. Last confirmed state persists. At most one session's nuance is lost.

### Save Protocol — Step by Step

**Step 1 — Run mechanical updates (script):**

Run Level 1 ONCE with all data accumulated during this session:
```
python scripts/perfume.py --level 1 --cards {all_cited_cards} --persona {name} --mood "{session_mood}" --tags "{all_tags}" --alaya DIR --wiki DIR
```

This handles: card strength boost (summed per card), affinity increment, mood overwrite + trajectory push, attention tag decay/boost.

**Step 2 — Prepare semantic fields (from conversation observation):**

Based on what you observed during the conversation, prepare the semantic ambient fields and history entry for the combined save command (see Step 3-5).

**Step 3-5 — Atomic save (combined):**

Run ONE script call that handles all three remaining steps atomically:
```
python scripts/perfume.py --level save --persona {name} \
  --ambient '{"recent_themes":"...","open_threads":[...],"user_style_notes":"..."}' \
  --history '{"topic":"...","tags":[...],"mood":"...","summary":"...","key_insights":[...],"cards_cited":[...],"turns":N}' \
  --alaya DIR --wiki DIR
```

The `--ambient` JSON accepts the same three semantic fields:

| Field | Strategy |
|---|---|
| `recent_themes` | **Re-synthesize**: Based on this conversation + hot history, write 2-3 fresh Chinese sentences capturing what the user has been exploring and how. Do NOT reuse old value — always rewrite from scratch. |
| `open_threads` | **Maintain**: Add new unresolved questions (with `{"question": "...", "since": "YYYY-MM-DD"}`). Remove questions that were answered satisfactorily or haven't been mentioned for 5+ interactions. Cap at 3. |
| `user_style_notes` | **Append if new**: Only write if you discovered something new about how the user thinks, learns, or prefers to interact. Do not rotate or overwrite — this accumulates. |

Note: `recent_mood`, `mood_trajectory`, and `recent_attention` were already handled by the script in Step 1. Don't include them in `--ambient`.

The `--history` JSON follows this structure:
```json
{
  "date": "{today}",
  "topic": "{one-line conversation topic}",
  "tags": ["{key_topic_1}", "{key_topic_2}"],
  "mood": "{2-3 Chinese words}",
  "summary": "{2-3 sentence summary of what was discussed and resolved}",
  "key_insights": ["{specific insight or decision from this conversation}"],
  "cards_cited": ["{card_name_1}", "{card_name_2}"],
  "turns": {approx_turn_count}
}
```

If hot zone exceeds 5 entries, the script rotates oldest to cold zone (compressed: date, topic, tags, summary). Cold zone capped at 45.

The script automatically runs the BI Observer pass (dormant personas, knowledge gaps, affinity asymmetry) and saves findings to `bi_notes.json` and a protocol checklist to `_protocol_checklist.json`.

**Step 6 — Confirm to user:**

After Step 3-5 completes, display:

```
记忆已保存 ✓
- 情绪轨迹：{mood} → {mood} → {mood}
- 关注主题：{one-line summary of recent_themes}
- 未解问题：{count} 个
```

If the saved `bi_notes.json` record contains `system_health` items, display them after the confirmation block:

```
{severity_marker} alaya系统提醒您：
  • {问题简述}（{依据数据}）
    → 建议您对智能体说「{自然语言行动}」
```

**Severity marker rules:**
- If any item has `severity=high`: use `⚠️`
- Otherwise: use `📋`

**Example output:**
```
⚠️ alaya系统提醒您：
  • 检测到 3 个脏类别（量子物理、机器学习、哲学）
    → 建议您对智能体说「重建索引」，智能体会自动全量构建知识图谱，修复所有脏类别和连边关系
  • 知识图谱索引 index.md 不存在，尚未初始化
    → 建议您对智能体说「构建索引」，智能体会自动初始化知识图谱的三层网络结构
📋 alaya系统提醒您：
  • 2 个角色超过 14 天未互动：庄子(28d)、小昭(16d)
    → 建议您和庄子、小昭聊聊最近的话题，重新激活他们的视角和知识储备
```

**Important rules:**
- If `system_health` is empty (all clear), show nothing extra after the confirmation block.
- Each item MUST include: what problem is, what data supports it, and a natural-language action the user can say to the Agent.
- Do NOT show raw command strings (e.g. "python scripts/build_index.py") — always phrase as something the user says to the Agent.

### Special Cases

- **User says "记一下" mid-conversation**: Execute Save Protocol immediately, then continue. Don't wait for boundary detection.
- **Group discussion**: Save history for ALL participating personas. Run `--level save` once per persona: first call includes both `--ambient` and `--history`, subsequent calls only need `--history` (omit `--ambient` to avoid overwriting).
- **Save fails** (file write error): Report "保存失败，你可以稍后让我重试" and keep the conversation context for manual recovery.
- **3+ interactions without save**: If hot zone's latest entry is >3 interactions old (check by counting turns since last save mention), proactively remind: "需要我帮你记一下最近的讨论吗？"

**Step 7 (隐式) — 索引刷新检查**: After save confirmation and BI notes display, check `.index_metadata.json`:
- If `stale_descriptions` is non-empty → Agent proactively runs "更新类别描述" on stale categories
- If `index_desync` detected by BI → Agent proactively runs "更新索引描述"

### When to Read Deeper Memory

- **User references past conversation**: "上次我们聊的...", "last time we discussed..."
  → Search hot zone tags/summary first, then cold zone
  → Time-decay weighting: 30d=1.0, 30-60d=0.5, 60d+=0.3
  → Return top 3 matches
- **BI pattern analysis**: Read bi_notes.json for previous observations + all `_history.json` hot zones for current patterns (see Rule G)
- **Group Discussion opening**: Read hot zone of all participants for recent context

---

## 2. Persona JSON Schema (Complete)

```json
{
  "persona": "PersonaName",
  "persona_zh": "角色中文名 (optional)",
  "title": "One-line archetype (English)",
  "title_zh": "角色定位（中文，可选）",
  "ego_vector": {
    "interest_foci": { "area": {"value": 0.9, "floor": 0.15} },
    "bias_dimensions": { "dim": {"value": 0.8, "floor": 0.1} },
    "communication": { "style": {"value": 0.8, "floor": 0.1} }
  },
  "affinity": {},
  "interaction_history": [],
  "confidence": 0.75,
  "mode_config": { "behavior": "auto", "auto_trigger_threshold": 0.7 },
  "signature_phrases": ["phrase1", "phrase2"],
  "icon": "⚛",
  "domain_scope": {
    "owns": ["area1"],
    "shares": ["area2"],
    "defers_to": { "area3": "OtherPersonaName" }
  },
  "triggers": {
    "active": ["keyword1", "keyword2"],
    "passive": ["context1"],
    "emotions": ["emotion1"]
  }
}
```

### Fields Explained

| Field | Purpose | Example |
|:--|:--|:--|
| `icon` | Single emoji that represents this persona in group discussions and message prefixes. | Feynman: `"⚛"`, Buddha: `"☸"`, Xiaozhao: `"🌸"` |
| `signature_phrases` | Characteristic expressions that shape the persona's voice. The Agent naturally weaves these into replies. | Feynman: `"What's the evidence?"`, Buddha: `"万法唯识。"` |
| `domain_scope.owns` | Topics this persona exclusively handles. Other personas defer on these. | Buddha owns `consciousness-only`, `yogacara` |
| `domain_scope.shares` | Topics where multiple personas can contribute. | Feynman and Galileo both share `scientific_method` |
| `domain_scope.defers_to` | Topics this persona voluntarily hands off to another persona. `{"area": "PersonaName"}` | Galileo defers `quantum_mechanics` to Feynman |
| `triggers.active` | Keywords that make this persona proactively speak up (even if not directly addressed). | Feynman triggers on `physics`, `quantum` |
| `triggers.passive` | Context clues that make this persona available but not proactive. | Buddha passive on `meaning of life` |
| `triggers.emotions` | User emotional states that activate this persona. | Xiaozhao triggers on `loneliness`, `sadness` |

### Source File Fields (for Deep Read)

When importing papers or local documents, cards should include these additional fields:

| Field | Purpose | Example |
|:--|:--|:--|
| `source_file` | Relative path to the original document in raw/ | `"raw/my-paper.pdf"` |
| `source_url` | URL of the source (arXiv, website, etc.) | `"https://arxiv.org/abs/2201.12345"` |
| `source_type` | Format of the original source | `"pdf"`, `"url"`, `"local"`, `"md"`, `"txt"` |

---

## 3. Persona Creation Protocol (Full Interview)

Use this 7-phase protocol when user says "创建角色", "蒸馏角色", "distill persona", "make a persona".

### Phase 1: Interview (6 rounds, 1-2 questions per round)

**Round 1 — Identity:**
- What is this persona's name?
- How should they address the user? How do they refer to themselves?

**Round 2 — Personality:**
- What are 3-5 core traits? (Describe each briefly)
- What is their default emotional tone?

**Round 3 — Knowledge:**
- What domains do they know well?
- What do they NOT know? (Knowledge boundary — critical for honesty)

**Round 4 — Language:**
- What are their catchphrases / signature expressions?
- Speech habits: fast/slow? Formal/casual? Any dialect or linguistic quirks?
- Language style ratio: (e.g., playful 40% + analytical 35% + provocative 25%)

**Round 5 — Boundaries:**
- What topics should they avoid?
- What behaviors should be prevented?

**Round 6 — Triggers & Scenarios:**
- When should this persona activate? (Keywords, emotions, contexts)
- Any specific scenarios you envision?

**After Round 6:** Ask "Anything else I should know?" — give space for additions.

### Phase 2: Design Proposal

Output a concise design (fits one screen):

```
Design: {persona_name}

JSON Config:
  - interest_foci: {top 3-5 from Round 3}
  - triggers: {from Round 6}
  - domain_scope: owns/shares/defers_to

Profile.md:
  - Core persona: {from Round 1-2}
  - Language style: {from Round 4}
  - Behavior rules: {from Round 5}
  - Example dialogues: 3-5 scenarios

OK to proceed? Or adjust.
```

### Phase 3: User Confirmation

- User confirms → Phase 4
- User adjusts → modify proposal → re-confirm
- **Never start writing files without user confirmation**

### Phase 4: Create Files

Create TWO files:

1. `manas/{name}.json` — structural config (use `templates/persona_template.json` as base)
2. `manas/{name}_profile.md` — character bible (use `templates/persona_profile_template.md` as structure, fill with interview results)

Follow the exact profile template chapters: 核心人设 → 语言风格基调 → 使用场景 → 行为要求 → 典型对话示例.

### Phase 5: Audit

Check:
- [ ] Persona traits and example dialogues are self-consistent
- [ ] JSON has all required fields (ego_vector, triggers, domain_scope, icon, signature_phrases)
- [ ] profile.md has all required sections (核心人设, 知识边界, 语言风格基调, 使用场景, 行为要求, 典型对话示例)
- [ ] Knowledge boundary is clearly defined
- [ ] No contradictory instructions (e.g., "doesn't understand tech" but example shows deep tech discussion)

### Phase 6: Fix Issues

Fix any audit findings. Ask user about optional improvements.

### Phase 7: User Acceptance

Ask: "Want to test? Say the persona's name to try them out."

---

## 4. Paper Import Workflow (Detailed)

### Step 1 — Get metadata

```
python scripts/import_paper.py <file_or_url> --mode info
```

Returns JSON: `{title, type_hint, chars, preview, recommendation}`

### Step 2 — Present options to user

Present the detected info and ask:
> (1) **总结摘要** — LLM summarizes into template structure (see `templates/`). Ask user for max chars (default 2000).
> (2) **全文提取** — Save full text as wiki card, no truncation.

### Step 3 — Execute

**Option A — Full mode** (user wants all content):
```
python scripts/import_paper.py <file> --mode full [--category cat]
```
Script extracts and saves full text as a wiki card with proper Alaya frontmatter.
The script automatically records `source_file`, `source_url`, and `source_type` in frontmatter.

**Option B — Summary mode** (user wants summarized content):
1. Read the appropriate template: `templates/paper_summary.md`, `templates/news_summary.md`, or `templates/other_summary.md`
2. Summarize extracted text following the template structure, within user's max-char limit
3. Write the filled card to `wiki/{category}/{slug}.md`
4. Run: `python scripts/build_index.py --category {cat}`

Templates are editable Markdown files. Users can customize section headers or add new sections by editing `templates/{type}_summary.md`.

### Source File Linking

When importing local files, the card frontmatter will automatically include:

```yaml
source_file: "raw/original-filename.pdf"
source_type: "pdf"
```

The original file is copied to `{kb_root}/raw/` for persistent storage and future deep-read access.

---

## 5. Script Reference (Full Table)

### Core Scripts

| Script | Purpose | Called By Agent When |
|:--|:--|:--|
| `scripts/setup_wizard.py` | Interview-style config + persona creation | First launch detection |
| `scripts/build_index.py` | Build two-layer index + inject missing metadata + extract descriptions | "build index" / after import |
| `scripts/import_paper.py` | Two-mode import (info/full), supports paper/news/other | "import paper {url}" |
| `scripts/batch_import.py` | Batch import files (MD/PDF/TXT) with checkpoint/resume | "batch import {path}" / "import {path}" |
| `scripts/perfume.py` | Three-level xunxi orchestrator | Topic switch / session start / manual |

### Subsystem Modules (called by perfume.py, not directly)

| Module | System | Purpose |
|:--|:--|:--|
| `scripts/perfume_knowledge.py` | Knowledge | Card strength boost, decay, sleep, dirty tracking |
| `scripts/perfume_memory.py` | Memory | History write (hot/cold), ambient state, migration |
| `scripts/perfume_persona.py` | Persona | Affinity increment and decay |

### Maintenance Scripts

| Script | Purpose | Called By Agent When |
|:--|:--|:--|
| `scripts/health_check.py` | Check three-layer network integrity | "health check" |
| `scripts/fix_links.py` | Fix broken wiki-links (case mismatch) | "fix links" |
| `scripts/bi_observer.py` | Cross-persona pattern observation (affinity network, dormant detection, knowledge gaps) | "BI report" / "BI观察" / "天道观察" |

### Build & Validation Scripts

| Script | Purpose | Called By Agent When |
|:--|:--|:--|
| `scripts/build_skill_full.py` | Merge SKILL.md + SKILL_GUIDE.md + SKILL_REF.md into SKILL_FULL.md | After updating SKILL files (auto-detected) |

### Shared Libraries

| Module | Purpose |
|:--|:--|
| `scripts/lib/yaml_utils.py` | YAML frontmatter parsing, metadata injection, card discovery |
| `scripts/lib/format_converter.py` | Zero-dependency format conversion (MD/TXT native, PDF optional) |

---

## 6. Category/Index Refinement Prompts (Full Templates)

### Category Header Refinement Prompt

```
Input: Category slug + all card descriptions from ## Cards section of {cat}_category.md

Generate a Chinese category overview. Constraints:
- 100-200 characters
- 3-segment structure:
  ① 领域定位（1句）：本类别在知识体系中的位置与学术/实践语境
  ② 核心议题（2-3句）：从卡片描述中识别的主要主题线，标注卡片间的互补/递进/对立关系
  ③ 阅读指引（1句）：建议的阅读切入点或学习路径
- Use the card descriptions as raw material — distill, don't copy-paste
- Write in prose, not bullet points
- Cross-reference other categories when natural ("与XX类别在YY概念上交叉")

Output: Write the generated text to the <!-- AUTO --> block of the category file.
Preserve any existing <!-- MANUAL --> blocks.
Do NOT modify the ## Cards section.
```

### Index Entry Refinement Prompt

```
Input: wiki/index.md current content + all category headers (from {cat}_category.md <!-- AUTO --> blocks)

For each category in the index, generate a refined entry. Constraints:
- 150-300 characters per category
- Content requirements:
  ① 类别概述（从 category header 蒸馏，非照抄，换一个角度表述）
  ② 与其他类别的交叉点（如"与XX类别在YY概念上交叉"——仅当确有关联时写）
  ③ 适用场景提示（什么类型的问题应检索此类别）
- Each entry starts with the wiki-link line, followed by the description paragraph
- Write in prose, not bullet points
- If a category has only 1-2 cards, keep the entry concise (≈150字)

Output: Write ALL entries to the <!-- AUTO --> block of wiki/index.md (Categories section).
Preserve any existing <!-- MANUAL --> blocks.
```

---

## 7. Deep Read Protocol (Detailed)

### Trigger

User says: **"深读 {card_name}"** / **"deep read {card_name}"** / **"查看 {card_name} 原文"** / **"回查原文"**

### Process

1. **Locate the card**: Search wiki/ for the named card file (`{slug}.md`)
2. **Read frontmatter**: Extract `source_file`, `source_url`, `source_type` fields
3. **Determine source type and respond**:

   **If `source_file` exists** (local file):
   > 📎 原文已保存：`{kb_root}/raw/{source_file}`
   >
   > 你可以在 Obsidian 中打开该卡片，同时用系统 PDF 阅读器打开原文并排阅读。
   > 如需在命令行中查看：`cd {kb_root} && {platform_open_cmd} raw/{source_file}`

   **If `source_url` exists** (arXiv or web URL):
   > 🔗 原文链接：{source_url}
   >
   > 你可以用浏览器打开该链接查看完整内容。

   **If neither exists**:
   > 这篇卡片没有关联原文。你可以在 `{kb_root}/raw/` 下放入 PDF 或文档，
   > 然后对我说「把 raw/ 下的 {filename} 链接到 {card_name}」。

4. **Extract key passages** from the card content that reference specific sections, page numbers, or figures in the original. Present them with original-context pointers:
   > 卡片中"Transformer 通过自注意力机制..."这一段的对应原文在第 3 页"Scaled Dot-Product Attention"章节。

5. **Suggest next action**:
   > 读完原文后，如果需要：
   > - 更新卡片内容 → 对我说「更新 {card_name}」
   > - 新建相关卡片 → 对我说「基于这篇论文建一张关于 X 的卡片」
   > - 做更深入的分析 → 对我说「分析 {card_name}，对比 Y」

### Linking a Source File to an Existing Card

When user says "把 raw/{filename} 链接到 {card_name}":

1. Verify the file exists in `raw/`
2. Read the card file
3. Add `source_file` and `source_type` to the YAML frontmatter
4. Update `last_activated` timestamp
5. Confirm to user: "原文链接已添加。现在你可以说「深读 {card_name}」来回查原文。"

### Marking Cards at Import Time

When importing papers via `import_paper.py --mode full`:

The script automatically:
1. Copies the source file to `{kb_root}/raw/{slug}.{ext}` (if local file)
2. Records `source_file`, `source_url`, and `source_type` in frontmatter
3. Adds a source link at the bottom of the card content:
   ```markdown
   ---
   📎 原文链接
   - 本地文件：[\`raw/{filename}\`](raw/{filename})
   ---
   ```

---

## 8. Batch Import Protocol (Full)

**Trigger**: User says "batch import" / "批量导入" / "批量导入markdown" / "批量导入txt" / "import papers" / "导入笔记" / "import {path}" / "快速导入PDF" / "并行导入PDF" / "深度导入论文" / "LLM导入"

**Scope**: Supports single file, multiple files, and mixed format imports.

- **Single file**: Import one file (e.g., `import paper.pdf`)
- **Multiple files**: Import from directory (e.g., `import papers/`)
- **Mixed formats**: Handle .md, .txt, .pdf in same directory

When user requests batch import, follow this protocol:

### Step 1: Detect File Types and Source Type

First, determine if user provided a single file or directory:

- **Single file**: Import just that one file
- **Directory**: Recursively scan for all files

Then analyze file type distribution:

- Count PDF files (.pdf)
- Count Markdown files (.md)
- Count Text files (.txt)
- Count unsupported formats (.docx, .html, .png, etc.)

### Step 2: Determine Available Modes

**Supported formats** (.md, .txt, .pdf):

- **batch_import.py** supports all three formats (.md, .txt, .pdf) → Mode 1 available
- **academic_import.py** supports PDF only → Mode 2 available for PDF files
- **LLM Mode** supports all formats → Mode 3 always available

Agent recommendation strategy:

- **Simple files** (.md/.txt) → Mode 1 (Fast Script) - fast and zero cost
- **PDF < 10 papers** → Mode 1 or Mode 3 (User choice based on quality needs)
- **PDF 10+ papers** → Mode 2 (Parallel Script) - fastest for large batches
- **High quality needed** → Mode 3 (LLM) - structured summary and understanding

**Unsupported formats** (.docx, .html, .png, etc.):

- Only provide Mode 3 (LLM Intelligent Import)
- Agent note: "⚠️ 此格式需要LLM理解处理 / This format requires LLM processing"

### Step 3: Present Available Options to User

**Important**: Agent should NOT make decisions for the user. Instead:

1. Clearly state the current file format situation
2. List all available modes based on file type
3. Explain pros/cons of each mode
4. Provide suggestions (not decisions)
5. Let the user decide

```markdown
## 批量导入 - 模式选择 / Batch Import - Mode Selection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 当前文件检测 / Current File Detection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

导入类型 / Import type: {import_type}
{import_type_description}

检测到以下文件格式 / Detected file formats:
{file_detection_summary}
  • PDF文件: {pdf_count} 个
  • Markdown文件: {md_count} 个
  • Text文件: {txt_count} 个
  • 其他格式: {other_count} 个 ({other_formats})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 可用导入模式 / Available Import Modes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

基于当前文件格式，以下模式可选 / Based on current formats, these modes are available:

【选项 1】脚本快速导入 (Fast Script Mode)
───────────────────────────────────────────────────
✓ 可处理当前所有文件 / Can process all current files
✓ 速度：0.5-2秒/文件 / Speed: 0.5-2s per file
✓ 成本：零成本，无需LLM / Cost: Zero, no LLM needed
✗ 内容质量：原始文本，无结构化 / Quality: Raw text, no structuring

适用场景 / Best for:
• 快速建立知识库底座 / Quick knowledge base setup
• 大量简单文件需要快速入库 / Large simple files need fast import
• 对内容结构化要求不高 / Low requirement for structuring

───────────────────────────────────────────────────

【选项 2】脚本并行导入 (Parallel Script Mode)
───────────────────────────────────────────────────
{mode2_availability}
✓ 速度：最快（2-4倍加速，利用多核）/ Speed: Fastest (2-4x, multi-core)
✓ 成本：零成本，无需LLM / Cost: Zero, no LLM needed
✗ 内容质量：原始PDF文本，无结构化 / Quality: Raw PDF text, no structuring
✗ 格式限制：仅支持PDF / Format limit: PDF files only

适用场景 / Best for:
• 大量PDF文件批量处理 / Large PDF batch processing
• 需要最快速度归档论文 / Need fastest archiving of papers
• 对内容结构化要求不高 / Low requirement for structuring

⚠️ 注意 / Note: {mode2_warning}

───────────────────────────────────────────────────

【选项 3】LLM智能导入 (LLM Intelligent Mode)
───────────────────────────────────────────────────
✓ 可处理所有格式（包括不支持的格式）/ Can process ALL formats
✓ 内容质量：高质量结构化（智能摘要+关键点）/ Quality: High structured content
✓ 灵活性：Agent智能理解文件内容 / Flexibility: AI understands content
✗ 速度：较慢（10-30秒/文件）/ Speed: Slower (10-30s per file)
✗ 成本：消耗平台配额 / Cost: Consumes platform quota

适用场景 / Best for:
• 重要文献需要深度理解 / Important papers need deep understanding
• 不支持的格式（Word、网页等）/ Unsupported formats (Word, web, etc.)
• 需要高质量知识卡片 / Need high-quality knowledge cards
• 希望获得结构化摘要 / Want structured summaries

───────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 建议仅供参考 / Suggestions for Reference Only
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 如果追求速度和效率 / If prioritizing speed and efficiency:
  → 建议选项 1 或 2 / Suggest option 1 or 2

• 如果追求内容质量 / If prioritizing content quality:
  → 建议选项 3 / Suggest option 3

• 如果有 unsupported 格式 / If has unsupported formats:
  → 必须选择选项 3 / Must choose option 3

• 如果不确定 / If unsure:
  → 可以先用选项 1 快速建立索引，再用选项 3 处理重要文件
  / Can use option 1 for quick indexing, then option 3 for important files

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👉 请选择模式 / Please choose mode: 输入 1/2/3 (Enter 1/2/3)
```

**Template Variables**:

- `{import_type}` - Import type: "单个文件 / Single file" or "批量导入 / Batch import"
- `{import_type_description}` - Description of what will be imported
- `{file_detection_summary}` - Summary of detected files
- `{pdf_count}`, `{md_count}`, `{txt_count}`, `{other_count}` - File counts
- `{other_formats}` - List of unsupported formats (e.g., ".docx, .html")
- `{mode2_availability}` - "✓ 可用 / Available" (if PDF present) OR "✗ 不可用 / Unavailable" (no PDF)
- `{mode2_warning}` - Warning if mode2 unavailable or only for PDF files

**Example outputs**:

**Example 1: Single PDF file**

```
导入类型: 单个文件
将导入 1 个文件: paper.pdf

检测到以下文件格式:
  • PDF文件: 1 个
  • Markdown文件: 0 个
  • Text文件: 0 个
  • 其他格式: 0 个

【选项 1】脚本快速导入
✓ 可处理 1 个 PDF 文件

【选项 2】脚本并行导入
✓ 可用 - 可处理 1 个 PDF 文件
⚠️ 注意: 单个文件使用并行模式收益较小，建议选择选项1

【选项 3】LLM智能导入
✓ 可处理 1 个 PDF 文件
```

**Example 2: Mixed formats (.md, .txt, .pdf)**

```
检测到以下文件格式:
  • PDF文件: 15 个
  • Markdown文件: 8 个
  • Text文件: 3 个
  • 其他格式: 0 个

【选项 2】脚本并行导入
✓ 可用 - 可处理 15 个 PDF 文件
⚠️ 注意: 仅处理PDF文件，其他文件将被跳过。如需处理所有文件，请选择选项1或3
```

**Example 3: Unsupported formats only (.docx)**

```
检测到以下文件格式:
  • PDF文件: 0 个
  • Markdown文件: 0 个
  • Text文件: 0 个
  • 其他格式: 5 个 (.docx)

【选项 1】脚本快速导入
✗ 不可用 - 不支持当前文件格式 (.docx)

【选项 2】脚本并行导入
✗ 不可用 - 不支持当前文件格式 (.docx)

【选项 3】LLM智能导入
✓ 可用 - 可处理所有格式，包括 .docx
```

**Example 4: Mixed formats with unsupported (.md, .pdf, .docx)**

```
导入类型: 批量导入
将导入目录中的 20 个文件

检测到以下文件格式:
  • PDF文件: 10 个
  • Markdown文件: 5 个
  • Text文件: 3 个
  • 其他格式: 2 个 (.docx)

【选项 1】脚本快速导入
✓ 可处理 18 个文件 (.md + .txt + .pdf)
⚠️ 注意: 2个.docx文件将被跳过

【选项 2】脚本并行导入
✓ 可用 - 可处理 10 个 PDF 文件
⚠️ 注意: 仅处理PDF文件（10个），其他10个文件将被跳过

【选项 3】LLM智能导入
✓ 可处理所有 20 个文件，包括 .docx
```

**Example 5: Large PDF batch**

```
检测到以下文件格式:
  • PDF文件: 50 个
  • Markdown文件: 0 个
  • Text文件: 0 个
  • 其他格式: 0 个

【选项 2】脚本并行导入
✓ 可用 - 最适合大量PDF文件
⚠️ 注意: 将使用多进程并行处理50个PDF文件，预计耗时约25-50秒
```

### Step 4: Execute Based on User Choice

| User Choice              | Agent Action                                                                   |
| ------------------------ | ------------------------------------------------------------------------------ |
| Mode 1 (Fast Script)     | Run:`python scripts/batch_import.py {source} --category {cat}`               |
| Mode 2 (Parallel Script) | Run:`python scripts/academic_import.py {source} --category {cat} --parallel` |
| Mode 3 (LLM)             | See LLM Mode Protocol below                                                    |

### LLM Mode Protocol (Mode 3)

When user chooses Mode 3, process each file as follows:

1. **Extract file content**:
   - For PDF: Use `lib/format_converter.py` to extract text (first 8000 chars)
   - For .md/.txt: Read file content directly
   - For unsupported formats: Agent analyzes file directly (if platform supports)
2. **Copy file to raw/**: Copy source file to `raw/{slug}.{ext}` for deep read
3. **Apply LLM prompt template**: Use the appropriate template below (Paper vs General)
4. **Generate card**: Use Agent's current LLM capability to generate structured content
5. **Validate format**: Use validation checklist below
6. **Write file**: Save to `wiki/{category}/{slug}.md`
7. **Update checkpoint**: Track progress for resume capability

#### Format-Specific Processing

| Format | Content Extraction                    | Template         |
| ------ | ------------------------------------- | ---------------- |
| .pdf   | `extract_text()` (first 8000 chars) | Paper Template   |
| .md    | Read directly (first 8000 chars)      | General Template |
| .txt   | Read directly (first 8000 chars)      | General Template |
| .docx  | Agent analyzes (if supported)         | General Template |
| .html  | Agent analyzes (if supported)         | General Template |
| Other  | Agent analyzes (if supported)         | General Template |

#### LLM Card Generation Prompt Template

```markdown
请基于以下论文全文，生成高质量的Alaya知识卡片。

论文标题：{title}
分类：{category}

论文全文（前8000字符）：
{text}

请按以下Markdown格式生成完整的知识卡片：

---
title: "{title}"
type: paper
seed_type: REFINED
created_by: academic_llm
strength: 0.7
last_activated: {today}
activation_count: 0
half_life: 30
description: "一句话描述论文核心价值"
source_file: "raw/{slug}.{ext}"
source_type: pdf
tags: ["GNN", "node-classification", "concept-tags"]
created: {today}
updated: {today}
---

# {title}

## Abstract
[2-3句话的中文摘要，说明研究问题、方法、关键发现 / 2-3 sentence Chinese abstract: research problem, method, key findings]

## Contributions
### 概念说明 / Overview
[2-3句话整体概括核心贡献 / 2-3 sentences overview of core contributions]

### 分点详述 / Details
- **贡献一（理论/方法）**：[具体描述，2-3句话 / Contribution 1 (theory/method): specific description, 2-3 sentences]
- **贡献二（算法/架构）**：[具体描述，2-3句话 / Contribution 2 (algorithm/architecture): specific description, 2-3 sentences]
- **贡献三（实验/应用）**：[具体描述，2-3句话 / Contribution 3 (experiment/application): specific description, 2-3 sentences]

## Method
[5-8段详细方法说明 / 5-8 paragraphs detailed method description]
- 问题定义与形式化 / Problem definition and formulation
- 整体架构总览 / Overall architecture overview
- 模块详解（核心组件）/ Module details (core components)
- 训练/优化策略 / Training/optimization strategy

## Key Results
- 主要基准测试/数据集及指标 / Main benchmarks/datasets and metrics
- 对比基线及排名 / Comparison with baselines and ranking
- 消融实验亮点 / Ablation study highlights

## Limitations
[1-2条已知局限性 / 1-2 known limitations]

## Relevance
[与你研究领域的具体关联 / Specific relevance to your research field]

## Concept Tags
- [[图神经网络]] / [[Graph Neural Networks]]
- [[节点分类]] / [[Node Classification]]
- [[相关概念]] / [[Related Concepts]]

## 原始文件 / Original File
[📄 打开原始文件 / Open original file](file:///{file_path})
```

#### LLM Card Generation Prompt Template (General Format)

```markdown
请基于以下文件内容，生成高质量的Alaya知识卡片。

文件标题：{title}
分类：{category}
文件格式：{format}

文件内容（前8000字符）：
{text}

请按以下Markdown格式生成完整的知识卡片：

---
title: "{title}"
seed_type: REFINED
created_by: llm_import
strength: 0.6
last_activated: {today}
activation_count: 0
half_life: 30
description: "一句话描述文件核心内容"
source_file: "raw/{slug}.{ext}"
source_type: {source_type}
tags: ["tag1", "tag2", "tag3"]
created: {today}
updated: {today}
---

# {title}

## 核心内容 / Core Content
[3-5段概括文件核心内容 / 3-5 paragraphs summarizing core content]
- 主要主题 / Main topics
- 关键观点 / Key points
- 重要细节 / Important details

## 关键概念 / Key Concepts
- **概念一**：[说明 / Concept 1: description]
- **概念二**：[说明 / Concept 2: description]
- **概念三**：[说明 / Concept 3: description]

## 价值与应用 / Value and Applications
[文件内容的价值和应用场景 / Value and application scenarios]

## 相关链接 / Related Links
- [[相关概念1]] / [[Related Concept 1]]
- [[相关概念2]] / [[Related Concept 2]]

## 原始文件 / Original File
[📄 打开原始文件 / Open original file](file:///{file_path})
```

#### Generation Requirements

1. **Alaya metadata complete**: Must include all Alaya core fields
2. **Chinese language**: Write in Chinese except technical terms (keep GNN, Transformer, etc.)
3. **Structured content**: Follow template structure strictly
4. **Accurate content**: Based on file content, do not fabricate
5. **Reasonable tags**: Extract core concept tags (2-5 tags)
6. **Format-specific**: Use Paper Template for .pdf, General Template for others

#### Validation Checklist

After generating each card, Agent must verify:

✅ **YAML Format Check**

- [ ] All Alaya core fields present
- [ ] `seed_type: REFINED`
- [ ] `strength: 0.7` (paper) or `0.6` (general)
- [ ] `created_by: academic_llm` (paper) or `llm_import` (general)
- [ ] `description` field is not empty
- [ ] `source_file: "raw/{slug}.{ext}"` exists
- [ ] `source_type` matches actual file type

✅ **Content Structure Check**

- [ ] Abstract/Core Content section exists and is substantive
- [ ] Contributions/Key Concepts section exists with details
- [ ] Method/Value section exists and is detailed
- [ ] No placeholder text (not "[...]" or "待填写")

✅ **File Path Check**

- [ ] File copied to `raw/` directory
- [ ] `source_file` path is correct
- [ ] Card written to `wiki/{category}/{slug}.md`

✅ **Quality Check**

- [ ] Content is based on actual file content
- [ ] Written in Chinese, technical terms in English
- [ ] Structure hierarchy is clear
- [ ] No garbled characters or encoding issues

If validation fails, Agent should:

1. Indicate specific issue
2. Ask user whether to regenerate

### Step 5: Quality Review (Post-Import)

After import completes, **ask user if they want quality review**:

```markdown
## 导入完成 / Import Complete

✅ 导入已完成！是否进行质量审查？

质量审查会检查:
  • Alaya元数据完整性
  • 内容质量（占位符、空章节等）
  • 源文件链接有效性
  • 字符编码问题

[1] 跳过审查，直接构建索引
[2] 进行质量审查

请选择 / Please choose: 输入 1/2
```

If user chooses **Option 1 (Skip)**:

- Proceed directly to Step 6 (Build Index)

If user chooses **Option 2 (Quality Review)**:

1. **Run quality review script**:

   ```bash
   python scripts/import_quality_review.py --category {category} --verbose
   ```
2. **Review results**: Script generates report showing:

   - Total cards reviewed
   - Cards with issues
   - Specific issue types
3. **If issues found**: Ask user if they want Agent to review and fix:

   ```markdown
   ⚠️ 发现 {issue_count} 个卡片存在问题

   是否让Agent智能体进行深度审查和修复？
   • Agent可以智能修复缺失的元数据字段
   • 生成缺失的description
   • 识别和修复内容质量问题

   [1] 跳过，直接构建索引
   [2] Agent深度审查并修复

   请选择 / Please choose: 输入 1/2
   ```
4. **If user chooses Agent review**:

   - Agent reads each problematic card
   - Identifies and fixes issues using LLM
   - Updates card files
   - Re-runs quality review to verify fixes
5. **After quality review**: Proceed to Step 6 (Build Index)

**Quality review script**: `import_quality_review.py`
**Review result location**: `alaya/.import_reviews/{category}_{date}.json`

### Step 6: Build Index

After import completes, always run:

```bash
python scripts/build_index.py --category {category}
```

This updates:

- `wiki/index.md` - Main index
- `wiki/{category}/{category}_category.md` - Category page with descriptions
