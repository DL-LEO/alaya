---
name: alaya-maintenance
name_zh: 识海·维护
description: "System health checks, xunxi cycles, and maintenance utilities"
version: 1.0.0
author: Liang Shao
license: Apache-2.0
type: subskill
depends_on:
  main_skill: "alaya >= 3.0.0"
  data_dirs: ["wiki/", "alaya/"]
trigger_keywords:
  - 健康检查
  - health check
  - 运行熏习
  - run xunxi
  - 修复链接
  - fix links
trigger_commands:
  - BI report
  - BI观察
  - 天道观察
  - show config
  - 查看配置
---

# Alaya Maintenance · 识海维护

> **维护识海系统的健康与活力**
>
> 通过熏习、健康检查和 BI 观察，保持知识库的生长和系统的健康。

## 熏习系统 (Rule C)

熏习 (Xunxi) 是识海的核心维护机制，通过三层更新保持系统的活力：知识卡片、角色好感、记忆状态。

### Level 1: 会话边界 (批量)

```bash
python scripts/perfume.py --level 1 \
  --cards {all_cited} \
  --persona {name} \
  --mood "{session_mood}" \
  --tags "{all_tags}" \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

**处理**：
- **卡片强度提升**：求和每卡引用后一次性应用 (零信息损失)
- **好感增量**：计数角色交互后一次性应用
- **情绪覆盖 + 轨迹推送**：使用会话最后 mood，推送一次 (更好 - 不填充重复)
- **注意力标签衰减**：每会话衰减一次而非 N 次 (可忽略 - 相对标签排名在会话内保持)

**会话期间**：Agent 不在每次回复后更新卡片文件或运行脚本。简单在内存跟踪：哪些卡片被引用，多少次，哪些标签出现，和会话 mood。

**会话边界** (用户确认保存)：用累积数据运行一次。

### Level 2: 话题切换

**触发信号** — 任何以下：

- 用户说："继续", "next", "continue", "下一个", "换个话题"
- 用户问明显不同主题
- 用户说："运行熏习" 或 "run xunxi" (手动触发)
- 会话边界检测 (保存提示时 — 运行 Level 2 作为清理)
- 距上次完整熏习超过 10 轮对话

**Action**：运行 `python scripts/perfume.py --level 2`

```bash
python scripts/perfume.py --level 2 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

### Level 3: 会话开始 (后台检查)

**Action**：运行 `python scripts/perfume.py --level 3`

```bash
python scripts/perfume.py --level 3 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

仅在距上次 xunxi > 24h 时运行 Level 2。

---

## 健康检查

### 触发

用户说 "健康检查" 或 "health check"

### 执行

```bash
python scripts/health_check.py
```

### 检查项

- [ ] **三层网络完整性** (index → category → card)
  - index.md 存在且格式正确
  - 所有分类目录存在
  - 分类文件有 ## Cards 部分
  - 卡片文件可访问

- [ ] **角色配置完整性** (JSON + profile.md)
  - manas/ 下每个角色有 JSON 文件
  - JSON 格式正确且包含必需字段
  - 对应 profile.md 文件存在 (可选但推荐)

- [ ] **元数据覆盖率** (description, tags)
  - 所有卡片有 description 字段
  - 所有卡片有 tags 字段
  - 强度值在合理范围 (0-1)

- [ ] **链接有效性** (wikilinks)
  - 所有 [[wikilinks]] 指向存在文件
  - 无断链
  - 无循环引用

- [ ] **文件编码问题**
  - 所有文件 UTF-8 编码
  - 无乱码或特殊字符问题

- [ ] **系统文件完整性**
  - config.json 存在且格式正确
  - .index_metadata.json 存在
  - memory/ 目录结构完整

### 输出报告

```markdown
## 识海健康报告

生成时间: {timestamp}
知识库路径: {ALAYA_ROOT}

### 📊 知识图谱状态
✓ index.md 存在
✓ 8 个分类目录
⚠️ 3 个卡片缺少 description
  → 建议: 运行 "补充描述" 自动提取

### 👥 角色系统状态
✓ 8 个角色配置完整
✓ 6 个角色有 profile.md
⚠️ 2 个角色缺少 profile.md
  → 建议: 运行 "创建 {name} profile" 补充

### 🔗 链接完整性
✓ 所有 wikilinks 有效
⚠️ 发现 2 个大小写不匹配链接
  → 建议: 运行 "修复链接"

### 🗂️ 系统文件状态
✓ config.json 存在且格式正确
✓ .index_metadata.json 存在
✓ memory/ 目录结构完整

### 📋 总体评估
健康度: 85% (良好)
建议操作:
  1. 补充缺失描述
  2. 修复链接大小写问题
  3. 为缺失角色创建 profile.md
