---
name: Alaya
name_zh: 识海
description: "Personified multi-role knowledge memory system - main orchestrator"
version: 3.0.0
author: Liang Shao
license: Apache-2.0
type: main
subskills:
  - alaya-retrieval
  - alaya-memory
  - alaya-persona
  - alaya-import
  - alaya-maintenance
skill_files:
  core: SKILL.md
  guide: SKILL_GUIDE.md
  reference: SKILL_REF.md
subskills_dir: skills/
compatibility:
  - WorkBuddy (recommended)
  - Claude Code (recommended)
  - Cursor
  - Codex
  - OpenClaw
  - Hermes
  - Any LLM Agent with filesystem read/write access
dependencies:
  - Filesystem read/write permission (for subskills)
  - Optional: Python 3.8+ (for scripts, called automatically by Agent)
  - Optional: Obsidian (recommended for knowledge management)
---

# Alaya · 识海 (主技能)

> **One shared knowledge base. Each persona retrieves it differently.**
>
> The same question asked by an engineer, a philosopher, and a caregiver yields three different perspectives — from the same source.

---

## 快速开始 (3 步)

```bash
# 1. 安装技能 Install Skill (对 Agent 说)
"install this skill: https://github.com/DL-LEO/alaya"
# 或 Gitee (国内更快/Faster in China):
"install this skill: https://gitee.com/DL-LEO-gitee/alaya"
# 中文命令:
"帮我安装这个技能：https://github.com/DL-LEO/alaya"
"帮我安装这个技能：https://gitee.com/DL-LEO-gitee/alaya"

# 2. 初始化知识库 Initialize Knowledge Base
"alaya init" 或 "初始化识海"
# → 选择知识库目录，创建初始结构

# 3. 开始使用 Start Using
"健康检查" 或 "health check"    # 验证系统状态
"Feynman, 什么是量子纠缠？"      # 向角色提问
```

**目录结构说明：**

```
技能代码 (~/.claude/skills/alaya/)     ← 安装时自动克隆
├── SKILL.md                            ← Agent 加载这个文件
├── skills/                             ← 子技能目录
├── scripts/                            ← 工具脚本
└── ...

知识库 (你选择的任何位置)               ← 初始化时创建
├── wiki/                               ← 知识卡片
├── alaya/
│   ├── config.json                     ← 配置
│   ├── memory/                         ← 记忆
│   └── manas/                          ← 角色
└── raw/                                ← 原始文档

~/.alaya_path                            ← 记录知识库位置
```

---

## 核心理念：转识成智

**识 (Consciousness)** = knowledge stored, passively retrieved, flat
**智 (Wisdom)** = knowledge lived, multi-perspective, growing

Alaya 通过多角色、多视角的反复熏习，将存储在知识库中的"识"转化为"智"。

---

## 三系统架构

Alaya 由三个独立子系统组成，各司其职：

| 系统 | 数据目录 | 职责 | 子技能 |
|:--|:--|:--|:--|
| **Knowledge** (知识) | `wiki/` | 三层知识图谱、描述驱动检索 | `alaya-retrieval` |
| **Memory** (记忆) | `alaya/memory/` | 交互历史、情感状态、BI 观察 | `alaya-memory` |
| **Persona** (角色) | `alaya/manas/` | 角色定义、多角色协议 | `alaya-persona` |

每个系统有独立的数据目录、配置字段和版本号，更新互不影响。

---

## 安装方式

### 核心概念：技能代码 vs 用户知识库

Alaya 分为两个独立部分：

| 部分 | 目录 | 内容 | 谁维护 |
|:--|:--|:--|:--|
| **技能代码** | `alaya-code/` | SKILL.md、scripts/、skills/ | 固定，来自仓库 |
| **用户知识库** | `my-knowledge/` | wiki/、alaya/、raw/ | 用户，持续增长 |

**两者可以分离**：技能代码安装一次，知识库可以放在任何地方。

---

### 自动安装

对 Agent 说以下任一语句，Agent 将自动克隆并安装：

```
# English / 英文
"install this skill: https://github.com/DL-LEO/alaya"
"install this skill: https://gitee.com/DL-LEO-gitee/alaya"
"add alaya to my agent"

# 中文
"帮我安装这个技能：https://github.com/DL-LEO/alaya"
"帮我安装这个技能：https://gitee.com/DL-LEO-gitee/alaya"
"添加识海到我的智能体"
```

**源说明：**
- **GitHub**：全球可用，更新最快
- **Gitee**：中国用户推荐，访问更快

**Agent 执行流程：**

