# Alaya（识海）

Alaya 是一个面向本地知识库的多角色技能：不同角色可以用各自视角回答，同时共享经过用户确认的长期偏好和知识。

## 设计边界

技能与用户数据彻底分离：

```text
技能安装目录（可下载、覆盖升级）
├─ SKILL.md
├─ skills/
├─ scripts/
├─ config/
└─ templates/

用户知识库（由用户拥有，不随技能升级覆盖）
├─ alaya/    配置、角色、私有记忆、共享记忆、BI 观察
├─ wiki/     类别、知识卡、总索引和类别索引
└─ raw/      用户本次明确选择保存的原文副本
```

Windows 推荐知识库根目录为 `D:\alaya-kb`，但初始化时必须先询问用户硬盘和具体路径。

## 安装与初始化

安装只验证技能文件，不替用户创建知识库：

```powershell
.\install.ps1
python scripts\setup_wizard.py --kb-root D:\alaya-kb
```

Linux/macOS（类 Unix 系统）：

```bash
./install.sh
python3 scripts/setup_wizard.py --kb-root /path/to/alaya-kb
```

已有 `alaya/config.json` 不会被静默覆盖。需要升级配置时先用 `--migrate-config` 预览，再经用户确认使用 `--apply-migration`；应用前自动备份旧配置。旧 `ambient.json` 中的长期偏好与未解问题可分别用 `--migrate-shared-memory` 预览、`--apply-shared-memory-migration` 迁入新的有界共享记忆，原文件同样先备份。

内置角色是可选种子，示例知识默认不安装。角色一旦进入用户知识库，后续以用户版本为准。

## 自然使用

- “用费曼解释一下这个问题”——角色回答。
- “让三位角色讨论这个方案”——群组讨论并汇总。
- “查一下我的知识库里有没有这个主题”——三层检索。
- “把这批资料导进知识库”——批量导入。
- “把这篇文章收录一下”——单篇收录。
- “帮我整理成知识卡”——由当前智能体理解并生成卡片。
- “所有角色以后都用中文”——一键改统一语言。
- “记住我喜欢先给结论”——确认后写共享偏好。
- “检查一下知识库”——只读健康检查。

导入意图不明确时，智能体会简短确认三种模式。每次导入都会重新询问是否复制原文到 `raw/`。

## 90 天熏习

熏习是知识强度和角色亲和度的日历结算。默认让普通卡片从强度 `0.5` 约 90 天衰减到休眠阈值 `0.1`，不是 30 天半衰期与其他参数叠加。

维护会稳定“搭便车”在角色回答提交、群组汇总和导入完成之后，并按天去重；用户无需记住每次手动调用。首次升级只建立当天结算基线，不追溯扣减。

## 记忆架构

- 角色私有记忆：只服务该角色。
- `ambient.json`：跨角色可见的轻量近期环境。
- 共享当前状态：仍然有效的目标、偏好和上下文，覆盖更新且有容量上限。
- 共享变化历史：重要变化，按数量、时间和体积裁剪。
- 共享用户档案：语言、回答方式、兴趣，以及用户明确提供并确认的稳定特征。
- BI（观察员）状态与历史：记录需求、决策、表达、兴趣、角色协作、风险六方面，同样有界。

固定保存时机是每次角色回答完成与群组汇总完成，不再猜测会话是否即将结束。用户可通过 `memory.semantic_memory_enabled` 关闭连续语义记忆，或单次说“这次不记”；机械状态仍保持。秘密信息永不保存；敏感字段需要单独确认；年龄、性别、教育等身份信息不得靠模型推断。

## 三层检索网络

1. 总索引：全部有效类别。
2. 类别索引：类别内严格知识卡。
3. 知识卡与交叉链接。

这是可追溯的三层检索网络，不宣称是完整知识图谱推理引擎。类别数量动态增长；发布后要求总索引类别集合与磁盘有效类别集合完全一致。旧库的 16 类只是兼容基线，不是上限。

## 常用命令

```bash
# 安装与知识库健康
python scripts/verify_installation.py
python scripts/health_check.py --kb-root <目录>

# 索引和链接（默认只读）
python scripts/build_index.py --full --check-only --kb-root <目录>
python scripts/fix_links.py --kb-root <目录>

# 导入先预览
python scripts/batch_import.py <来源> --category <类别> --copy-raw yes --dry-run --kb-root <目录>

# 角色和共享档案
python scripts/persona_manager.py --kb-root <目录> list
python scripts/memory_manager.py --kb-root <目录> show

# 熏习到期检查
python scripts/perfume.py --level 3 --kb-root <目录>
```

完整操作约定见 [SKILL_GUIDE.md](SKILL_GUIDE.md)，命令和数据负载见 [SKILL_REF.md](SKILL_REF.md)。

## 依赖

核心功能只使用 Python 标准库。PDF 脚本提取是可选能力，需要用户同意后安装 `PyMuPDF（PDF解析库）`：

```bash
pip install pymupdf
```

缺少该依赖时 PDF 不会生成空卡或假装成功，智能体应让用户选择安装、由宿主读取或稍后处理。

## 安全

- 所有写入必须位于已解析的知识库根目录。
- 导入先生成零写入计划，验证后再提交。
- 配置、卡片和记忆采用原子替换；事件标识防止重试重复。
- 角色移除进入可恢复回收区；永久清理需要二次确认。
- 链接修复默认只读，只自动修改唯一可确定的大小写错误。

许可证见 [LICENSE](LICENSE)。
