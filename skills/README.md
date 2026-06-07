# Alaya 子技能系统

## 概述

Alaya v3.0 采用模块化子技能架构，将核心功能拆分为独立的子技能，按需加载，减少初始 context 占用。

## 子技能列表

| 子技能          | 职责                             | 触发时机                   | 版本   |
| :-------------- | :------------------------------- | :------------------------- | :----- |
| **主技能**       | 初始化、命令路由、版本协调         | 每次会话开始               | 3.0.0  |
| **alaya-retrieval**  | 知识检索、描述驱动匹配         | 用户提问、构建索引         | 2.0.0  |
| **alaya-memory**     | 记忆管理、会话边界、BI 观察     | 会话结束、"记一下"        | 1.0.0  |
| **alaya-persona**    | 角色管理、多角色协议、群组讨论 | 创建角色、多角色对话       | 1.7.0  |
| **alaya-import**     | 论文导入、批量导入、质量审查   | 导入文件                   | 1.0.0  |
| **alaya-maintenance** | 系统维护、健康检查、熏习       | 维护命令                   | 1.0.0  |

## 文件结构

```
alaya/
├── SKILL.md                    # 主技能 (轻量级核心)
├── SKILL_GUIDE.md              # 操作指南
├── SKILL_REF.md               # 详细参考
├── SKILL_FULL.md              # 完整合并版本 (单文件平台)
├── skills/                     # 子技能目录
│   ├── README.md              # 本文件
│   ├── alaya-retrieval/       # 知识检索子技能
│   │   └── SKILL.md
│   ├── alaya-memory/          # 记忆管理子技能
│   │   └── SKILL.md
│   ├── alaya-persona/         # 角色管理子技能
│   │   └── SKILL.md
│   ├── alaya-import/          # 导入功能子技能
│   │   └── SKILL.md
│   └── alaya-maintenance/     # 维护工具子技能
│       └── SKILL.md
├── scripts/                   # Python 脚本 (共享)
├── manas/                     # 默认角色模板
├── templates/                 # 导入模板
├── config/                    # 默认配置
└── examples/                  # 示例知识库
```

## 安装方式

### 方式一：完整安装 (推荐新手)

用户说：

```
"install this skill: https://github.com/DL-LEO/alaya"
```

Agent 执行：

```bash
1. git clone {repo_url} {target_dir}
2. 读取主技能 SKILL.md (核心路由)
3. 自动加载所有子技能 (首次)
4. 运行初始化向导
```

**特点**：一次性安装所有功能，简单直接。

### 方式二：按需安装 (推荐高级用户)

用户说：

```
"install alaya core only" 或 "仅安装识海核心"
```

Agent 执行：

```bash
1. git clone {repo_url} {target_dir}
2. 仅加载主技能 SKILL.md
3. 其他子技能按需加载
```

**特点**：最小初始占用，根据使用自动加载子技能。

## 子技能加载机制

### 自动加载 (主技能控制)

主技能在检测到以下触发词时自动加载对应子技能：

| 用户输入                     | 加载子技能          |
| :--------------------------- | :------------------ |
| (任何问题/询问)              | alaya-retrieval     |
| "记一下"/会话结束             | alaya-memory        |
| "创建角色"/多角色             | alaya-persona       |
| "导入论文"/批量导入           | alaya-import        |
| "健康检查"/熏习              | alaya-maintenance   |

### 手动加载

用户可以明确要求加载特定子技能：

```
"加载识海检索技能"   → 加载 alaya-retrieval
"加载识海记忆技能"   → 加载 alaya-memory
"加载识海角色技能"   → 加载 alaya-persona
"加载识海导入技能"   → 加载 alaya-import
"加载识海维护技能"   → 加载 alaya-maintenance
```

### 子技能状态检查

用户可以检查当前加载的子技能：

```
"查看已加载技能" 或 "list loaded skills"
```

Agent 显示：

```markdown
## 当前加载的子技能

✓ alaya-retrieval (v2.0.0) - 已加载
✓ alaya-memory (v1.0.0) - 已加载
○ alaya-persona (v1.7.0) - 未加载 (按需)
○ alaya-import (v1.0.0) - 未加载 (按需)
○ alaya-maintenance (v1.0.0) - 未加载 (按需)

总 Context 占用: ~15KB (主技能 + 已加载子技能)
```

## Context 占用对比