```
1. 克隆代码仓库
   git clone {repo} ~/.claude/skills/alaya
   (目标目录因平台而异)

2. 通知用户
   "✓ Alaya 已安装 / Alaya installed"
   "说 'alaya init' 或 '初始化识海' 配置知识库"
```

**最终目录结构：**

```
~/.claude/skills/alaya/          ← 技能代码 (固定)
├── SKILL.md
├── skills/
├── scripts/
└── ...

~/your-knowledge/                ← 知识库 (自定义位置)
├── wiki/
├── alaya/
└── raw/

~/.alaya_path                     ← 路径文件
```

---

## 平台加载指南

### 平台能力分类

| 能力类型 | 说明 | 加载策略 |
|:--|:--|:--|
| **会话时动态读取** | 可在会话期间随时读取文件 | SKILL.md（子技能按需加载） |
| **启动时注入** | 仅在启动时读取文件，会话中不可读取 | SKILL.md + 所有子技能 |

### 各平台加载建议

| 平台 | 能力类型 | 加载文件 |
|:--|:--|:--|
| **Claude Code** | 会话时动态读取 | SKILL.md（子技能自动按需加载） |
| **WorkBuddy** | 会话时动态读取 | SKILL.md（子技能自动按需加载） |
| **Cursor** | 启动时注入 | 见下方清单 |
| **Codex** | 启动时注入 | 见下方清单 |
| **其他平台** | 待检测 | 尝试会话时读取，如失败则使用启动时注入清单 |

### 启动时注入平台文件清单

对于 Cursor、Codex 等启动时注入平台，请在启动时一次性加载以下文件：

```
alaya/
├── SKILL.md                          # 主技能（必需）
└── skills/
    ├── alaya-retrieval/SKILL.md      # 检索子技能（必需）
    ├── alaya-memory/SKILL.md         # 记忆子技能（必需）
    ├── alaya-persona/SKILL.md        # 角色子技能（必需）
    ├── alaya-import/SKILL.md         # 导入子技能（必需）
    └── alaya-maintenance/SKILL.md    # 维护子技能（必需）
```

**总共 6 个文件**，约 80-100KB。

**配置方法**（以 Cursor 为例）：
1. 将 Alaya 克隆到项目目录：`git clone https://github.com/DL-LEO/alaya.git`
2. 在 Cursor 的 `.cursorrules` 或项目配置中添加：
   ```
   @alaya/SKILL.md
   @alaya/skills/alaya-retrieval/SKILL.md
   @alaya/skills/alaya-memory/SKILL.md
   @alaya/skills/alaya-persona/SKILL.md
   @alaya/skills/alaya-import/SKILL.md
   @alaya/skills/alaya-maintenance/SKILL.md
   ```

---

**自动检测方法**：尝试从克隆的仓库读取任意文件。如果读取成功 → 多文件模式。如果无法读取 → 单文件模式。

| 用户说                                                                                     | Agent 路由到           | 触发条件           |
| :------------------------------------------------------------------------------------------ | :--------------------- | :----------------- |
| (任何问题/询问)                                                                            | `alaya-retrieval`      | 默认路由           |
| "记一下" / "save" / 会话结束                                                                | `alaya-memory`         | 会话边界信号       |
| "创建角色" / "克隆角色" / "删除角色" / "各位大佬" / "group discussion" / 叫XX和XX讨论        | `alaya-persona`        | 角色相关关键词     |
| "导入论文" / "import paper" / "批量导入" / "batch import" / "快速导入" / "并行导入" / "LLM导入" | `alaya-import`         | 导入关键词         |
| "健康检查" / "health check" / "运行熏习" / "run xunxi" / "修复链接" / "fix links" / "BI报告"  | `alaya-maintenance`     | 维护关键词         |
| "build index" / "构建索引" / "补充描述" / "更新描述"                                       | `alaya-retrieval`      | 索引相关           |

---

## 首次启动检测 [MANDATORY — 每会话开始时检查]

在每次会话开始时，在其他操作之前，首先定位 Alaya 知识库：

