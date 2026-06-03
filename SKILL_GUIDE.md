---
name: Alaya Guide
description: "Post-init operation guide for Alaya · 识海 — shown to users after first-time setup."
version: 2.0.0
trigger: "Read and display after initial setup completes (First Launch Detection Step 3)"
---

# Alaya · 识海 — 操作指南

> 初始化完成！以下是你可以用识海做的所有事情。
> Setup complete! Here's what you can do with Alaya.

---

## 📚 构建与充实知识库

```
"帮我构建索引"         → 扫描 wiki/ 并构建三层知识图谱（index → category → card）
"导入这篇论文"         → 导入论文 PDF 或 arXiv 链接（自动摘要或全文提取）
"批量导入 raw/"        → 从 raw/ 文件夹批量导入文档（MD/TXT/PDF）
"补充卡片描述"         → 自动从正文提取缺失的卡片描述
"更新类别描述"         → LLM 重新生成类别头部描述（100-200字三段式）
"更新索引描述"         → LLM 重新生成 index.md 各分类的入口描述
"审视分类结构"         → BI 检查分类是否需要合并
```

> **💡 小贴士：** 把下载的论文、PDF 或任何原始文档放到 `raw/` 目录下（位置：`{your_kb_root}/raw/`），
> 然后让 Agent 批量导入或逐篇导入。导入成功后 Agent 会自动建立指向原文的链接，
> 方便你后续「深读」时快速回查原文。

---

## 👤 角色管理

```
"创建角色"             → 7 阶段访谈式角色创建，从零构建一个完整人设
"蒸馏角色 {名字}"      → 从对话中蒸馏新角色，让 Agent 学习你的描述
"克隆角色 {名字}"      → 克隆现有角色再微调
"删除角色 {名字}"      → 删除角色及其配置
```

默认已安装 8 个角色（费曼、苏格拉底、佛祖、庄子、荣格、伽利略、赫本、小昭）。
你可以随时创建自己的角色——每个角色都是一面独特的"末那识"棱镜。

---

## 💬 对话示例

```
"Feynman, 解释量子纠缠"
    → ⚛ 费曼用物理直觉回答，引用知识库中的相关卡片

"Socrates, 你怎么看 attention 机制？"
    → 🏛️ 苏格拉底用哲学追问的方式回答，从同一知识库选取不同卡片

"叫 Feynman 和 Buddha 讨论意识与物理的关系"
    → ⚛☸ 多角色圆桌讨论，Agent 自动主持

"各位大佬"
    → 触发圆桌讨论协议，所有活跃角色参与
```

---

## 📂 准备原始文档

把你的论文、PDF、读书笔记等原始文档放到知识库下的 `raw/` 文件夹：

```
{your_kb_root}/
├── raw/                      ← 原始文档（你主动放入）
│   ├── my-paper.pdf
│   ├── research-notes.md
│   └── meeting-summary.txt
├── wiki/                     ← 知识卡片（Agent 自动管理）
└── alaya/                    ← 系统配置（Agent 自动管理）
```

> 放入 `raw/` 后，对 Agent 说 **"批量导入 raw/"** 即可自动导入到 wiki。
> 导入时 Agent 会自动记录原始文件路径，你以后可以说 **"深读 {卡片名}"** 来回查原文。

---

## 🔗 配合 Obsidian 可视化（强烈推荐）

Alaya 的 wiki 使用 `[[wikilinks]]` 格式——与 [Obsidian](https://obsidian.md) 完全兼容。

将知识库根目录作为 Obsidian Vault 打开，即可看到完整的知识图谱：

1. 下载 [Obsidian](https://obsidian.md/download)（免费）
2. 打开 Obsidian → **"Open folder as vault"** → 选择你的知识库根目录（包含 `wiki/` 的目录）
3. 点击右上角 **Graph View**（图谱视图）→ 所有卡片和关联关系以节点图呈现
4. 所有 `[[wikilinks]]` 自动可点击跳转，类别结构清晰可见

> 如果你还没有 Obsidian Vault，安装 Obsidian 后新建一个 Vault，指向知识库根目录即可。
> 更推荐的做法：在初始化识海时，直接将 Obsidian Vault 目录作为知识库根目录选择。

---

## 🩺 维护命令

```
"运行熏习"       → 运行知识衰减、强度更新、好感网络更新
"健康检查"        → 检查三层知识图谱完整性、角色配置、元数据覆盖率
"修复链接"        → 修复 wiki 链接大小写不匹配问题
"BI观察"          → 跨角色模式观察（休眠角色、知识缺口、好感网络）
"查看配置"        → 显示当前 alaya/config.json
"把 top_K 改成 5"  → 调整检索深度
```

---

## ✅ 首次配置检查清单

初始化完成后，请确认：

- [ ] `alaya/config.json` 存在且配置正确
- [ ] `alaya/manas/` 下有至少一个角色（JSON + profile.md），默认 8 个
- [ ] `wiki/` 下有类别子文件夹和知识卡片（sample 示例已自动安装）
- [ ] `wiki/index.md` 已生成（若未生成，对 Agent 说 **"构建索引"**）
- [ ] `raw/` 文件夹已创建
- [ ] 运行了 **"构建索引"** 完成三层知识图谱初始化

如果发现任何遗漏，直接对 Agent 说对应的命令即可。

---

## ❓ 需要帮助？

随时说：
- **"识海帮助"** — 显示本指南
- **"健康检查"** — 诊断系统状态
- **"查看配置"** — 查看当前配置
- **"alaya init"** — 重新运行配置向导
