---
name: alaya-retrieval
name_zh: 识海·检索
description: "Three-tier knowledge retrieval system with persona filtering and description-driven matching"
version: 2.0.0
author: Liang Shao
license: Apache-2.0
type: subskill
depends_on:
  main_skill: "alaya >= 3.0.0"
  data_dirs: ["wiki/", "alaya/manas/"]
trigger_keywords:
  - (default)  # 任何非特定命令的输入
trigger_commands:
  - build index
  - 构建索引
  - 补充描述
  - 更新类别描述
  - 更新索引描述
  - rebuild index
---

# Alaya Retrieval · 识海检索

> **Question-driven retrieval + Persona filtering**
>
> 用户的一个提问，通过工程师、哲学家、看护者三个角色，会得到三种不同的回答 — 来自同一个知识源。

## 核心设计原则

**检索分为两个阶段**：**问答驱动** (找到相关知识) 和 **角色驱动** (过滤和解释)。

- **第 1-2 层** (Tier 1-2)：问答驱动，确保可靠检索
- **第 3 层** (Tier 3)：角色驱动，塑造解释

Token 效率：第 2 层只读单行描述 (~1KB)；完整卡片内容只在第 3 层为 5 张选中卡片加载。

---

## 核心协议：Rule A (问题驱动检索 + 角色过滤)

### TIER 0: 加载活跃角色 + 记忆上下文

```
用户提问 (可选点名角色)
    ↓
解析角色名：
    → 用户说 "Feynman, explain X" → Richard Feynman
    → 未点名 → 检查所有角色的 triggers:
        - 如果任何角色的 `triggers.active` 匹配用户关键词 → 自动选该角色
        - 如果用户情绪匹配角色的 `triggers.emotions` → 自动选该角色
        - 无匹配 → 使用 manas/ 目录第一个角色 (字母排序)

读取角色配置：
    → 读取 alaya/manas/{role}.json
    → 加载 interest_foci, bias_dimensions, communication, signature_phrases, domain_scope
    → 读取 alaya/manas/{role}_profile.md (如果存在)
        - 加载 YAML 摘要作为 L0 上下文 (<500B，始终加载)
        - 完整档案内容按需加载用于更深角色化

塑造声音：
    → 使用档案的 core persona, address forms, language style ratio, speech habits
    → 使用 signature_phrases 作为额外声音锚点
    → 加载 icon 用于回复和群组讨论的视觉前缀

检查领域边界：
    → 检查 domain_scope:
        - 如果主题在 `domain_scope.owns` → 该角色主导回答
        - 如果主题在 `domain_scope.defers_to` → 建议用户询问目标角色

记忆层 (始终加载，~200 tokens)：
    → 读取 alaya/memory/{role}_history.json 热区 (≤5 条)
        提供：该角色最近的交互 (主题、情绪、标签、摘要)
    → 读取 alaya/memory/ambient.json
        提供：recent_mood (当前情绪状态，共享)
        提供：mood_trajectory (近期情绪弧 — 是更平静？更沮丧？)
        提供：recent_themes (用户探索的内容 — LLM 合成语义摘要)
        提供：open_threads (来自先前对话的未解问题)
        提供：user_style_notes (用户如何偏好学习/思考 — 随时间积累)
        提供：recent_attention {tag: weight} (标签频率，自动维护)

BI 观察者 (如果 bi_enabled)：
    → 读取 alaya/memory/bi_notes.json (如果存在)
        提供：上一次会话的 affinity_observations, dormant_alert, knowledge_gap_hint
```

### TIER 1: 问答驱动的分类选择 (角色独立)

```
读取 wiki/index.md (~1-2KB)
    每个分类条目：[[{cat}/{cat}_category|{cat}]] + 描述段落
    ↓
LLM 将用户问题与分类名和描述进行语义匹配
    ↓
选择 top-K 分类 (K 来自 config.knowledge.top_k，默认 3)
    ↓
此步骤纯问答驱动 — 角色不 influencing 分类选择
```

**注意**：描述以散文自然表达跨分类关系 — LLM 读取"与认知科学在注意力概念上交叉"与读取图边相同。
**跨分类关联**：index.md 各分类条目末尾的 `关联类别` 行提供显式的分类间关联。
**扩展**：选中 top-K 分类后，检查 index.md 中各选中分类的关联类别提示。如用户问题涉及跨领域概念，将关联分类也加入候选列表（不占 top-K 名额，作为补充分类）。

### TIER 2: 构建候选池 (角色独立)