```
STEP 1 — 尝试 ~/.alaya_path (跨平台路径文件):
    如果 ~/.alaya_path 存在:
        读取文件中的 kb_root
        设置 ALAYA_ROOT = kb_root
        如果 {ALAYA_ROOT}/alaya/config.json 存在:
            → 通过路径文件找到。继续到读取配置步骤。

STEP 2 — 回退：当前目录 (向后兼容):
    如果 ALAYA_ROOT 尚未设置 且 alaya/config.json 存在:
        设置 ALAYA_ROOT = 当前目录
        → 通过回退找到。继续到读取配置步骤。

STEP 3 — 未找到 → 首次设置:
    → 这是首次设置。
    → 通知用户："Alaya 尚未配置。让我们开始设置。"

    选项 A [bash 可用]: 运行 `python scripts/setup_wizard.py`
      (setup_wizard.py 结束时自动写入 ~/.alaya_path)
    选项 B [无 bash，手动]: 逐步引导用户:
      1. 选择知识库根目录
      2. 在该目录创建 alaya/ 子目录
      3. 从 config/default_config.json 创建 alaya/config.json
      4. 从 manas/ 复制默认角色到 alaya/manas/
      5. 从 examples/sample_knowledge_base/wiki/ 复制示例到 wiki/
      6. 创建 raw/ 目录用于源文档
      7. 运行 `python scripts/build_index.py` (如果 bash 可用)
      8. 将 kb_root 写入 ~/.alaya_path 供未来会话使用:
         echo "{kb_root}" > ~/.alaya_path
    → 设置完成后，读取并显示 SKILL_GUIDE.md 展示初始化后操作指南。
      如果 SKILL_GUIDE.md 不可用，setup_wizard.py 输出已包含必要的"下一步"
      信息 — 系统仍完全可用。
    → 通知用户："设置完成！说'构建索引'初始化知识图谱，然后尝试向角色提问。"

READ CONFIG:
    读取 {ALAYA_ROOT}/alaya/config.json
    如果 config.enabled == false:
        → Alaya 已暂停。跳过检索和熏习。
        → 如果用户说 "enable Alaya"，设置 config.enabled = true 并继续。
    否则:
        → 系统活跃。使用 ALAYA_ROOT 作为知识库根目录。
        → 运行 `python scripts/perfume.py --level 3` (回填检查，最近则自动跳过)
        → 检查：当前角色是否有 profile.md？如果缺失，建议创建。
```

**重要提示**：

- 在设置完成且 config.enabled 为 true 之前，不要继续基于角色的知识检索。
- `~/.alaya_path` 是纯文本文件，只包含一行：知识库根目录的绝对路径。它在设置时创建一次，每次会话读取。这使得 Alaya 能跨不同 agent 平台 (Claude Code, WorkBuddy, Codex 等) 工作，即使工作目录可能不同。

---

## 跨平台路径兼容

### 路径文件位置

`~/.alaya_path` 在不同操作系统中的实际位置：

| 操作系统 | 路径文件位置 | 用户主目录 |
|:--|:--|:--|
| **Linux/macOS** | `~/.alaya_path` | `/home/{user}/` 或 `/Users/{user}/` |
| **Windows** | `%USERPROFILE%\.alaya_path` | `C:\Users\{username}\` |

### 路径文件格式

路径文件应使用**正斜杠**（跨平台兼容）：

```
E:/projects/alaya
```

或**操作系统原生格式**：

```
E:\projects\alaya
```

### Agent 检测逻辑

Agent 在启动时按以下顺序检测路径文件：

```bash
# 1. 尝试环境变量
if $ALAYA_PATH_FILE exists:
    read from $ALAYA_PATH_FILE

# 2. 尝试标准位置
if ~/.alaya_path exists:
    read from ~/.alaya_path
elif $HOME/.alaya_path exists:
    read from $HOME/.alaya_path
elif $USERPROFILE/.alaya_path exists:
    read from $USERPROFILE/.alaya_path

# 3. 回退到当前目录
if alaya/config.json exists in current directory:
    use current directory as ALAYA_ROOT
