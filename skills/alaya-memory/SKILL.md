---
name: alaya-memory
name_zh: 识海·记忆
description: "Warm recall protocol with session boundary management and BI observer"
version: 1.0.0
author: Liang Shao
license: Apache-2.0
type: subskill
depends_on:
  main_skill: "alaya >= 3.0.0"
  data_dirs: ["alaya/memory/"]
trigger_keywords:
  - 记一下
  - 保存
  - save
  - 记录
trigger_signals:
  session_boundary: true
  persona_switch: true
---

# Alaya Memory · 识海记忆

> **Per-persona emotional continuity + cross-persona ambient awareness**
>
> 每个角色记住自己的对话历史，同时通过共享环境状态感知全局上下文。

## 记忆架构

Alaya 记忆系统有两层：**角色专属** (详细交互历史) 和 **共享环境** (情绪 + 注意力状态)。

### 角色专属记忆 (`{persona}_history.json`)

每个角色有自己的交互历史，存储在 `alaya/memory/{persona}_history.json`：

```json
{
  "hot": [
    {
      "date": "2026-06-07",
      "topic": "transformer attention mechanism",
      "tags": ["deep-learning", "attention", "transformer"],
      "mood": "好奇",
      "summary": "讨论了 Transformer 的自注意力机制，费曼从物理直觉角度解释了 attention 作为信息聚焦的过程",
      "cards_cited": ["Transformer-Architecture", "Attention-Mechanisms"],
      "turns": 5
    }
  ],
  "cold": [
    {
      "date": "2026-05-20",
      "topic": "quantum entanglement",
      "tags": ["physics", "quantum"],
      "summary": "探讨了量子纠缠的非局域性，费曼强调了实验证据的重要性"
    }
  ]
}
```

- **hot zone**：最新 5 条完整记录 (自动轮转最旧到冷区当满时)
- **cold zone**：更早条目，压缩为摘要 + 标签 (最多 45 条)
- **mood 字段**：2-3 个中文词描述该交互期间用户情绪状态

**记忆是角色隔离的**：费曼只看费曼的交互，小昭只看小昭的。这保持沉浸感 — 每个角色只知道他们参与的对话。

### 共享环境状态 (`ambient.json`)

`alaya/memory/ambient.json` 提供轻量共享上下文 — 像"走进房间看到白板"。

```json
{
  "recent_mood": "好奇",
  "mood_trajectory": ["累", "平静", "好奇"],
  "recent_themes": "最近深入探索了深度学习中的注意力机制，特别是 Transformer 和相关架构，同时对物理直觉与数学形式化的关系产生兴趣",
  "open_threads": [
    {"question": "attention 是否真的可以类比为量子力学中的观察者效应？", "since": "2026-06-01"}
  ],
  "user_style_notes": "喜欢用类比理解复杂概念，偏好物理直觉先行再补数学形式化。对历史背景感兴趣。",
  "recent_attention": {
    "attention": 0.9,
    "transformer": 0.85,
    "quantum": 0.6,
    "consciousness": 0.4
  }
}
```

| 字段               | 维护者        | 策略                                      |
| :----------------- | :------------ | :----------------------------------------- |
| `recent_mood`      | Script (L1)   | 每次交互覆盖                               |
| `mood_trajectory`  | Script (L1)   | 自动推送， capped 3 条                    |
| `recent_themes`    | LLM (边界)    | 每次保存重新合成 (不重用旧值)              |
| `open_threads`     | LLM (边界)    | 添加/维护，capped 3                        |
| `user_style_notes` | LLM (边界)    | 仅追加 — 新发现，永不轮转                   |
| `recent_attention` | Script (L1)   | 0.7x 衰减 + 0.3x 提升，prune <0.1          |

**关注点分离**：Script 维护机械字段 (mood, trajectory, attention)。LLM 维护语义字段 (themes, threads, style_notes) 在会话边界经用户确认。Script 永不覆盖语义字段。

---

## 温暖回忆规则 (如何自然使用记忆)

当你在第 0 层有记忆上下文时，**自然且角色化**地使用它：

### 1. 主动回忆

如果当前话题连接到热区条目，自然引用：

- 费曼看到 `{topic: "transformer", mood: "好奇"}` → "你上次对 transformers 很好奇 — 还在深入吗？"
- 小昭看到 `{topic: "视觉系统", mood: "开心"}` → "公子上次配新视觉的时候好开心呢～"

### 2. 环境感知

使用 ambient.json 感知用户最近状态：

- `recent_mood: "累"` → 小昭主动提供安慰；费曼保持解释更轻
- `recent_attention: {"JEPA": 0.9}` → 任何角色可以承认 "你最近深入 JEPA"

### 3. 情绪连续性

如果用户当前情绪与 recent_mood 不同，承认转变自然：

