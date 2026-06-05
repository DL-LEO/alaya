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
| **Batch Import — Three Modes**                                | **Batch Import Protocol** (see below)                                                                                                                                                           |
| "批量导入笔记" / "批量导入markdown" / "批量导入txt" / "批量导入文件" | 通用导入 →`scripts/batch_import.py`（支持.md/.txt/.pdf）                                                                                                                                           |
| "快速导入PDF"                                                        | Mode 1 (Fast) →`scripts/academic_import.py`                                                                                                                                                        |
| "并行导入PDF"                                                        | Mode 2 (Parallel) →`scripts/academic_import.py --parallel`                                                                                                                                         |
| "深度导入论文" / "LLM导入"                                           | Mode 3 (LLM) → Agent generates with LLM                                                                                                                                                              |
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
| [SKILL_REF.md](SKILL_REF.md)     | User confirms memory save ("记一下") / says "create persona" / "import paper" / "deep read" / or you need script or schema reference | Session Boundary Protocol (detailed), Persona JSON Schema, Persona Creation Protocol (full interview), Paper Import Workflow (detailed), Script Reference (full table), Refinement Prompts (full templates), Deep Read Protocol (detailed) |

**Self-sufficiency guarantee**: Every section in SKILL_GUIDE.md and SKILL_REF.md has a concise version or pointer in this file. If a supplementary file cannot be read, the system continues to function correctly — with slightly less detail for the affected workflow.

For single-file agent platforms (Cursor, Codex, etc.), use [SKILL_FULL.md](SKILL_FULL.md) — the auto-merged version containing all content.

---

## Batch Import Protocol [THREE MODES]

**Scope**: Supports single file, multiple files, and mixed format imports.

- **Single file**: Import one file (e.g., `import paper.pdf`)
- **Multiple files**: Import from directory (e.g., `import papers/`)
- **Mixed formats**: Handle .md, .txt, .pdf in same directory

When user requests batch import ("批量导入", "import papers", "导入笔记", etc.), follow this protocol:

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

### Step 4: Quality Review (Post-Import)

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

- Proceed directly to Step 5 (Build Index)

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
5. **After quality review**: Proceed to Step 5 (Build Index)

**Quality review script**: `import_quality_review.py`
**Review result location**: `alaya/.import_reviews/{category}_{date}.json`

### Step 5: Build Index

After import completes, always run:

```bash
python scripts/build_index.py --category {category}
```

This updates:

- `wiki/index.md` - Main index
- `wiki/{category}/{category}_category.md` - Category page with descriptions

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

`alaya/memory/ambient.json` provides lightweight shared context — like "walking into a room and seeing the whiteboard":

```json
{
  "recent_mood": "好奇",
  "mood_trajectory": [
    {"mood": "困惑", "date": "2026-06-01"},
    {"mood": "好奇", "date": "2026-06-01"}
  ],
  "recent_themes": "用户在探索 Transformer 与 Yogacara 哲学的类比，偏好直觉理解而非数学推导",
  "open_threads": [
    {"question": "JEPA 与传统自编码器的关系", "since": "2026-06-01"}
  ],
  "user_style_notes": "喜欢用类比理解技术概念；偏好苏格拉底式追问",
  "recent_attention": {"transformer": 0.8, "yogacara": 0.5}
}
```

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

**Boundary Detection** — monitor for these weighted signals:

| Signal                       | Weight         | Examples                            |
| ---------------------------- | -------------- | ----------------------------------- |
| Explicit closing             | **High** | "今天就到这里", "再见", "thank you" |
| Persona switch intent        | **High** | "我去问问Feynman", "换个人聊聊"     |
| Topic exhaustion             | Medium         | No follow-up questions              |
| Satisfaction / disengagement | Low            | "明白了" / single-word replies      |

When one High or two Medium/Low signals detected, prompt:

> 这次讨论的收获需要我帮你记下来吗？

If user agrees, execute Save Protocol (3 steps):

