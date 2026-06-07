# Alaya v3.0 迁移指南

## 概述

Alaya v3.0 引入了模块化子技能架构，大幅减少初始 context 占用，同时保持完全向后兼容。

## 主要变更

### 架构变更

| 方面         | v2.x                            | v3.0                            |
| :----------- | :------------------------------ | :------------------------------ |
| **架构**     | 单体技能                        | 模块化子技能                    |
| **主技能**   | SKILL.md (~40KB)                | SKILL.md (~8KB)                 |
| **子技能**   | 无                               | 5 个独立子技能                  |
| **Context**  | 全量加载 (~40KB)                | 按需加载 (~8-30KB)              |
| **加载方式** | 一次性全部加载                  | 触发式自动加载                  |

### 新增子技能

1. **alaya-retrieval** (v2.0.0)
   - 知识检索、描述驱动匹配
   - 触发：用户提问、构建索引

2. **alaya-memory** (v1.0.0)
   - 记忆管理、会话边界、BI 观察
   - 触发：会话结束、"记一下"

3. **alaya-persona** (v1.7.0)
   - 角色管理、多角色协议、群组讨论
   - 触发：创建角色、多角色对话

4. **alaya-import** (v1.0.0)
   - 论文导入、批量导入、质量审查
   - 触发：导入文件

5. **alaya-maintenance** (v1.0.0)
   - 系统维护、健康检查、熏习
   - 触发：维护命令

## 迁移步骤

### 自动迁移 (推荐)

对 Agent 说：

```
"upgrade alaya to v3.0"
```

Agent 会自动执行：

1. 检测当前版本
2. 备份现有数据
3. 拉取 v3.0 代码
4. 验证数据兼容性
5. 运行健康检查
6. 报告迁移结果

### 手动迁移

如果自动迁移失败，可以手动执行：

#### Step 1: 备份数据

```bash
# 备份知识库
cp -r {your_kb_root} {your_kb_root}.backup

# 或使用 tar
tar -czf alaya_backup_$(date +%Y%m%d).tar.gz {your_kb_root}
```

#### Step 2: 更新代码

```bash
cd {alaya_repo}

# 拉取最新代码
git fetch origin
git checkout v3.0

# 或重新克隆
git clone https://github.com/DL-LEO/alaya.git alaya_v3
```

#### Step 3: 验证结构

确保以下目录存在：

```
alaya_v3/
├── SKILL.md              # 主技能 (应该存在)
├── skills/               # 新增：子技能目录
│   ├── alaya-retrieval/
│   ├── alaya-memory/
│   ├── alaya-persona/
│   ├── alaya-import/
│   └── alaya-maintenance/
├── scripts/              # 保持不变
├── manas/                # 保持不变
└── templates/            # 保持不变
```

#### Step 4: 测试功能

```
"alaya init"              # 初始化
"健康检查"                # 验证数据完整性
"显示角色"                # 验证角色系统
```

## 数据兼容性

### 完全兼容

以下数据格式 v2.x 和 v3.0 完全兼容：