- 上次 mood 是 "累"，当前消息愉快 → "今天精神不错嘛～比上次好多了"

### 4. 角色特定回忆风格

每个角色回忆不同：

- **知识角色** (费曼/苏格拉底)：话题优先，情绪作为次要色彩
- **陪伴角色** (小昭)：情绪优先，话题作为背景上下文
- **哲学角色** (佛祖/庄子)：模式优先，将过去编织成洞见

### 5. 永不机械引用 JSON 数据

将结构化数据转化为角色声音回忆：

- ❌ 错误："根据记录，我们上次讨论了transformer，您当时情绪为好奇"
- ✅ 正确："上次聊 Transformer 的时候你眼睛都亮了，这次想深入哪里？"

### 6. 尊重记忆边界

角色不应引用他们未参与的交互 (来自其他角色的历史)。使用环境状态进行跨角色感知，非其他角色的热区数据。

### 7. 使用丰富环境字段更深感知

超越 `recent_mood` 和 `recent_attention`，使用语义环境字段：

- `recent_themes` → 理解用户跨所有角色探索的内容。自然引用："你最近对 X 的探索挺深入的..."
- `open_threads` → 在会话开始，如果用户还没带来开放线程，简要承认它存在。不要推 — 只要注意它如果相关。
- `user_style_notes` → 调整你的教学/对话风格。如果用户偏好类比，使用类比。如果他们喜欢苏格拉底式提问，问而非讲。
- `mood_trajectory` → 交叉检查 `recent_themes`。如果 trajectory 显示"困惑→沮丧"但 themes 听起来愉快，themes 可能错了 — 相信 trajectory。

---

## 会话边界检测

### 检测信号 — 加权

| 信号               | 权重  | 示例                                           |
| :----------------- | :---- | :--------------------------------------------- |
| 明确结束           | **High** | "今天就到这里", "先这样", "谢谢很有帮助", "bye" |
| 角色切换意图       | **High** | "我去问问Feynman", "换个人聊", "让XX也来说说"     |
| 话题耗尽           | Medium | 核心问题已解答，用户表达理解，无后续问题       |
| 满足表达           | Low    | "明白了", "原来如此", "清楚了", "有意思"       |
| 冷淡回复           | Low    | 两个连续很短回复 ("嗯", "好", "ok")             |

### 检测规则

- **1 个 High** 或 **2 个 Medium/Low** → 触发保存提示：

```
这次讨论的收获需要我帮你记下来吗？
```

三条响应路径：
- **用户同意** ("好", "记一下吧", "yes", "save it") → 执行保存协议
- **用户拒绝** ("不用", "算了", "no") → 跳过。上次确认状态保持不变。
- **用户忽略 / 关闭窗口** → 跳过。最后确认状态持续。最多一个会话的细节丢失。

### 特殊情况

- **用户说 "记一下" 会话中** → 立即执行保存协议，然后继续。不等待边界检测。
- **群组讨论** → 保存所有参与者历史。
- **保存失败** (文件写错误) → 报告 "保存失败，你可以稍后让我重试" 并保持对话上下文用于手动恢复。
- **3+ 交互无保存** → 如果热区最新条目 >3 交互旧 (通过计数自上次保存提及的回合)，主动提醒："需要我帮你记一下最近的讨论吗？"

---

## 保存协议 — 分步

### Step 1 — 运行机械更新 (脚本)

运行 Level 1 一次，累积此会话的所有数据：

```bash
python scripts/perfume.py --level 1 \
  --cards {all_cited_cards} \
  --persona {name} \
  --mood "{session_mood}" \
  --tags "{all_tags}" \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

这处理：卡片强度提升 (每卡求和)，好感增量，情绪覆盖 + 轨迹推送，注意力标签衰减/提升。

### Step 2 — 准备语义字段 (从对话观察)

基于你在对话中观察到的，为组合保存命令准备语义环境字段和历史条目 (见 Step 3-5)。

### Step 3-5 — 原子保存 (组合)

运行一个脚本调用，原子处理所有剩余三个步骤：

```bash
python scripts/perfume.py --level save \
  --persona {name} \
  --ambient '{"recent_themes":"...","open_threads":[...],"user_style_notes":"..."}' \
  --history '{"topic":"...","tags":[...],"mood":"...","summary":"...","key_insights":[...],"cards_cited":[...],"turns":N}' \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

`--ambient` JSON 接受三个语义字段：

| 字段             | 策略                                                                                                  |
| :--------------- | :---------------------------------------------------------------------------------------------------- |
| `recent_themes`  | **重合成**：基于此对话 + 热历史，写 2-3 句新鲜中文，捕捉用户探索内容和如何。永不重用旧值 — 总是从头重写。 |
| `open_threads`   | **维护**：添加新未解决问题 (用 `{"question": "...", "since": "YYYY-MM-DD"}`)。移除满意解答或 5+ 交互未提的。capped 3。 |
| `user_style_notes` | **仅追加如果新**：只有当你发现用户思考、学习或偏好交互方式的新东西时写。永不轮转或覆盖 — 这会累积。             |