```
为每个选中的分类读取 wiki/{category}/{category}_category.md ## Cards 部分
    从 "## Cards" 标记开始读取 (跳过分类头节省 tokens)
    每行：[[CardName]] — 一句话描述 (~80字/卡，~1KB 总共 10 卡)
    ↓
LLM 将查询与卡片描述进行语义匹配
    → 选择匹配查询的卡片 → 构建候选池
    → min_pool = config.knowledge.min_pool (默认 5)
    ↓
如果 |pool| < min_pool:
    → 回退 A：返回 index.md，使用第 1 层排名的下一个分类，选择更多卡片
    → 回退 B (所有分类耗尽)：包含选中分类的所有剩余卡片
    → 回退 C (New)：检查分类文件的 ## Related Categories 区段
        → 按关联分类的 ## Cards 扩展检索空间
    ↓
输出：仅卡片 ID 列表 (文件路径) — 尚未读完整内容
```

此步骤也问答驱动 — 角色不影响候选池构建。

### TIER 3: 角色驱动的卡片选择 + 深读

```
角色读取候选池卡片描述 (已在第 2 层上下文中) + 自己的 interest_foci
    ↓
LLM 基于 select 卡片匹配角色视角和兴趣的程度进行语义选择
    max_cards_per_persona 张卡片 (默认 5，在 config 中可配置)
    ↓
created_by_bonus：当前角色创建的卡片获得额外考虑
    ↓
仅现在读取选中卡片的完整内容 (~10KB 总共 5 卡)
    ↓
以角色声音提取知识并回答
    ↓
回答时应用温暖回忆 (见记忆系统) + 附加 RAI 锚点
```

### 扩展阅读：跟随跨分类卡片链接

```
深读选定卡片后，扫描卡片的 ## 跨分类链接 区段
    ↓
如果 wiki-link 指向候选池外的卡片且与用户问题语义相关：
    → 将其加入扩展阅读列表（不占 max_cards_per_persona 名额）
    → 提示用户存在跨分类相关内容
```

**关键设计原则**：角色只在第 3 层介入。第 1-2 层问答驱动，确保可靠检索。角色塑造 **解释**，而非检索。

---

## RAI 锚点 (Rule B) - 强制

每个引用知识库卡片的回答必须以：

```markdown
——————  Reference Anchors ——————
Above discussion references:
- {card_title}.md (strength: {value}, created_by: {persona})
```

结尾。

**例外**：纯聊天 (无知识库访问) → 无锚点。

---

## 索引结构 (v2.0)

每个分类文件有两个部分：

- **头部描述** (自动生成，可 LLM 精化)：3-5 句描述分类覆盖的内容
- **## Cards**：`[[CardName]] — description` 对的平面列表。不再有 Core/Peripheral/Dormant 层 — LLM 语义匹配替代基于强度的过滤。

### LLM 精化

当用户说 "更新类别描述" 或 "更新索引描述" (或 BI 检测到陈旧描述) 时，使用提示模板 (见下文)。

Python `build_index.py` 提供机械回退；LLM 提示产生精化版本。

---

## 描述更新协议

### 更新类别描述

**触发**：用户说 "更新类别描述"

```
1. 读取目标分类所有卡片的 description 字段
2. LLM 生成 100-200 字三段式中文描述
3. 写入 {cat}_category.md 的 <!-- AUTO --> 块
```

**提示模板**：

```markdown
输入：分类 slug + {cat}_category.md ## Cards 部分的所有卡片描述

生成中文分类概览。约束：
- 100-200 字
- 3 段结构：
  ① 领域定位 (1句)：本类别在知识体系中的位置与学术/实践语境
  ② 核心议题 (2-3句)：从卡片描述识别的主要主题线，标注卡片间互补/递进/对立关系
  ③ 阅读指引 (1句)：建议的阅读切入点或学习路径
- 使用卡片描述作为原材料 — 蒸馏，不要复制粘贴
- 以散文书写，非要点
- 自然时交叉引用其他分类 ("与XX类别在YY概念上交叉")

输出：将生成的文本写入分类文件的 <!-- AUTO --> 块。
保留任何现有 <!-- MANUAL --> 块。
不要修改 ## Cards 部分。
```

### 更新索引描述

**触发**：用户说 "更新索引描述"

```
1. 读取所有分类的头部描述 (从 {cat}_category.md <!-- AUTO --> 块)
2. LLM 为每个分类生成精化条目
3. 写入 wiki/index.md 的 <!-- AUTO --> 块
```

**提示模板**：

```markdown
输入：wiki/index.md 当前内容 + 所有分类头部 (从 {cat}_category.md <!-- AUTO --> 块)

为索引中的每个分类生成精化条目。约束：
- 每个分类 150-300 字
- 内容要求：
  ① 类别概览 (从分类头蒸馏，非照抄，换个角度表述)
  ② 与其他类别的交叉点 (如"与XX类别在YY概念上交叉" — 仅确有关联时写)
  ③ 适用场景提示 (什么类型的问题应检索此类别)
- 每个条目以 wiki-link 行开始，后跟描述段落
- 以散文书写，非要点
- 如果分类只有 1-2 张卡片，保持条目简洁 (≈150字)

输出：将所有条目写入 wiki/index.md 的 <!-- AUTO --> 块 (Categories 部分)。
保留任何现有 <!-- MANUAL --> 块。
```