```

---

## 链接修复

### 触发

用户说 "修复链接" 或 "fix links"

### 执行

```bash
python scripts/fix_links.py
```

### 修复内容

- **Wiki 链接大小写不匹配**
  - 检测 `[[Link]]` vs 实际文件名
  - 自动修正为正确大小写

- **指向不存在卡片的链接**
  - 报告断链
  - 询问是否删除或创建目标卡片

- **循环引用检测**
  - 检测 A→B→A 循环引用
  - 报告循环路径
  - 不自动修复 (需人工判断)

### 输出示例

```markdown
## 链接修复结果

扫描文件: 45 个
检测链接: 128 个

### ✅ 自动修复
- 大小写修正: 3 个
  - [[transformer-architecture]] → [[Transformer-Architecture]]
  - [[attention-mechanism]] → [[Attention-Mechanism]]
  - [[consciousness-theory]] → [[Consciousness-Theory]]

### ⚠️ 发现断链
- 2 个断链:
  - [[NonExistentCard]] 在 quantum-physics_category.md
  - [[AnotherMissingLink]] in consciousness-theory.md

建议操作:
  1. 删除断链
  2. 创建目标卡片
  3. 手动检查并修正

### 🔍 循环引用
- 检测到 1 个循环:
  Transformer-Architecture → Attention-Mechanism → Transformer-Architecture
  → 需人工判断是否合理
```

---

## BI 观察报告

### 触发

用户说 "BI 报告", "BI观察", "天道观察"

### 执行

```bash
python scripts/bi_observer.py
```

### 观察域

| 域           | 数据源                                      | 检测逻辑                                   | 输出                     |
| :----------- | :------------------------------------------ | :----------------------------------------- | :----------------------- |
| **好感网络** | affinity + history                           | 互信 >0.3 且增长；不对称 >0.15 差距；密集集群 3+ 互信 >0.3 | 描述性配对动态           |
| **休眠角色** | history 日期                                | >14 天未活跃                                | 温柔提醒                 |
| **知识缺口** | interest_foci vs wiki/ 分类覆盖 + 卡片计数 | 兴趣区域无分类或 <5 卡                     | 自然暂停或会话边界时提示 |

### 输出示例

```markdown
## BI 观察报告

观察时间: {timestamp}
观察窗口: 最近 30 天

### 💞 好感网络动态

#### 互信增长
- **费曼 ↔ 苏格拉底**: 互信 0.45 (+0.08)
  → 双方在"科学方法"话题频繁合作，形成稳定对话模式

- **小昭 ↔ 赫本**: 互信 0.38 (+0.12)
  → 在"人文关怀"话题上互动增多，形成互补视角

#### 单向关注
- **佛祖 → 庄子**: 单向 0.38 (庄子 → 佛祖: 0.15)
  → 佛祖常引用庄子观点，庄子较少回应
  → 建议: 在道法自然话题中让庄子更多参与

#### 密集集群
- **三人集群**: 费曼(0.9) ↔ 伽利略(0.85) ↔ 苏格拉底(0.8)
  → 在"实验验证"话题形成稳定三角关系
  → 适合复杂科学问题的多视角讨论

### 😴 休眠角色提醒

⏸️ **庄子**: 28 天未活跃
  → 近期兴趣: 自然演化、无为而治、道法自然
  → 建议: 聊聊"自然演化"或"无为而治"话题

⏸️ **小昭**: 16 天未活跃
  → 近期兴趣: 情感陪伴、日常关怀、温暖交流
  → 建议: 在情感话题时主动激活

### 🔍 知识缺口观察

#### 兴趣与库存不匹配
- **伽利略的兴趣 "实验验证"** 对应的分类 "实验科学" 仅 3 张卡片
  → 建议扩充该领域的知识卡片

- **费曼的兴趣 "粒子物理"** 尚无专门分类
  → 建议创建"粒子物理"分类并导入相关内容

#### 分类覆盖不足
- **荣格的兴趣 "集体无意识"** 现有卡片仅 2 张
  → 建议补充集体无意识、原型理论等核心内容

### 📊 系统健康提示

✓ 所有角色活跃度良好 (除庄子、小昭)
✓ 知识覆盖与兴趣匹配度 78%
⚠️ 3 个兴趣领域库存不足
  → 建议优先扩充"实验验证"、"粒子物理"、"集体无意识"
```

---

## 配置管理

### 查看配置

```bash
# 直接读取
read alaya/config.json