- **wiki/ 目录**：知识卡片格式不变
- **alaya/config.json**：配置格式不变
- **alaya/manas/**：角色文件格式不变
- **alaya/memory/**：记忆文件格式不变
- **raw/ 目录**：原始文件存储不变

### 新增字段

v3.0 可能添加新的可选字段，但不会破坏现有数据：

```json
// config.json 新增字段 (可选)
{
  "import": {
    "version": "1.0.0",
    "default_category": "uncategorized"
  }
}
```

## 功能映射表

| v2.x 功能                | v3.0 位置                | 变更  |
| :----------------------- | :----------------------- | :---- |
| 知识检索 (Rule A)        | alaya-retrieval          | 移动  |
| RAI 锚点 (Rule B)        | alaya-retrieval          | 移动  |
| 记忆系统                | alaya-memory             | 移动  |
| BI 观察者 (Rule G)       | alaya-memory             | 移动  |
| 会话边界协议            | alaya-memory             | 移动  |
| 熏习系统 (Rule C)        | alaya-maintenance        | 移动  |
| 多角色协议 (Rule E)      | alaya-persona            | 移动  |
| 群组讨论 (Rule F)        | alaya-persona            | 移动  |
| 两印法 (Rule D)          | alaya-persona            | 移动  |
| 论文导入                | alaya-import             | 移动  |
| 批量导入                | alaya-import             | 移动  |
| 健康检查                | alaya-maintenance        | 移动  |
| 修复链接                | alaya-maintenance        | 移动  |
| 初始化检测              | 主技能                   | 保留  |
| 命令路由                | 主技能                   | 新增  |
| 版本管理                | 主技能                   | 新增  |

## 常见问题

### Q: 迁移后会丢失数据吗？

**A**: 不会。v3.0 完全向后兼容，所有知识卡片、角色、记忆都会保留。

### Q: 必须迁移吗？

**A**: 不必须。v2.x 继续可用，但无法获得 v3.0 的性能优化和新功能。

### Q: 迁移失败怎么办？

**A**:
1. 恢复备份：`cp -r {your_kb}.backup {your_kb}`
2. 检查错误信息
3. 尝试手动迁移
4. 报告问题：https://github.com/DL-LEO/alaya/issues

### Q: 子技能可以单独更新吗？

**A**: 可以。每个子技能有独立版本号，可以单独更新而不影响其他部分。

### Q: 如何回退到 v2.x？

**A**:
```bash
# 恢复备份
cp -r {your_kb}.backup {your_kb}

# 切换到 v2.x 分支
git checkout v2.1
```

## 性能对比

### Context 占用

| 场景         | v2.x    | v3.0    | 减少   |
| :----------- | :------ | :------ | :----- |
| 初始会话     | ~40KB   | ~8KB    | 80%    |
| 用户提问     | ~40KB   | ~15KB   | 62%    |
| 创建角色     | ~40KB   | ~18KB   | 55%    |
| 批量导入     | ~40KB   | ~25KB   | 37%    |
| 多角色讨论   | ~40KB   | ~30KB   | 25%    |

### 响应时间

| 操作         | v2.x    | v3.0    | 改善   |
| :----------- | :------ | :------ | :----- |
| 初始化       | 2-3s    | 1-2s    | 33%    |
| 知识检索     | 1-2s    | 0.5-1s  | 50%    |
| 角色切换     | 1s      | 0.5s    | 50%    |
| 批量导入     | 取决文件 | 取决文件 | 相同   |

## 新功能

### 子技能管理

```bash
# 查看已加载子技能
"list loaded skills"

# 手动加载子技能
"加载识海检索技能"

# 检查子技能版本
"check subskill versions"
```

### 智能路由

主技能现在自动识别用户意图并路由到正确的子技能：

```
"导入论文" → 自动加载 alaya-import
"创建角色" → 自动加载 alaya-persona
"健康检查" → 自动加载 alaya-maintenance
```

### 版本兼容性检查

自动检查主技能和子技能版本兼容性，不一致时提示更新。

## 开发者影响

### 自定义扩展

如果你基于 Alaya v2.x 开发了自定义扩展：

1. **配置脚本**：无需变更，继续工作
2. **自定义角色**：无需变更，继续工作
3. **自定义模板**：无需变更，继续工作
4. **修改 SKILL.md**：需要适配新结构

### API 变更

无 API 变更。所有脚本接口保持不变：

```bash
# 所有脚本继续工作
python scripts/build_index.py
python scripts/perfume.py
python scripts/import_paper.py
# ...
```

## 支持

### 文档

- [SKILL.md](SKILL.md) - 主技能文档
- [skills/README.md](skills/README.md) - 子技能系统
- [SKILL_GUIDE.md](SKILL_GUIDE.md) - 操作指南
- [SKILL_REF.md](SKILL_REF.md) - 详细参考

### 问题反馈

- GitHub Issues: https://github.com/DL-LEO/alaya/issues
- Gitee Issues: https://gitee.com/DL-LEO-gitee/alaya/issues

### 社区

- Discussions: https://github.com/DL-LEO/alaya/discussions
- Wiki: https://github.com/DL-LEO/alaya/wiki

## 检查清单

迁移前：

- [ ] 备份知识库数据
- [ ] 记录当前版本号
- [ ] 检查自定义修改

迁移后：

- [ ] 验证所有知识卡片存在
- [ ] 验证所有角色正常工作
- [ ] 验证记忆数据完整
- [ ] 运行健康检查
- [ ] 测试核心功能 (提问、导入、维护)

## 下一步

迁移完成后，你可以：

1. 探索新的子技能架构
2. 享受更快的响应速度
3. 创建自定义子技能
4. 参与社区贡献

欢迎来到 Alaya v3.0！