---

## 脚本调用

### 构建完整索引

```bash
python scripts/build_index.py --full
```

处理：
- 生成 `wiki/index.md`
- 为所有分类生成 `{cat}_category.md` 文件
- 从卡片正文提取缺失的 `description` 字段
- 自动生成分类头部描述

### 仅更新特定分类

```bash
python scripts/build_index.py --category {category}
```

### 补充缺失描述

```bash
python scripts/build_index.py --full  # 自动检测并生成
```

---

## 配置项

在 `alaya/config.json` 中：

```json
{
  "knowledge": {
    "version": "2.0.0",
    "top_k": 3,
    "min_pool": 5,
    "max_cards_per_persona": 5,
    "half_life_default": 30
  }
}
```

| 字段                   | 默认值 | 说明                       |
| :--------------------- | :----- | :------------------------- |
| `top_k`               | 3      | 第 1 层选择的分类数        |
| `min_pool`            | 5      | 第 2 层最小候选池大小      |
| `max_cards_per_persona` | 5      | 第 3 层每角色最大卡片数    |
| `half_life_default`   | 30     | 新卡片默认半衰期 (天)      |

---

## 索引维护

### 何时需要构建索引

- 首次初始化后
- 导入新卡片后
- 修改分类结构后
- BI 检测到索引不同步时

### 自动刷新

会话边界保存后，主技能检查 `.index_metadata.json`：
- 如果 `stale_descriptions` 非空 → 自动触发 "更新类别描述"
- 如果检测到 `index_desync` → 自动触发 "更新索引描述"

---

## 文件格式规范

### 知识卡片 YAML frontmatter

```yaml
---
seed_type: REFINED
created_by: system
strength: 0.5
last_activated: 2026-06-07
activation_count: 0
half_life: 30
tags: [deep-learning, transformer, attention]
description: "Transformer 架构通过自注意力机制实现了序列到序列的高效建模。"
---

# 卡片标题

卡片内容...
```

### 分类文件格式

```markdown
# 分类名称

<!-- AUTO -->
分类头部描述 (100-200字，由 LLM 生成或精化)
<!-- AUTO -->

## Cards

[[CardName1]] — 卡片描述 (~80字)
[[CardName2]] — 卡片描述 (~80字)
...
```

### index.md 格式

```markdown
# Alaya Knowledge Index

## Categories

<!-- AUTO -->
[[category-1/category-1_category|分类1]] — 分类描述 (150-300字)
[[category-2/category-2_category|分类2]] — 分类描述 (150-300字)
<!-- AUTO -->
```

---

## 错误处理

### 索引缺失

```
检测：index.md 不存在或为空
处理：提示用户 "构建索引"
自动：运行 python scripts/build_index.py --full
```

### 分类目录缺失

```
检测：wiki/{category}/ 不存在
处理：提示用户检查分类路径或创建分类
```

### 卡片描述缺失

```
检测：卡片 YAML 中无 description 字段
处理：运行 build_index.py --full 自动提取
```

---

## 性能优化

### Token 使用估算

| 层级 | 读取内容 | Token 估算 |
|:--|:--|:--|
| TIER 0 | 角色 JSON + 热记忆 | ~500 |
| TIER 1 | index.md | ~1-2KB |
| TIER 2 | ## Cards 部分 | ~1KB/10 卡 |
| TIER 3 | 选中卡片完整内容 | ~10KB/5 卡 |
| **总计** | | **~12-14KB** |

### 按需加载策略

- **始终加载**：角色 JSON、热记忆 (5 条)、ambient.json
- **第 1 层后加载**：index.md
- **第 2 层后加载**：分类文件 ## Cards 部分
- **第 3 层后加载**：选中卡片完整内容

### 缓存友好

- `wiki/index.md` 缓存 (变化频率低)
- 角色文件缓存 (会话内不变)
- 记忆文件按需刷新 (会话边界更新)

---

## 与其他子技能的交互

### 与 alaya-memory

- 第 0 层加载记忆上下文
- 回答时应用温暖回忆协议
- RAI 锚点为记忆保存提供卡片引用

### 与 alaya-persona

- 读取角色配置和档案
- 使用角色 interest_foci 进行第 3 层选择
- 支持多角色和群组讨论协议 (见 alaya-persona)

### 与 alaya-maintenance

- 调用 build_index.py 进行索引维护
- 响应 BI 观察者的索引刷新建议
- 配合健康检查修复索引问题