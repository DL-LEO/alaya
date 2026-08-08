# Alaya 速查

| 你可以这样说 | 实际动作 |
|---|---|
| 初始化 Alaya | 询问硬盘与目录，建立独立 `alaya/wiki/raw` |
| 所有角色都用中文 | 改全局 `language`，统一生效 |
| 用某角色回答 | 读取角色与相关知识，答后用 `turn_id` 固定提交 |
| 让几个角色讨论 | 独立观点与汇总，按 `group_id` 提交一次 |
| 把这些资料导进知识库 | 批量脚本导入，先预览 |
| 把这篇文章收录一下 | 单篇收录 |
| 帮我整理成知识卡 | 宿主智能体语义整理 |
| 记住这个偏好 | 确认后更新共享当前状态/档案 |
| 忘掉某个字段 | 删除当前值和对应变化历史 |
| 检查知识库 | 只读健康检查 |
| 修复链接 | 先报告；只修唯一确定的大小写 |
| 现在熏习 | 立即结算；平时也每日搭便车 |

导入固定追问：“这次是否把原文复制到 `raw/`？”

关键命令：

```bash
python scripts/setup_wizard.py --kb-root <目录>
python scripts/health_check.py --kb-root <目录>
python scripts/build_index.py --full --check-only --kb-root <目录>
python scripts/batch_import.py <来源> --category <类别> --copy-raw yes --dry-run --kb-root <目录>
python scripts/persona_manager.py --kb-root <目录> list
python scripts/memory_manager.py --kb-root <目录> show
python scripts/perfume.py --level 3 --kb-root <目录>
```

三个原则：技能可更新、用户库不覆盖；检查默认只读；事件提交必须幂等。