```

### 路径分隔符处理

在脚本中使用路径时：

- Python: 使用 `pathlib.Path` 自动处理分隔符
- Bash: 使用变量展开 `${ALAYA_ROOT}/wiki/` 自动转换
- Agent: 始终输出正斜杠格式以保持兼容

---

---

## 按需文件加载

SKILL.md 是自足且独立可用的。以下补充文件为特定场景增加深度：

| 文件                            | 读取时机                                                                                                                   | 包含内容                                                                                                                                                                                                                                   |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [SKILL_GUIDE.md](SKILL_GUIDE.md) | 首次设置完成后                                                                                                            | 初始化后操作指南、下一步、Obsidian 推荐、raw/ 用法                                                                                                                                                                                         |
| [SKILL_REF.md](SKILL_REF.md)     | 用户确认保存 ("记一下") / 说 "创建角色" / "导入论文" / "批量导入" / "深读" / 或你需要脚本或模式参考                        | 会话边界协议 (详细)、角色 JSON 模式、角色创建协议 (完整访谈)、论文导入流程 (详细)、脚本参考 (完整表)、精化提示 (完整模板)、深读协议 (详细)、批量导入协议 (完整 3 模式) |

**自足保证**：SKILL_GUIDE.md 和 SKILL_REF.md 中的每节在本文件中都有精简版或指针。如果补充文件无法读取，系统继续正确运行 — 受影响工作流的细节略少。

对于启动时注入平台 (Cursor, Codex 等)，请参考「平台加载指南」部分获取完整的文件加载清单。

---

## 文件系统约定

```
{knowledge_base_root}/
├── wiki/                               ← 知识系统 (config.knowledge)
│   ├── index.md                        ← 第1层：分类概览 + 描述段落
│   ├── {category-1}/
│   │   ├── {category-1}_category.md    ← 第2层：分类头 + 卡片列表 + 描述
│   │   └── *.md                        ← 第3层：知识卡片
│   └── ...
├── raw/                                ← 源文档 (可选)
│   ├── *.pdf                           ← 原始论文、导入文件
│   ├── *.md                            ← 处理前原始笔记
│   └── ...
└── alaya/                              ← 记忆 + 角色系统
    ├── config.json                     ← 系统配置 (按子系统分区)
    ├── .index_metadata.json            ← 构建时间戳 (自动管理)
    ├── memory/                         ← 记忆系统 (config.memory)
    │   ├── {persona}_history.json      ← 每角色交互历史 (热/冷)
    │   ├── ambient.json                ← 共享情绪 + 注意力状态
    │   └── bi_notes.json               ← BI 观察者模式日志 (最多 20 条)
    └── manas/                          ← 角色系统 (config.persona)
        ├── {persona}.json              ← 角色配置
        └── {persona}_profile.md        ← 角色圣经 (LLM 读取用于声音)
```

**三系统分离**：wiki/ = 知识，alaya/memory/ = 情感记忆，alaya/manas/ = 角色身份。每个系统有自己的数据目录、配置节和版本。更新一个系统不影响其他系统的数据文件。

**config.language**：`config.json` 中的顶层 `language` 字段控制**新创建角色的默认语言** (由 `setup_wizard.py` 使用)。它不覆盖单个角色语言设置 — 每个角色自己 JSON 中的 `language` 字段优先。语言是角色级属性，非系统级。

**角色命名约定**：每个角色有两个名字：
- **规范键** (文件名基)：如 `feynman` — 用作内部唯一标识符，用于文件查找、历史文件、好感键和所有脚本操作
- **显示名** (`persona` 字段)：如 `Richard Feynman` — 在报告和 UI 中向用户显示

所有脚本通过 `lib/yaml_utils.py` 中的 `persona_key()` 将任何标识符 (显示名、中文名、slug、规范键) 解析为规范键。

**raw/ 目录**：将原始文档 (PDF、下载论文、原始笔记) 放在 `raw/` 中。当使用 `import_paper.py --mode full` 或 `batch_import.py` 导入时，源文件路径自动记录在卡片的 YAML frontmatter 中作为 `source_file`。用户随后可以说 "深读 {card_name}" 定位并链接回原始文档。

---

## 默认角色 (8 个内置)

| 角色            | 定位             | 语言 | 兴趣焦点                |
| :-------------- | :--------------- | :---: | :---------------------- |
| Audrey Hepburn  | Elegant Insight   | EN   | humanity, aesthetics, care |
| Buddha          | Dharma Nature     | ZH   | consciousness-only, wisdom |
| Zhuangzi        | Daoist Freedom    | ZH   | natural evolution, wu-wei  |
| Carl Jung       | Depth Psychology  | EN   | archetypes, individuation  |
| Socrates        | Philosophical Inquiry | EN | dialectic, epistemology    |
| Richard Feynman | Physical Intuition    | EN | intuition, simplicity      |
| Galileo Galilei | Experimental Science | EN | evidence, observation      |
| Xiaozhao        | Warm Companionship   | ZH | emotional care, warmth     |

添加更多角色："蒸馏角色" 或 "create persona" — 触发角色创建协议 (7 阶段)。

每个角色也可能有**配套档案文件** (`manas/{name}_profile.md`)，包含丰富角色定义 (核心人设、称呼形式、语言风格、说话习惯、行为规则、对话示例)。JSON 用于脚本管理配置；profile.md 用于 LLM 读取角色深度。

---

## 快速命令映射

```bash
# 系统初始化
"alaya init" 或 "启用识海"           → 运行首次设置向导

# 知识操作
"构建索引" 或 "rebuild index"        → python scripts/build_index.py --full
"补充卡片描述"                       → python scripts/build_index.py --full (自动生成缺失描述)