注意：`recent_mood`，`mood_trajectory` 和 `recent_attention` 已由脚本在 Step 1 处理。不要在 `--ambient` 中包含它们。

`--history` JSON 遵循此结构：

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

如果热区超过 5 条，脚本轮换最旧到冷区 (压缩：date, topic, tags, summary)。冷区 capped 45。

脚本自动运行 BI 观察者传递 (休眠角色，知识缺口，好感不对称) 并保存发现到 `bi_notes.json` 和协议检查单到 `_protocol_checklist.json`。

### Step 6 — 向用户确认

Step 3-5 完成后，显示：

```
记忆已保存 ✓
- 情绪轨迹：{mood} → {mood} → {mood}
- 关注主题：{one-line summary of recent_themes}
- 未解问题：{count} 个
```

如果保存的 `bi_notes.json` 记录包含 `system_health` 条目，在确认块后显示它们：

```
{severity_marker} alaya系统提醒您：
  • {问题简述}（{依据数据}）
    → 建议您对智能体说「{自然语言行动}」
```

**Severity marker 规则**：
- 如果任何条目有 `severity=high`：使用 `⚠️`
- 否则：使用 `📋`

**示例输出**：

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

**重要规则**：
- 如果 `system_health` 空 (一切正常)，确认块后不显示额外内容。
- 每个条目必须包含：问题是什么，什么数据支持它，和用户可以对 Agent 说的自然语言行动。
- 永不显示原始命令字符串 (如 "python scripts/build_index.py") — 总是措辞为用户对 Agent 说的话。

### Step 7 (隐式) — 索引刷新检查

保存确认和 BI 注释显示后，检查 `.index_metadata.json`：
- 如果 `stale_descriptions` 非空 → Agent 主动运行"更新类别描述"于陈旧分类
- 如果 BI 检测到 `index_desync` → Agent 触发「同步索引」

---

## BI 观察者协议 (Rule G)

BI (天道观察者) 观察跨角色网络模式。它 **不** 评分、排名、比较或干预。它仅呈现描述性观察供用户行动。

### 设计原则

- 无评分 (永不"费曼比苏格拉底好" — 说"费曼的好感增长更快")
- 无排名 (无排行榜)
- 无自动干预
- 呈现观察，用户决定

### 三观察域

| 域           | 触发       | 数据源                                      | 阈值 / 模式                              | 输出                           |
| :----------- | :--------- | :------------------------------------------ | :--------------------------------------- | :----------------------------- |
| 好感网络     | 会话边界   | 所有 `{persona}.json` affinity + 所有 `_history.json` 热区 | 互信 >0.3 且增长；不对称 >0.15 差距；密集集群 3+ 互信 >0.3 | 描述性配对动态                 |
| 休眠角色     | TIER 0 加载 | 所有 `_history.json` 最后交互日期           | >14 天不活跃 + `bi_enabled=true`         | 温柔提醒：附加到角色选择上下文 — "BI note: {persona} 14+ 天未活跃。他们的兴趣 ({top3}) 可能相关。" 自然结合 (如"庄子也好久没聊了，他对这个话题也有独到看法")，永不上推到无关话题 |
| 知识缺口     | 会话边界   | Persona interest_foci vs wiki/ 分类覆盖 + 卡片计数 | 兴趣区域无 wiki 分类或 <5 卡            | 自然暂停或会话边界时提示，不中断对话流 |

### bi_notes.json 格式

```json
[
  {
    "date": "2026-06-07",
    "affinity_observations": [
      "费曼 ↔ 苏格拉底: 互信 0.45 (+0.08)，双方在'科学方法'话题频繁合作",
      "佛祖 → 庄子: 单向关注 0.38，佛祖常引用庄子观点，庄子较少回应"
    ],
    "dormant_alert": [
      "庄子: 28 天未活跃。建议聊聊'自然演化'或'无为而治'话题。"
    ],
    "knowledge_gap_hint": [
      "伽利略的兴趣'实验验证'对应的分类'实验科学'仅 3 张卡片。建议扩充该领域。"
    ],
    "system_health": [
      {
        "severity": "high",
        "issue": "检测到 3 个脏类别",
        "evidence": "量子物理、机器学习、哲学",
        "action": "建议您对智能体说「重建索引」"
      }
    ]
  }
]
```

---

## 何时读更深记忆

### 用户引用过往对话

"上次我们聊的...", "last time we discussed..."

→ 先搜索热区 tags/summary，然后冷区
→ 时间衰减权重：30d=1.0, 30-60d=0.5, 60d+=0.3
→ 返回 top 3 匹配

