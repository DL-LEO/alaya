---
name: alaya-import
name_zh: 识海·导入
description: "Paper and batch file import with quality validation and multi-mode support"
version: 1.0.0
author: Liang Shao
license: Apache-2.0
type: subskill
depends_on:
  main_skill: "alaya >= 3.0.0"
  data_dirs: ["wiki/", "raw/"]
trigger_keywords:
  - 导入论文
  - import paper
  - 批量导入
  - batch import
  - 快速导入
  - 深度导入
  - LLM导入
  - 并行导入
---

# Alaya Import · 识海导入

> **将外部知识转化为识海种子**
>
> 从论文、文档、笔记中提取知识，转化为结构化的知识卡片。

## 论文导入协议

### Step 1: 获取元数据

```bash
python scripts/import_paper.py {file_or_url} --mode info
```

返回 JSON：

```json
{
  "title": "Attention Is All You Need",
  "type_hint": "paper",
  "chars": 8500,
  "preview": "We propose a new simple network architecture...",
  "recommendation": "full"
}
```

### Step 2: 呈现选项

向用户呈现检测到的信息并问：

```
(1) **总结摘要** — LLM 按模板结构化 (见 `templates/`)
(2) **全文提取** — 保存完整文本为 wiki 卡片，无截断
```

### Step 3: 执行

**选项 A — Full 模式** (用户想要所有内容)：

```bash
python scripts/import_paper.py {file} --mode full [--category {cat}]
```

脚本提取并保存完整文本为 wiki 卡片，带适当 Alaya frontmatter。
脚本自动在 frontmatter 记录 `source_file`, `source_url`, 和 `source_type`。

**选项 B — Summary 模式** (用户想要总结内容)：

1. 读取适当模板：`templates/paper_summary.md`, `templates/news_summary.md`, 或 `templates/other_summary.md`
2. 用模板结构总结提取文本，在用户最大字符限制内
3. 写填充的卡片到 `wiki/{category}/{slug}.md`
4. 运行：`python scripts/build_index.py --category {cat}`

模板是可编辑 Markdown 文件。用户可通过编辑 `templates/{type}_summary.md` 自定义章节头或添加新章节。

### 源文件链接

导入本地文件时，卡片 frontmatter 将自动包括：

```yaml
---
source_file: "raw/original-filename.pdf"
source_type: "pdf"
---
```

原始文件被复制到 `{kb_root}/raw/` 用于持久存储和未来深读访问。

---

## 批量导入协议 (三模式)

**触发**：用户说 "batch import", "批量导入", "批量导入markdown", "批量导入txt", "import papers", "导入笔记", "import {path}", "快速导入PDF", "并行导入PDF", "深度导入论文", "LLM导入"

**范围**：支持单文件、多文件和混合格式导入。

- **单文件**：仅导入一个文件 (如 `import paper.pdf`)
- **多文件**：从目录导入 (如 `import papers/`)
- **混合格式**：同目录处理 .md, .txt, .pdf

用户请求批量导入时，遵循此协议：

### Step 1: 检测文件类型和源类型

首先，确定用户提供单文件还是目录：

- **单文件**：仅导入该文件
- **目录**：递归扫描所有文件

然后分析文件类型分布：

- 统计 PDF 文件 (.pdf)
- 统计 Markdown 文件 (.md)
- 统计 Text 文件 (.txt)
- 统计不支持格式 (.docx, .html, .png 等)

### Step 2: 确定可用模式

**支持格式** (.md, .txt, .pdf)：

- **batch_import.py** 支持所有三种格式 (.md, .txt, .pdf) → 模式 1 可用
- **academic_import.py** 仅支持 PDF → 模式 2 可用于 PDF 文件
- **LLM 模式** 支持所有格式 → 模式 3 总是可用

**Agent 推荐策略**：

