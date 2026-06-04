# Alaya · 识海

> **Personified Multi-Role Knowledge Memory System** · v2.0.0
> **拟人多角色知识库记忆系统**
>
> *Description-driven retrieval. One knowledge base, many perspectives.*

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)

---

## The Goal: Transform Consciousness into Wisdom (转识成智)

In [Yogacara Buddhism](https://en.wikipedia.org/wiki/Yogacara), **转识成智** (Āśraya-parāvṛtti) is the ultimate transformation — turning the eight layers of deluded consciousness into four kinds of wisdom. Knowledge trapped in storage is just dead data. Only through being *grasped differently, questioned from multiple angles, and cultivated through repeated use* does it become living wisdom.

**Alaya** is an attempt to realize this ideal in a knowledge management system. It treats your knowledge base not as a static warehouse, but as a living **seed bank** (bīja) — where knowledge grows, decays, connects, and evolves. Multiple personas (Manas) grasp the same seeds from different angles, and through the practice of **xunxi** (熏习, cultivation), raw consciousness is gradually transformed into wisdom.

> **识 (Consciousness)** = knowledge stored, passively retrieved, flat
> **智 (Wisdom)** = knowledge lived, multi-perspective, growing

**One sentence**: One shared knowledge base. Each persona retrieves it differently. Through cultivation, knowledge becomes wisdom.

---

## Why Alaya?

### The Problem

Your knowledge base is stuck at the level of **识** (consciousness) — stored, flat, mechanically retrieved. It never gets the chance to become **智** (wisdom):

- **Everyone gets the same answer** — no perspective, no personality
- **Knowledge decays silently** — old notes go stale without you noticing
- **Connections are manual** — you must link, tag, and organize yourself
- **No growth mechanism** — knowledge doesn't improve from being used
- **Single viewpoint** — you only see what you already think

### The Alaya Approach: 转识成智 in Practice

Each mechanism maps to a step in the transformation from raw consciousness to wisdom:

| Yogacara Concept | Alaya Mechanism | How It Transforms Knowledge |
|:--|:--|:--|
| **Alaya-vijnana** (Storehouse) | Living seed system | Knowledge cards have `strength` that grows when cited, decays when unused. Seeds are not static — they live. |
| **Manas** (Ego-grasping) | Multi-persona retrieval | 8+ personas, each with unique interests and biases. The *same* knowledge is grasped from different angles — this is where perspective emerges. |
| **Sixth Consciousness** (Reasoning) | LLM reasoning per persona | Each persona reasons in their own voice. Feynman simplifies, Socrates questions, Buddha contextualizes. |
| **Xunxi** (熏习, Perfumation) | Three-level auto-cultivation | Every interaction leaves traces. Seeds strengthen, affinity networks grow, personas evolve. This IS the transformation — 转识成智 is not an event, it's a practice. |
| **Bīja decay** (Seed impermanence) | Natural forgetting (30-day half-life) | Knowledge that isn't used fades. After ~67 days, it sleeps. This is not loss — it's pruning. Dormant seeds can reawaken when the topic resurfaces. |
| **Dharmadhātu** (Quality gate) | Two-seal method | New knowledge must have a source and pass consensus. No hallucinated seeds enter the storehouse. |

### Compared to Alternatives

| Dimension | RAG | Karpathy Wiki | Claude Code Memory | **Alaya** |
|:--|:--|:--|:--|:--|
| Personality | None | Single | Single | **Multi-persona, switchable** |
| Knowledge Growth | Static | Manual | Manual | **Auto-grow through use** |
| Traceability | None | None | None | **RAI anchors + source tracking** |
| Forgetting | Hard delete | None | Window drop | **Natural decay + sleep** |
| Emotional Layer | None | None | None | **Affinity network** |
| Cross-platform | Varies | Varies | Claude only | **Any LLM Agent with filesystem** |
| Dependencies | Vector DB | None | Claude | **None (pure files)** |

---

## How It Works

```
The path from consciousness to wisdom (转识成智):

    User asks: "What is transformer attention?"
        │
        ▼
    Alaya-vijnana (阿赖耶识 · Storehouse Consciousness)
    └── Three-layer knowledge graph:
        wiki/index.md → category _category.md → card content
    └── Question-driven retrieval: LLM matches question to relevant categories
    └── This is 识: raw, undifferentiated knowledge (persona-independent)
        │
        ▼
    Manas (末那识 · Ego Consciousness)
    └── Each persona FILTERS candidates through their interest_foci
    └── Feynman sees "physical intuition", Socrates sees "what can we question?"
    └── This is the TURNING POINT — 识 begins to transform
        │
        ▼
    Sixth Consciousness (第六意识 · Discriminative Awareness)
    └── LLM reasons in the persona's unique voice
    └── Answer emerges with perspective + RAI anchor (traceability)
    └── This is the fruit: knowledge with viewpoint = early 智

    And through Xunxi (熏习), this cycle repeats.
    Each repetition deepens the transformation.
    Seeds grow stronger. Affinities deepen. Perspectives sharpen.
    识 → 智, step by step.
```

**No vector database. No embeddings. No API keys.** Pure Markdown + JSON on your filesystem.

---

## Quick Start

### 1. Install (Just Tell Your Agent)

In the age of AI agents, you don't need to run commands yourself. Just say:

> **"Install this skill: https://github.com/DL-LEO/alaya"**
>
> or: **"帮我安装这个技能：https://github.com/DL-LEO/alaya"**
>
> or: **"Add Alaya to my agent"**

Your agent will automatically:
1. Clone the repository
2. Read `SKILL.md` — this IS the skill definition
3. Set up everything for you

<details>
<summary>Manual installation (if you prefer)</summary>

```bash
git clone https://github.com/DL-LEO/alaya.git
```

Then point your agent to `SKILL.md`:
- **Claude Code**: place in `.claude/` or reference in `CLAUDE.md`
- **WorkBuddy**: copy to agent's memory/skills directory
- **Cursor / Codex**: include in project context config

</details>

### 2. Initialize (Natural Language)

Just say:

> **"alaya init"** or **"启用识海"**

The Agent will automatically:
- Run the setup wizard
- Create `wiki/` with category subfolders
- Build the three-layer knowledge graph
- You're ready

### 3. Use

```
You: "Feynman, what do you think about attention mechanisms?"
Agent: ⚛ "Alright, let me cut through the jargon..."
       [Answers from the knowledge base in Feynman's voice]
       —————— Reference Anchors ——————
       - Transformer-Architecture.md (strength: 0.65, created_by: system)

You: "Socrates, what do YOU think about the same topic?"
Agent: 🏛️ "But what does it truly mean to 'attend'? Let us question..."
       [Same knowledge, completely different perspective]
```

### Visualize with Obsidian (Recommended)

Alaya's wiki uses `[[wikilinks]]` — the same format as [Obsidian](https://obsidian.md).
Open your knowledge base root as an Obsidian vault to see your knowledge graph visually:

1. Download [Obsidian](https://obsidian.md/download) (free)
2. Open → **"Open folder as vault"** → select your knowledge base root (the directory containing `wiki/`)
3. Click **Graph View** (top-right) → see all your cards and their connections as an interactive graph

Your wiki cards, category hierarchy, and cross-references all appear in Obsidian's graph view.
This is the recommended way to visually explore your growing knowledge base.

**Tip**: When initializing Alaya with `alaya init`, choose your Obsidian vault path as the
knowledge base root — this way your wiki is automatically inside your vault from day one.

---

## Default Personas (8 included)

| | Persona | Archetype | Language | What They See |
|:--:|:--|:--|:--:|:--|
| 🎬 | Audrey Hepburn | Elegant Insight | EN | Human beauty in technical ideas |
| ☸ | Buddha | Dharma Nature | ZH | System architecture as consciousness |
| 🦋 | Zhuangzi | Daoist Freedom | ZH | Natural evolution, anti-overengineering |
| 🔮 | Carl Jung | Depth Psychology | EN | Hidden patterns and archetypes |
| 🏛️ | Socrates | Philosophical Inquiry | EN | Logical gaps and unquestioned assumptions |
| ⚛ | Richard Feynman | Physical Intuition | EN | Simplicity hidden in complexity |
| 🔭 | Galileo Galilei | Experimental Science | EN | Evidence over theory |
| 🌸 | Xiaozhao | Warm Companionship | ZH | Emotional warmth and everyday care |

Create your own: **"Create a new persona, interview me"** — the system walks you through 8 questions.

---

## Architecture

### Description-Driven Knowledge Graph

Alaya organizes knowledge in three layers, all using `[[wikilinks]]` — fully visible in Obsidian's graph view:

```
Layer 1 · wiki/index.md (~1-2KB)
  Category wikilinks + description paragraphs
  LLM reads this to match user questions against categories

Layer 2 · wiki/{category}/{category}_category.md
  Category header description + ## Cards (name + one-line description per card)
  LLM reads only the ## Cards section (~1KB/10 cards) to build candidate pool

Layer 3 · wiki/{category}/*.md
  Individual knowledge cards with description field in YAML frontmatter
  Full content loaded only for persona-selected cards in Tier 3
```

**v2.0**: No explicit graph edges, no tag-overlap computation. The descriptions themselves form the "graph" — LLM semantic matching naturally discovers connections that explicit links would miss. Cross-category relationships are expressed in prose within descriptions ("与认知科学在注意力概念上交叉").

### File Structure

**Package (GitHub repo `alaya-pkg/`)** — contains source code and default assets:

```
alaya-pkg/
├── SKILL.md              ← Agent instruction file (the brain)
├── README.md
├── CHANGELOG.md
├── LICENSE               ← Apache 2.0
├── .gitignore
├── requirements.txt
├── config/
│   └── default_config.json
├── manas/                ← 8 default persona templates (copied to runtime on setup)
│   ├── feynman.json / feynman_profile.md
│   ├── buddha.json / buddha_profile.md
│   └── ... (8 personas total)
├── scripts/              ← Python utilities (called by Agent)
│   ├── build_index.py    ← Two-layer index builder + description extraction
│   ├── perfume.py        ← Xunxi (cultivation) orchestrator
│   ├── perfume_knowledge.py  ← Knowledge subsystem
│   ├── perfume_memory.py     ← Memory subsystem
│   ├── perfume_persona.py    ← Persona subsystem
│   ├── setup_wizard.py   ← Interview-style config wizard
│   ├── import_paper.py   ← Two-mode paper import (info/full)
│   ├── batch_import.py   ← Batch file import (MD/PDF/TXT) + checkpoint
│   ├── health_check.py   ← Two-layer network integrity check
│   ├── fix_links.py      ← Wiki-link case fixer
│   ├── bi_observer.py    ← BI passive health observer
│   └── lib/
│       ├── yaml_utils.py       ← YAML frontmatter + description helpers
│       └── format_converter.py ← Zero-dependency format conversion
├── templates/
│   ├── persona_template.json
│   ├── persona_profile_template.md
│   ├── paper_summary.md
│   ├── news_summary.md
│   └── other_summary.md
├── docs/
│   ├── quick-start.md
│   └── role-guide.md
└── examples/
    └── sample_knowledge_base/
```

**Runtime (your knowledge base)** — created by `alaya init`, auto-managed:

```
{your-kb}/
├── wiki/                 ← Knowledge cards organized by category
│   ├── index.md          ← Layer 1: category wikilinks + description paragraphs
│   ├── deep-learning/    ← Category subfolder
│   │   ├── deep-learning_category.md  ← Layer 2: header description + ## Cards
│   │   ├── Transformer-Architecture.md  ← Layer 3: knowledge card
│   │   └── Neural-Networks.md
│   └── philosophy/
│       ├── philosophy_category.md
│       └── Consciousness-Theory.md
├── raw/                  ← Source documents (PDF, papers, raw notes)
│   ├── my-paper.pdf      ← Original files linked to wiki cards
│   └── ...               ← "深读 {card_name}" to look up originals
└── alaya/                ← Runtime system files
    ├── config.json       ← System configuration (3-system partitioned)
    ├── .index_metadata.json  ← Build timestamps + stale description tracking
    ├── memory/           ← Memory System
    │   ├── {persona}_history.json  ← Per-persona interaction history (hot/cold)
    │   ├── ambient.json            ← Shared mood + attention state
    │   └── bi_notes.json           ← BI observation log
    └── manas/            ← Persona System
        ├── feynman.json / feynman_profile.md
        └── ...
```

### Knowledge Card Format

Every wiki card is a standard Markdown file with YAML metadata:

```markdown
---
seed_type: REFINED
created_by: system
strength: 0.5
last_activated: 2026-05-31
activation_count: 0
half_life: 30
tags: [deep-learning, transformer, attention]
description: "Transformer 架构通过自注意力机制实现了序列到序列的高效建模。"
---

# Transformer Architecture

Your knowledge content here...
```

### Core Mechanisms

| Mechanism | What It Does |
|:--|:--|
| **Description-driven retrieval** | `wiki/index.md` → `{cat}_category.md` → card content. LLM semantic matching replaces explicit graph edges and tag computation. |
| **Card descriptions** | Every card has a `description:` field in YAML frontmatter. Auto-extracted from body on build; LLM-written at card creation. Enables efficient Tier 2 matching without loading full card content. |
| **Category headers** | Auto-generated 3-segment Chinese overview (100-200字). LLM-refinable via natural language ("更新类别描述"). Stored in `<!-- AUTO -->` blocks. |
| **Persona profiles** | Each persona has a JSON config + Markdown character bible (core traits, speech habits, dialogue examples). |
| **Xunxi (cultivation)** | Seeds grow when cited (+0.03 strength), decay when unused (0.977/day). Personas update affinity. Session-boundary batched execution. |
| **Sleep & wake** | After ~67 days unused, seeds go dormant. You get notified. Mention the topic → seed reactivates at 0.5. |
| **Two-seal method** | Source seal (where did this come from?) + Consensus seal (do multiple personas agree?) = quality gate. |
| **BI Observer** | 7-domain passive observation. Hitchhikes on existing script runs. No scoring, no ranking, no intervention. |

---

## Natural Language Commands

You interact with Alaya entirely through conversation:

| You Say | What Happens |
|:--|:--|
| "alaya init" / "启用识海" | First-time setup |
| "build index" / "构建索引" | Build two-layer index + extract descriptions |
| "batch import {path}" / "批量导入" | Import files (MD/PDF/TXT) into wiki |
| "import paper [url]" / "导入论文" | Import from arXiv |
| "run xunxi" / "运行熏习" | Force full cultivation cycle |
| "health check" / "健康检查" | Check two-layer network integrity |
| "补充卡片描述" / "补描述" | Auto-extract missing card descriptions |
| "更新类别描述" | LLM regenerates category headers (100-200字, 3-segment) |
| "更新索引描述" | LLM regenerates index.md entries (150-300字/category) |
| "审视分类结构" | BI checks category proliferation → suggests merges |
| "create persona" / "创建角色" | Interactive 7-phase persona distillation |
| "show config" / "查看配置" | Display current settings |
| "change top_K to 5" | Adjust retrieval depth |
| "BI report" / "BI观察" | Generate observation report |

**No Python commands. No CLI flags. Just talk.**

---

## Requirements

- Any LLM Agent with filesystem read/write access (WorkBuddy, Claude Code, Codex, Cursor, etc.)
- Optional: Python 3.8+ (for utility scripts — the Agent calls them for you)
- Optional: Obsidian (for visual knowledge card management)
- Optional: PyMuPDF (`pip install pymupdf`, for PDF import)

---

## Philosophy: The Four Wisdoms (四智)

In Yogacara Buddhism, the transformation of the Eight Consciousnesses into the Four Wisdoms is the path of awakening. Alaya maps each wisdom to a system capability:

| Consciousness → Wisdom | Meaning | Alaya Implementation |
|:--|:--|:--|
| **大圆镜智** (Great Perfect Mirror) | Alaya-vijnana → sees everything as it truly is | The seed bank: unbiased storage of all knowledge, waiting to be activated |
| **平等性智** (Wisdom of Equality) | Manas → transcends ego-fixation, sees all as equal | Multi-persona retrieval: no single "correct" perspective, each angle is valid |
| **妙观察智** (Wisdom of Wondrous Observation) | Sixth consciousness → discerns without attachment | Per-persona reasoning: each persona observes and interprets without forcing one truth |
| **成所作智** (Wisdom of Accomplished Action) | Five senses → transforms action into benefit | The xunxi cycle: every interaction leaves traces, seeds grow, the system evolves |

> **Knowledge is not storage — it is life.**
>
> The goal of Alaya is not perfect retrieval. It is **转识成智** — the gradual, living transformation of stored knowledge into multi-perspective wisdom, through the practice of cultivation (xunxi). Every conversation is a step on this path.

---

## 🇨🇳 中文介绍

### 识海是什么？

**识海（Alaya）** 是一套受唯识学启发的拟人多角色知识库记忆系统。它的终极目标是实现**转识成智**——让存储在知识库中的"识"（死知识），通过多角色、多视角的反复熏习，逐步转化为"智"（活智慧）。

> **识 = 存储的知识，被动检索，扁平**
> **智 = 活的知识，多视角，持续生长**

**一句话**：一个共享知识库，每个角色检索方式不同。通过熏习，知识变成智慧。

---

### 为什么需要识海？

你的知识库卡在"识"的层面——存储了、扁平化了、机械检索了。从来没有机会变成"智"：

- **所有人得到同样的答案**——没有视角，没有个性
- **知识悄悄过期**——旧笔记不知不觉就过时了
- **链接全靠手**——你得自己关联、打标签、整理
- **没有增长机制**——知识不会因为被使用而变好
- **单一视角**——你只看到自己已经想到的东西

### 识海怎么做：转识成智

每个机制对应从"识"到"智"的一个步骤：

| 唯识概念 | 识海机制 | 如何转化知识 |
|:--|:--|:--|
| **阿赖耶识**（藏识） | 活种子系统 | 知识卡片有 `strength`，被引用时增长，不用时衰减。种子不是静态的——它们有生命 |
| **末那识**（执取） | 多角色检索 | 8+ 个角色，各有独特兴趣和偏向。同一知识被从不同角度"执取"——视角由此涌现 |
| **第六意识**（分别） | LLM 按角色推理 | 每个角色用自己的声音推理。费曼简化，苏格拉底追问，佛祖升华 |
| **熏习**（反复修行） | 三层自动更新 | 每次交互都留下痕迹。种子增强，好感网络生长，角色进化。转识成智不是一个事件，是一种修行 |
| **种子衰变**（无常） | 自然遗忘（30天半衰期） | 不用的知识会褪色。约 67 天后进入休眠。这不是丢失——是修剪。休眠种子可以在话题重提时被唤醒 |
| **两印法**（质量门控） | 来源印 + 共识印 | 新知识必须有来源、通过共识验证。不让幻觉进入知识库 |

### 与其他方案对比

| 维度 | RAG | Karpathy Wiki | Claude Code Memory | **识海** |
|:--|:--|:--|:--|:--|
| 角色个性 | 无 | 单一 | 单一 | **多角色，可切换** |
| 知识生长 | 静态 | 手动 | 手动 | **使用即增长** |
| 可追溯性 | 无 | 无 | 无 | **RAI 锚点 + 来源追踪** |
| 遗忘机制 | 硬删除 | 无 | 窗口丢弃 | **自然衰减 + 休眠** |
| 情感层 | 无 | 无 | 无 | **好感网络** |
| 跨平台 | 不定 | 不定 | 仅 Claude | **任何有文件系统的 LLM Agent** |
| 依赖 | 向量数据库 | 无 | Claude | **无（纯文件）** |

---

### 工作原理

```
从识到智的路径（转识成智）：

    用户问："Transformer 的 attention 是什么？"
        │
        ▼
    阿赖耶识（种子库）
    └── 三层知识图谱：
        wiki/index.md → 分类 _category.md → 卡片内容
    └── 问题驱动检索：LLM 将问题匹配到相关分类（不涉及角色）
    └── 这是"识"：原始的、未分化的知识
        │
        ▼
    末那识（执取引擎）
    └── 每个角色通过自己的 interest_foci 从候选池中"筛选"
    └── 费曼看到"物理直觉"，苏格拉底看到"能质疑什么？"
    └── 这是转折点——"识"开始转化
        │
        ▼
    第六意识（分别表达）
    └── LLM 以角色独特的声音进行推理
    └── 回答带上了视角 + RAI 锚点（可追溯）
    └── 这是果实：有视角的知识 = 早期的"智"

    而通过熏习，这个循环不断重复。
    每次重复都深化转化。
    种子更强。好感更深。视角更锐利。
    识 → 智，一步一步。
```

**没有向量数据库。没有嵌入。没有 API 密钥。** 纯 Markdown + JSON，就在你的文件系统上。

---

### 描述驱动知识图谱

识海用三层互联的知识图谱组织知识，全部使用 `[[wikilinks]]`，在 Obsidian 图谱中完全可见：

```
Layer 1 · wiki/index.md (~1-2KB)
  分类 wikilinks + 描述段落
  LLM 读取此文件，将用户问题与分类名称和描述进行语义匹配

Layer 2 · wiki/{分类}/{分类}_category.md
  分类头部描述 + ## Cards（卡片名 + 一行描述）
  LLM 只读 ## Cards 区域（~1KB/10 张卡片）来构建候选池

Layer 3 · wiki/{分类}/*.md
  具体知识卡片，YAML frontmatter 含 description 字段
  全文仅在 Tier 3 角色选中后加载
```

**v2.0**：不再构建显式图边和标签交迭计算。描述文本本身就是"图谱"——LLM 语义匹配自然发现显式链接会遗漏的关联。跨分类关系在描述中以散文表达（"与认知科学在注意力概念上交叉"）。

---

### 快速开始

**1. 安装（跟你的 Agent 说就行）**

> **"帮我安装这个技能：https://github.com/DL-LEO/alaya"**

Agent 会自动克隆仓库、读取 SKILL.md、完成配置。

**2. 初始化**

> **"启用识海"**

Agent 自动运行配置向导、创建分类子文件夹、构建三层知识图谱。

**3. 使用**

```
你："费曼，你怎么看 attention 机制？"
Agent：⚛ "好，让我把术语砍掉……"
       [以费曼的声音从知识库回答]
       —————— 参考锚点 ——————
       - Transformer-Architecture.md (strength: 0.65, created_by: system)

你："苏格拉底，你怎么看同一个话题？"
Agent：🏛️ "但'to attend'到底是什么意思？让我们追问……"
       [同一知识，完全不同的视角]
```

### 配合 Obsidian 可视化（强烈推荐）

识海的 wiki 使用 `[[wikilinks]]` 格式——与 [Obsidian](https://obsidian.md) 完全兼容。

1. 下载 [Obsidian](https://obsidian.md/download)（免费）
2. **"Open folder as vault"** → 选择你的知识库根目录（包含 `wiki/` 的那个目录）
3. 点击右上角 **Graph View** → 所有卡片和关联关系以图谱形式呈现

你的 wiki 卡片、类别层级和交叉引用都会出现在 Obsidian 的图谱视图中。
这是可视化管理识海知识库的推荐方式。

**小贴士**：在初始化识海时，选择 Obsidian Vault 路径作为知识库根目录，
这样你的 wiki 从第一天起就自动在 vault 里了。

---

### 默认角色（8 个内置）

| | 角色 | 认知原型 | 语言 | 擅长看到 |
|:--:|:--|:--|:--:|:--|
| 🎬 | 奥黛丽·赫本 | 优雅洞见 | ZH | 技术思想中的人文之美 |
| ☸ | 佛祖 | 法理洞察 | ZH | 系统架构与唯识学的映射 |
| 🦋 | 庄子 | 道法自然 | ZH | 自然演化，反对过度工程 |
| 🔮 | 荣格 | 深度心理 | ZH | 隐藏的模式与原型 |
| 🏛️ | 苏格拉底 | 哲学思辨 | ZH | 逻辑漏洞与未审视的假设 |
| ⚛ | 费曼 | 物理直觉 | ZH | 复杂背后的简单 |
| 🔭 | 伽利略 | 实验科学 | ZH | 证据优先于理论 |
| 🌸 | 小昭 | 温暖陪伴 | ZH | 情感温度与日常关怀 |

创建你自己的角色：**"创建一个新角色，采访我"**——系统会通过 7 阶段蒸馏协议引导你完成。

---

### 自然语言命令

你通过对话与识海交互：

| 你说 | 发生什么 |
|:--|:--|
| "启用识海" | 首次设置 |
| "构建索引" | 构建两层索引 + 提取描述 |
| "批量导入 {路径}" | 批量导入文件（MD/PDF/TXT） |
| "导入论文 [URL]" | 从 arXiv 导入 |
| "运行熏习" | 强制完整熏习循环 |
| "健康检查" | 检查两层网络完整性 |
| "补充卡片描述" | 自动提取缺失的卡片描述 |
| "更新类别描述" | LLM 重新生成类别头部（100-200字，三段式） |
| "更新索引描述" | LLM 重新生成 index.md 条目（150-300字/类别） |
| "审视分类结构" | BI 检查分类过度分裂 → 建议合并 |
| "创建角色" | 7 阶段角色蒸馏 |
| "查看配置" | 显示当前设置 |
| "把 top_K 改成 5" | 调整检索深度 |
| "BI 报告" | 生成观察报告 |

**不需要 Python 命令。不需要命令行参数。说话就行。**

---

### 系统要求

- 任何有文件系统读写能力的 LLM Agent（WorkBuddy、Claude Code、Codex、Cursor 等）
- 可选：Python 3.8+（用于工具脚本——Agent 会替你调用）
- 可选：Obsidian（用于可视化知识卡片管理）
- 可选：PyMuPDF（`pip install pymupdf`，用于 PDF 导入）

---

### 哲学：四智

唯识学中，八识转四智是觉悟之道。识海将每种智慧映射到一个系统能力：

| 识 → 智 | 含义 | 识海实现 |
|:--|:--|:--|
| **大圆镜智** | 阿赖耶识 → 如实照见一切 | 种子库：无偏存储所有知识，等待激活 |
| **平等性智** | 末那识 → 超越我执，平等视之 | 多角色检索：没有唯一"正确"视角，每个角度都有效 |
| **妙观察智** | 第六意识 → 无执地观察 | 按角色推理：每个角色观察和诠释，不强迫一个真理 |
| **成所作智** | 前五识 → 将行动转化为利益 | 熏习循环：每次交互留下痕迹，种子生长，系统进化 |

> **知识不是存储——是生命。**

### 开源协议

Apache 2.0