| 场景                  | 旧版 (v2.x)        | 新版 (v3.0 子技能) |
| :-------------------- | :----------------- | :----------------- |
| **初始会话**          | ~40KB (全量)       | ~8KB (仅主技能)    |
| **用户提问**          | ~40KB              | ~15KB (主+检索)    |
| **创建角色**          | ~40KB              | ~18KB (主+角色)    |
| **批量导入**          | ~40KB              | ~25KB (主+导入)    |
| **多角色讨论**        | ~40KB              | ~30KB (主+角色)    |

## 版本兼容性

### 依赖关系

```yaml
主技能 (alaya >= 3.0.0)
  ├── alaya-retrieval (v2.0.0)  → 依赖: main_skill >= 3.0.0
  ├── alaya-memory (v1.0.0)     → 依赖: main_skill >= 3.0.0
  ├── alaya-persona (v1.7.0)    → 依赖: main_skill >= 3.0.0
  ├── alaya-import (v1.0.0)     → 依赖: main_skill >= 3.0.0
  └── alaya-maintenance (v1.0.0) → 依赖: main_skill >= 3.0.0
```

### 版本检查

主技能在启动时检查子技能版本兼容性：

```
检查 alaya-retrieval 版本...
  ✓ 版本 2.0.0 兼容

检查 alaya-memory 版本...
  ✓ 版本 1.0.0 兼容

检查 alaya-persona 版本...
  ⚠️ 版本 1.5.0 不兼容 (需要 >= 1.7.0)
  → 提示更新
```

## 迁移指南

### 从 v2.x 迁移到 v3.0

1. **备份现有数据**：
   ```bash
   cp -r {your_kb} {your_kb}.backup
   ```

2. **安装 v3.0**：
   ```
   "upgrade alaya to v3.0"
   ```

3. **数据迁移** (自动)：
   - wiki/ 目录保持不变
   - alaya/ 目录保持不变
   - 子技能自动加载

4. **验证**：
   ```
   "健康检查"
   ```

### 自定义子技能

用户可以基于 Alaya 子技能框架创建自定义子技能：

```yaml
---
name: my-alaya-extension
description: "My custom extension for Alaya"
type: subskill
depends_on:
  main_skill: "alaya >= 3.0.0"
trigger_keywords:
  - my-custom-command
---
```

## 故障排除

### 子技能无法加载

**症状**：提示"子技能缺失"

**解决**：
```
1. 检查 skills/ 目录是否存在
2. 检查子技能 SKILL.md 文件是否存在
3. 尝试重新安装： "reinstall alaya"
```

### 版本不兼容

**症状**：提示"版本不兼容"

**解决**：
```
1. 更新主技能： "update alaya"
2. 更新子技能： "update alaya subskills"
3. 手动拉取最新代码
```

### Context 占用过高

**症状**：会话响应变慢

**解决**：
```
1. 检查已加载子技能： "list loaded skills"
2. 卸载未使用子技能 (如果支持)
3. 检查是否有子技能重复加载
```

## 开发者指南

### 添加新子技能

1. 在 `skills/` 下创建新目录：
   ```bash
   mkdir skills/alaya-new-feature
   ```

2. 创建 SKILL.md：
   ```yaml
   ---
   name: alaya-new-feature
   type: subskill
   depends_on:
     main_skill: "alaya >= 3.0.0"
   trigger_keywords:
     - new-feature-command
   ---
   ```

3. 在主技能中添加路由：
   ```
   | 用户说 | 路由到 |
   | :-- | :-- |
   | "新功能命令" | `alaya-new-feature` |
   ```

4. 测试：
   ```
   "加载新功能子技能"
   "测试新功能命令"
   ```

### 子技能最佳实践

1. **独立职责**：每个子技能负责一个明确的功能域
2. **最小依赖**：尽量减少对其他子技能的依赖
3. **清晰触发**：定义明确的触发词和触发条件
4. **版本管理**：独立版本号，明确依赖关系
5. **错误处理**：定义清晰的错误处理和回退机制

## 更新日志

### v3.0.0 (2026-06-07)

**重大变更**：
- 拆分为模块化子技能架构
- 主技能轻量化 (从 ~40KB 到 ~8KB)
- 新增子技能按需加载机制
- 新增子技能版本兼容性检查

**新增功能**：
- 子技能状态检查命令
- 手动子技能加载/卸载
- 自定义子技能支持

**向后兼容**：
- v2.x 数据完全兼容
- 自动迁移工具
- 渐进式升级路径

## 贡献指南

欢迎贡献新的子技能！

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/new-subskill`
3. 在 `skills/` 下创建新子技能目录
4. 编写 SKILL.md 和相关文档
5. 测试并提交 PR

## 许可证

Apache 2.0 - 详见 LICENSE 文件