- **简单文件** (.md/.txt) → 模式 1 (快速脚本) - 快速且零成本
- **PDF < 10 论文** → 模式 1 或模式 3 (用户基于质量需求选择)
- **PDF 10+ 论文** → 模式 2 (并行脚本) - 大批量最快
- **需要高质量** → 模式 3 (LLM) - 结构化总结和理解

**不支持格式** (.docx, .html, .png 等)：

- 仅提供模式 3 (LLM 智能导入)
- Agent 注："⚠️ 此格式需要 LLM 理解处理 / This format requires LLM processing"

### Step 3: 向用户呈现可用选项

**重要**：Agent 不应为用户做决定。而是：

1. 清晰陈述当前文件格式情况
2. 列出基于文件类型的所有可用模式
3. 解释每个模式优/缺点
4. 提供建议 (非决定)
5. 让用户决定

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

**模板变量**：

- `{import_type}` - 导入类型："单个文件 / Single file" 或 "批量导入 / Batch import"
- `{import_type_description}` - 将导入什么的描述
- `{file_detection_summary}` - 检测到的文件摘要
- `{pdf_count}`, `{md_count}`, `{txt_count}`, `{other_count}` - 文件计数
- `{other_formats}` - 不支持格式列表 (如 ".docx, .html")
- `{mode2_availability}` - "✓ 可用 / Available" (如果 PDF 存在) 或 "✗ 不可用 / Unavailable" (无 PDF)
- `{mode2_warning}` - 如果模式 2 不可用或仅用于 PDF 文件的警告

### Step 4: 基于用户选择执行

| 用户选择          | Agent 动作                                                                   |
| :---------------- | :--------------------------------------------------------------------------- |
| 模式 1 (快速脚本) | 运行:`python scripts/batch_import.py {source} --category {cat}`            |
| 模式 2 (并行脚本) | 运行:`python scripts/academic_import.py {source} --category {cat} --parallel` |
| 模式 3 (LLM)      | 见下文 LLM 模式协议                                                          |

### LLM 模式协议 (模式 3)

当用户选择模式 3 时，按以下处理每个文件：

1. **提取文件内容**：
   - PDF: 使用 `lib/format_converter.py` 提取文本 (前 8000 字)
   - .md/.txt: 直接读文件内容
   - 不支持格式: Agent 直接分析 (如果平台支持)