# 角色操作
"创建角色" 或 "蒸馏角色"             → 7 阶段角色创建协议
"克隆 {name}" 或 "clone {name}"      → 克隆角色 JSON + profile.md 然后定制
"删除角色 {name}"                    → 从 manas/ 删除角色 JSON + profile.md

# 导入操作
"导入论文 {url}"                     → 两模式导入流程
"批量导入 {path}"                    → 三模式批量导入协议

# 维护操作
"运行熏习" 或 "run xunxi"            → python scripts/perfume.py --level 2
"健康检查" 或 "health check"         → python scripts/health_check.py
"修复链接" 或 "fix links"            → python scripts/fix_links.py
"BI报告" 或 "BI观察"                 → python scripts/bi_observer.py

# 配置操作
"查看配置" 或 "show config"           → 读取并显示 alaya/config.json
"把 top_K 改成 N"                    → 更新 config.json 字段
"禁用 BI" 或 "disable BI"            → 更新 config.json → bi_enabled: false
```

**用户永远不应直接运行 Python 命令。** Agent 在这些自然语言触发器后处理所有脚本执行。

---

## 子技能协调

### 共享状态维护

- 所有子技能共享 `ALAYA_ROOT` 环境变量 (从 ~/.alaya_path 读取)
- 子技能间通过 `alaya/` 目录读写传递状态
- `wiki/`、`raw/` 目录为所有涉及子技能共享

### 版本兼容

- 主技能版本 = 核心协议版本
- 子技能独立版本号
- 依赖关系在子技能 frontmatter 声明
- 主技能在启动时检查子技能版本兼容性

### 回退机制

当子技能加载失败时，按以下策略处理：

#### 子技能文件缺失

```
检测：skills/{subskill}/SKILL.md 不存在
处理：
  1. 显示警告："⚠️ 子技能 {name} 未找到，相关功能将受限"
  2. 提供恢复选项：
     - 运行验证：`python scripts/verify_installation.py`
     - 重新安装：`git pull` 或重新克隆仓库
     - 继续：使用主技能基础功能（可能受限）
降级：主技能提供基础功能，高级功能不可用
```

#### 版本不兼容

```
检测：子技能版本 < 主技能要求版本
处理：
  1. 显示警告："⚠️ 子技能 {name} 版本不兼容（当前 v{X}，需要 v{Y}+）"
  2. 提供选项：
     - 更新：`git pull` 获取最新子技能
     - 继续：功能可能不稳定
降级：尝试使用现有版本，可能存在兼容性问题
```

#### 路径未配置

```
检测：~/.alaya_path 不存在或无效
处理：自动触发 setup_wizard.py（见首次启动检测）
```

---

## 架构 (一段式总结)

> 受唯识学八识启发：**Alaya (阿赖耶识)** 是共享种子库 (知识库)。每个 **Manas (末那识)** 是独立执取引擎 (角色，有 interest_foci, affinity, communication style)。**第六识** 是 LLM 推理引擎。单个查询触发从 Alaya 的问答驱动检索：LLM 从 index.md 读取分类描述 (第1层)，扫描分类文件中的卡片描述 (第2层)，构建候选池，然后通过 Manas 分支 — 每个角色从同一候选池选择和解释不同卡片 (第3层)。**记忆系统** 增加情感连续性。知识随更多卡片共享标签空间而增长 → 描述自然表达更丰富交叉连接 → LLM 发现更多不同检索路径。无向量数据库，无图算法 — 纯文件系统 + LLM 语义理解。

---

## 系统要求

- 任何有文件系统读写能力的 LLM Agent (WorkBuddy, Claude Code, Codex, Cursor 等)
- 可选：Python 3.8+ (用于工具脚本 — Agent 替你调用)
- 可选：Obsidian (用于可视化知识卡片管理)
- 可选：PyMuPDF (`pip install pymupdf`，用于 PDF 导入)

---

## 哲学：四智

在唯识学中，八识转四智是觉悟之道。Alaya 将每种智慧映射到一个系统能力：

| 识 → 智        | 含义                   | Alaya 实现                      |
| :-------------- | :--------------------- | :------------------------------ |
| **大圆镜智**   | 阿赖耶识 → 如实照见一切 | 种子库：无偏存储所有知识，等待激活 |
| **平等性智**   | 末那识 → 超越我执，平等视之 | 多角色检索：无单一"正确"视角，每个角度都有效 |
| **妙观察智**   | 第六意识 → 无执地观察     | 按角色推理：每个角色观察和诠释，不强迫一个真理 |
| **成所作智**   | 前五识 → 将行动转化为利益  | 熏习循环：每次交互留下痕迹，种子生长，系统进化 |

> **知识不是存储——是生命。**