# 或通过 Agent 呈现
"show config" 或 "查看配置" → 呈现可读格式
```

### 修改配置

```
"把 top_K 改成 5" → 更新 config.knowledge.top_k = 5
"把 half_life 改成 45" → 更新 config.knowledge.half_life_default = 45
"关闭 BI" → 更新 config.bi_enabled = false
"启用 Alaya" → 更新 config.enabled = true
```

### 配置项说明

```json
{
  "enabled": true,
  "language": "zh",
  "knowledge": {
    "version": "2.0.0",
    "top_k": 3,
    "min_pool": 5,
    "max_cards_per_persona": 5,
    "half_life_default": 30
  },
  "memory": {
    "version": "1.0.0",
    "hot_zone_size": 5,
    "cold_zone_size": 45
  },
  "persona": {
    "version": "1.7.0",
    "default_persona": "feynman"
  },
  "bi_enabled": true,
  "import": {
    "version": "1.0.0",
    "default_category": "uncategorized",
    "max_chars_for_extraction": 8000,
    "parallel_workers": 4
  }
}
```

---

## 维护建议

### 日常维护

```
每次会话结束: 自动 Level 1 熏习
每周一次: "健康检查"
每月一次: "BI 报告" + 审查分类结构
```

### 紧急修复

```
链接断开: "修复链接"
索引不同步: "构建索引" --full
卡片缺失描述: "补充描述"
角色配置损坏: 重新运行 setup_wizard.py
```

### 预防性维护

```
每季度: 审查分类结构，合并过度分裂的分类
每半年: 清理休眠卡片 (strength < 0.1 且 90+ 天未激活)
每年: 备份 wiki/ 和 alaya/ 目录
```

---

## 维护命令速查

| 命令                    | 脚本                              | 频率           |
| :---------------------- | :-------------------------------- | :------------- |
| 构建索引                | `build_index.py --full`          | 导入后/索引损坏 |
| 补充描述                | `build_index.py --full`          | 描述缺失时     |
| 更新类别描述            | Agent LLM 生成                    | BI 检测到陈旧   |
| 更新索引描述            | Agent LLM 生成                    | BI 检测到不同步 |
| 运行熏习 (Level 2)      | `perfume.py --level 2`           | 话题切换/手动  |
| 健康检查                | `health_check.py`                | 每周/异常时     |
| 修复链接                | `fix_links.py`                   | 链接问题时     |
| BI 报告                 | `bi_observer.py`                 | 每月/决策时     |
| 查看配置                | `read config.json`               | 随时           |

---

## 脚本调用

### 熏习操作

```bash
# Level 1: 会话边界 (批量更新)
python scripts/perfume.py --level 1 \
  --cards {all_cited_cards} \
  --persona {name} \
  --mood "{session_mood}" \
  --tags "{all_tags}" \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki

# Level 2: 话题切换 (完整熏习)
python scripts/perfume.py --level 2 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki

# Level 3: 会话开始 (回填检查)
python scripts/perfume.py --level 3 \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

### 健康检查

```bash
python scripts/health_check.py \
  --alaya {ALAYA_ROOT}
```

### 链接修复

```bash
python scripts/fix_links.py \
  --alaya {ALAYA_ROOT} \
  --wiki {ALAYA_ROOT}/wiki
```

### BI 观察

```bash
python scripts/bi_observer.py \
  --alaya {ALAYA_ROOT}
```

---

## 配置项

在 `alaya/config.json` 中：

```json
{
  "maintenance": {
    "version": "1.0.0",
    "auto_xunxi_interval_days": 1,
    "health_check_interval_days": 7,
    "bi_report_interval_days": 30,
    "auto_fix_links": false,
    "stale_description_threshold_days": 60
  }
}
```

| 字段                            | 默认值 | 说明                   |
| :------------------------------ | :----- | :--------------------- |
| `auto_xunxi_interval_days`      | 1      | 自动熏习间隔天数       |
| `health_check_interval_days`    | 7      | 健康检查建议间隔天数   |
| `bi_report_interval_days`       | 30     | BI 报告建议间隔天数    |
| `auto_fix_links`                | false  | 是否自动修复链接       |
| `stale_description_threshold_days` | 60   | 描述陈旧阈值天数       |

---

## 错误处理

### 脚本执行失败

```
检测：脚本返回非零退出码
处理：显示错误信息
回退：提示用户手动检查或运行
```

### 配置文件损坏

```
检测：config.json 格式错误或缺少必需字段
处理：从 config/default_config.json 恢复默认值
提示：告知用户配置已重置
```

### 文件权限问题

```
检测：无法写入文件
处理：检查文件权限
提示：告知用户检查目录权限
```

---

## 与其他子技能的交互

### 与 alaya-retrieval

- 健康检查验证索引完整性
- 链接修复维护检索路径
- 构建索引维护检索数据结构

### 与 alaya-memory

- 熏习系统更新记忆状态
- BI 观察分析记忆模式
- 会话边界触发维护操作

### 与 alaya-persona

- 健康检查验证角色配置
- BI 观察分析角色休眠和好感
- 角色创建后更新配置

### 与 alaya-import

- 导入后自动构建索引
- 质量审查集成到健康检查
- 链接修复处理导入的断链