2. **复制文件到 raw/**: 复制源文件到 `raw/{slug}.{ext}` 用于深读
3. **应用 LLM 提示模板**: 使用下文适当模板 (Paper vs General)
4. **生成卡片**: 使用 Agent 当前 LLM 能力生成结构化内容
5. **验证格式**: 使用验证检查单
6. **写文件**: 保存到 `wiki/{category}/{slug}.md`
7. **更新检查点**: 跟踪进度支持恢复

#### 格式特定处理

| 格式   | 内容提取                          | 模板           |
| :----- | :-------------------------------- | :------------- |
| .pdf   | `extract_text()` (前 8000 字)   | Paper 模板     |
| .md    | 直接读取 (前 8000 字)            | General 模板   |
| .txt   | 直接读取 (前 8000 字)            | General 模板   |
| .docx  | Agent 分析 (如果支持)            | General 模板   |
| .html  | Agent 分析 (如果支持)            | General 模板   |
| 其他   | Agent 分析 (如果支持)            | General 模板   |

#### LLM 卡片生成提示模板 (论文)

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

#### LLM 卡片生成提示模板 (通用格式)

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

#### 生成要求

1. **Alaya 元数据完整**：必须包括所有 Alaya 核心字段
2. **中文语言**：用中文写，除技术术语 (保留 GNN, Transformer 等)
3. **结构化内容**：严格遵循模板结构
4. **准确内容**：基于文件内容，不要捏造
5. **合理标签**：提取核心概念标签 (2-5 标签)
6. **格式特定**：Paper 用 .pdf，其他用 General 模板

#### 验证检查单

生成每个卡片后，Agent 必须验证：

✅ **YAML 格式检查**

- [ ] 所有 Alaya 核心字段存在
- [ ] `seed_type: REFINED`
- [ ] `strength: 0.7` (paper) 或 `0.6` (general)
- [ ] `created_by: academic_llm` (paper) 或 `llm_import` (general)
- [ ] `description` 字段非空
- [ ] `source_file: "raw/{slug}.{ext}"` 存在
- [ ] `source_type` 匹配实际文件类型

✅ **内容结构检查**

- [ ] Abstract/Core Content 章节存在且实质性
- [ ] Contributions/Key Concepts 章节存在有细节
- [ ] Method/Value 章节存在且详细
- [ ] 无占位符文本 (非 "[...]" 或 "待填写")

✅ **文件路径检查**

- [ ] 文件复制到 `raw/` 目录
- [ ] `source_file` 路径正确
- [ ] 卡片写入 `wiki/{category}/{slug}.md`

✅ **质量检查**

- [ ] 内容基于实际文件内容
- [ ] 用中文写，技术术语用英文
- [ ] 结构层级清晰
- [ ] 无乱码或编码问题

如果验证失败，Agent 应该：

1. 指示具体问题
2. 问用户是否重新生成

### Step 5: 质量审查 (导入后)

导入完成后，**问用户是否要质量审查**：

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

如果用户选 **选项 1 (跳过)**：

- 直接进行 Step 6 (构建索引)

如果用户选 **选项 2 (质量审查)**：

1. **运行质量审查脚本**：

   ```bash
   python scripts/import_quality_review.py --category {category} --verbose
   ```

2. **审查结果**：脚本生成报告显示：

   - 审查的总卡片数
   - 有问题的卡片
   - 具体问题类型

3. **如果发现问题**：问用户是否要 Agent 审查和修复：

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

4. **如果用户选 Agent 审查**：

   - Agent 读每个问题卡片
   - 用 LLM 识别和修复问题
   - 更新卡片文件
   - 重运行质量审查验证修复

5. **质量审查后**：进行 Step 6 (构建索引)

**质量审查脚本**：`import_quality_review.py`
**审查结果位置**：`alaya/.import_reviews/{category}_{date}.json`

### Step 6: 构建索引

导入完成后，总是运行：

```bash
python scripts/build_index.py --category {category}
```

这更新：

- `wiki/index.md` - 主索引
- `wiki/{category}/{category}_category.md` - 分类页面带描述

---

## 深读协议

### 触发

用户说：**"深读 {card_name}"** / **"deep read {card_name}"** / **"查看 {card_name} 原文"** / **"回查原文"**

### 流程

1. **定位卡片**：在 wiki/ 中搜索命名卡片文件 (`{slug}.md`)
2. **读 frontmatter**：提取 `source_file`, `source_url`, `source_type` 字段
3. **确定源类型并响应**：

   **如果 `source_file` 存在** (本地文件)：

   ```
   📎 原文已保存：`{kb_root}/raw/{source_file}`

   你可以在 Obsidian 中打开该卡片，同时用系统 PDF 阅读器打开原文并排阅读。
   如需在命令行中查看：`cd {kb_root} && {platform_open_cmd} raw/{source_file}`
   ```

   **如果 `source_url` 存在** (arXiv 或 web URL)：

   ```
   🔗 原文链接：{source_url}

   你可以用浏览器打开该链接查看完整内容。
   ```

   **如果都不存在**：

   ```
   这篇卡片没有关联原文。你可以在 `{kb_root}/raw/` 下放入 PDF 或文档，
   然后对我说「把 raw/ 下的 {filename} 链接到 {card_name}」。
   ```

4. **提取关键段落**：从卡片内容中引用原文特定章节、页码或图表的关键段落，用原文上下文指针呈现：

   ```
   卡片中"Transformer 通过自注意力机制..."这一段的对应原文在第 3 页"Scaled Dot-Product Attention"章节。
   ```

5. **建议后续动作**：

   ```
   读完原文后，如果需要：
   - 更新卡片内容 → 对我说「更新 {card_name}」
   - 新建相关卡片 → 对我说「基于这篇论文建一张关于 X 的卡片」
   - 做更深入的分析 → 对我说「分析 {card_name}，对比 Y」
   ```

### 链接源文件到现有卡片

当用户说 "把 raw/{filename} 链接到 {card_name}" 时：

1. 验证文件在 `raw/` 中存在
2. 读卡片文件
3. 添加 `source_file` 和 `source_type` 到 YAML frontmatter
4. 更新 `last_activated` 时间戳
5. 向用户确认："原文链接已添加。现在你可以说「深读 {card_name}」来回查原文。"

### 导入时标记卡片

使用 `import_paper.py --mode full` 导入论文时：

脚本自动：
1. 复制源文件到 `{kb_root}/raw/{slug}.{ext}` (如果本地文件)
2. 在 frontmatter 记录 `source_file`, `source_url`, 和 `source_type`
3. 在卡片内容底添加源链接：

   ```markdown
   ---
   📎 原文链接
   - 本地文件：[`raw/{filename}`](raw/{filename})
   ---
   ```

---

## 脚本调用

### 论文导入

```bash
# 获取元数据
python scripts/import_paper.py {file_or_url} --mode info

# 全文导入
python scripts/import_paper.py {file} --mode full [--category {cat}]

# 仅提取 (用于手动处理)
python scripts/import_paper.py {file} --mode extract
```

### 批量导入

```bash
# 模式 1: 快速脚本 (MD/TXT/PDF)
python scripts/batch_import.py {source} --category {cat}

# 模式 2: 并行脚本 (仅 PDF)
python scripts/academic_import.py {source} --category {cat} --parallel

# 检查点恢复 (断点续传)
python scripts/batch_import.py {source} --category {cat} --resume
```

### 质量审查

```bash
python scripts/import_quality_review.py --category {cat} --verbose
```

---

## 配置项

在 `alaya/config.json` 中：

```json
{
  "import": {
    "version": "1.0.0",
    "default_category": "uncategorized",
    "max_chars_for_extraction": 8000,
    "parallel_workers": 4,
    "chunk_size": 100
  }
}
```

| 字段                        | 默认值           | 说明                   |
| :-------------------------- | :--------------- | :--------------------- |
| `default_category`          | "uncategorized"  | 默认导入分类           |
| `max_chars_for_extraction`  | 8000             | 提取最大字符数         |
| `parallel_workers`          | 4                | 并行导入工作进程数      |
| `chunk_size`               | 100              | 批量处理块大小         |

---

## 文件组织

```
{knowledge_base_root}/
├── raw/                              ← 源文档 (用户/Agent 主动放入)
│   ├── my-paper.pdf                  ← 原始论文
│   ├── research-notes.md            ← 原始笔记
│   └── meeting-summary.txt          ← 会议记录
├── wiki/                             ← 知识卡片 (Agent 自动管理)
│   └── {category}/
│       └── {slug}.md                 ← 导入的知识卡片
└── alaya/
    └── .import_reviews/              ← 质量审查报告
        └── {category}_{date}.json
```

---

## 错误处理

### 文件读取失败

```
检测：无法读取源文件
处理：提示用户检查文件路径和权限
回退：如果 LLM 模式，Agent 尝试直接分析 (如果可能)
```

### 格式不支持

```
检测：文件格式在不支持列表 (.docx, .html)
处理：自动切换到 LLM 模式
提示：告知用户 LLM 模式更慢但更准确
```

### 导入中断

```
检测：导入过程被中断
处理：保存检查点
恢复：支持 --resume 继续
```

---

## 与其他子技能的交互

### 与 alaya-retrieval

- 导入后自动构建索引
- 更新分类描述和索引描述
- 确保新卡片可被检索

### 与 alaya-memory

- 导入操作可记录到会话历史
- 支持深读协议回查原文

### 与 alaya-maintenance

- 导入后运行健康检查验证文件完整性
- 质量审查集成到维护流程
- 支持修复链接功能