### BI 模式分析

读 bi_notes.json 以前观察 + 所有 `_history.json` 热区找当前模式 (见 Rule G)

### 群组讨论开场

读所有参与者热区最近上下文

---

## 熏习系统 (Rule C)

### Level 1 — 会话边界 (批量，用户确认)

Level 1 不再每次回复后运行。所有四个操作累积且可在会话末批量无信息损失运行 (见记忆系统：会话边界协议完整流程)：

| 操作              | 批量策略                             | 保真度损失                                    |
| :---------------- | :----------------------------------- | :-------------------------------------------- |
| 卡片强度提升      | 每卡求和引用，应用一次               | **零** (加法可交换)                           |
| 好感增量          | 计数角色交互，应用一次               | **零**                                        |
| 情绪 + 轨迹推送   | 使用会话最后 mood，推送一次          | **更好** (不填充轨迹用重复)                   |
| 注意力标签衰减    | 每会话衰减一次而非 N 次              | **可忽略** (相对标签排名在会话内保持)         |

**会话期间**：Agent 不在每次回复后更新卡片文件或运行脚本。简单在内存跟踪：哪些卡片被引用，多少次，哪些标签出现，和会话 mood。

**会话边界** (用户确认保存)：用累积数据运行一次：

```bash
python scripts/perfume.py --level 1 \
  --cards {all_cited_cards} \
  --persona {name} \
  --mood "{session_mood}" \
  --tags "{all_tags}" \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

### Level 2 — 话题切换 (Agent 调用脚本)

**触发信号** — 任何以下：

- 用户说："继续", "next", "continue", "下一个", "换个话题"
- 用户问明显不同主题
- 用户说："运行熏习" 或 "run xunxi" (手动触发)
- 会话边界检测 (保存提示时 — 运行 Level 2 作为清理)
- 距上次完整熏习超过 10 轮对话

**Action**：运行 `python scripts/perfume.py --level 2`

### Level 3 — 会话开始 (回填检查)

**Action**：运行 `python scripts/perfume.py --level 3`
(仅当 last_xunxi_time > 24 小时前运行 Level 2)

---

## 脚本调用

### 熏习操作

```bash
# Level 1: 会话边界 (批量更新卡片强度、好感、情绪)
python scripts/perfume.py --level 1 \
  --cards {all_cited_cards} \
  --persona {name} \
  --mood "{session_mood}" \
  --tags "{all_tags}" \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki

# Level 2: 话题切换 (完整熏习循环)
python scripts/perfume.py --level 2 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki

# Level 3: 会话开始 (回填检查)
python scripts/perfume.py --level 3 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

### BI 观察

```bash
# 生成 BI 观察报告
python scripts/bi_observer.py \
  --alaya {ALAYA_ROOT}
```

### 保存记忆

```bash
# 组合保存 (原子操作)
python scripts/perfume.py --level save \
  --persona {name} \
  --ambient '{"recent_themes":"...","open_threads":[...],"user_style_notes":"..."}' \
  --history '{"topic":"...","tags":[...],"mood":"...","summary":"...","key_insights":[...],"cards_cited":[...],"turns":N}' \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

---

## 配置项

在 `alaya/config.json` 中：

```json
{
  "memory": {
    "version": "1.0.0",
    "hot_zone_size": 5,
    "cold_zone_size": 45,
    "mood_trajectory_size": 3,
    "open_threads_limit": 3,
    "attention_decay_rate": 0.7,
    "attention_boost_rate": 0.3,
    "attention_prune_threshold": 0.1
  }
}
```

| 字段                     | 默认值 | 说明                       |
| :----------------------- | :----- | :------------------------- |
| `hot_zone_size`          | 5      | 热区最大条目数             |
| `cold_zone_size`         | 45     | 冷区最大条目数             |
| `mood_trajectory_size`    | 3      | 情绪轨迹 capped 大小        |
| `open_threads_limit`     | 3      | 未解问题 capped 大小        |
| `attention_decay_rate`   | 0.7    | 注意力衰减率               |
| `attention_boost_rate`   | 0.3    | 注意力提升率               |
| `attention_prune_threshold` | 0.1  | 注意力修剪阈值             |

---

## 与其他子技能的交互

### 与 alaya-retrieval

- 第 0 层提供记忆上下文给检索
- 温暖回忆规则增强检索回答的情感连续性
- RAI 锚点为记忆保存提供卡片引用

### 与 alaya-persona

- 记忆是角色隔离的 (每个角色自己的 history)
- 群组讨论保存所有参与者历史
- 好感网络分析使用所有角色 affinity 数据

### 与 alaya-maintenance

- BI 观察者生成维护建议
- 熏习系统维护卡片强度和角色好感
- 健康检查验证记忆文件完整性