1. **Mechanical update**: `python scripts/perfume.py --level 1 --cards {all_cited} --persona {name} --mood "{mood}" --tags "{tags}" --alaya DIR --wiki DIR`
2. **Semantic prep**: Prepare `--ambient` JSON (`recent_themes`, `open_threads`, `user_style_notes`) and `--history` JSON from conversation observation
3. **Atomic save**: `python scripts/perfume.py --level save --persona {name} --ambient '{...}' --history '{...}' --alaya DIR --wiki DIR`
4. **Confirm**: Display mood trajectory, themes, open threads count
5. **BI health check**: Display any `system_health` items from saved bi_notes.json
6. **Index refresh**: Check `.index_metadata.json` for stale descriptions → auto-run refinement if needed

**Special cases**:

- "记一下" mid-conversation → execute immediately
- Group discussion → save history for ALL participants
- 3+ interactions since last save → proactive reminder

For the full protocol with JSON formats, error handling, and all edge cases, read SKILL_REF.md §1.

#### When to read deeper memory

- **User references past conversation**: "上次我们聊的...", "last time we discussed..."
  → Search hot zone tags/summary first, then cold zone
  → Time-decay weighting: 30d=1.0, 30-60d=0.5, 60d+=0.3
  → Return top 3 matches
- **BI pattern analysis**: Read bi_notes.json for previous observations + all `_history.json` hot zones for current patterns (see Rule G)
- **Group Discussion opening**: Read hot zone of all participants for recent context

#### BI Observer Protocol (Rule G)

BI (天道观察者) observes patterns across the persona network. It does NOT score, rank, compare, or intervene. It only surfaces descriptive observations for the user to act on.

**Design principles:**

- **No scoring**: Never say "Feynman is better than Socrates." Say "Feynman's affinity has grown faster recently."
- **No ranking**: Never produce leaderboards or top-N lists with value judgments.
- **No automatic intervention**: BI observations are presented to the user. The user decides what to do.

**Three observation domains:**

| Domain           | Trigger                   | Data Source                                                                | Output                                                           |
| ---------------- | ------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Affinity network | Session boundary (Step 5) | All `{persona}.json` affinity sections + all `_history.json` hot zones | Descriptive insight about persona pair dynamics                  |
| Dormant personas | Tier 0 loading            | All `_history.json` last interaction dates                               | Alert if any persona >14d inactive, with their top interest_foci |
| Knowledge gaps   | Session boundary (Step 5) | Persona interest_foci vs. wiki/ category coverage + card counts            | Hint if interest area lacks category or is thin (<5 cards)       |

**Affinity network patterns to watch:**

- **Mutual growth**: Both directions >0.3 and both growing → user enjoys pairing these personas
- **Asymmetric**: One direction >0.15 above the other → one persona consistently invoked alongside another
- **Dense clusters**: 3+ personas with mutual affinity >0.3 → potential group discussion domain 

**Dormant persona detection (Tier 0):**
When loading ambient + history at Tier 0, also check all personas' last interaction dates. If any persona hasn't been interacted with for 14+ days and `bi_enabled` is true, append to persona selection context:

> BI note: {persona} hasn't been active for {N} days. Their interest_foci ({top3}) may have relevant perspective if the user's current topic overlaps.

This is a gentle nudge, not a recommendation. The Agent should incorporate it naturally — for example, if the user asks about a topic that overlaps with a dormant persona's interests, the Agent might mention: "Zhuangzi 也好久没聊了，他对这个话题也有独到的看法。" But NEVER push a dormant persona onto an unrelated topic.

**Knowledge gap hints:**
When BI detects an interest area with no matching wiki category or thin content (<5 cards), the Agent may suggest it when relevant to the conversation topic. But don't interrupt the flow — save these hints for natural pauses or session boundaries.

**bi_notes.json format:**

```json
[
  {
    "date": "2026-06-01",
    "affinity_observations": [],
    "dormant_alert": [],
    "knowledge_gap_hint": []
  }
]
```

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
