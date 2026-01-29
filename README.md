# Skill Lab

**中文 | [English](README_EN.md)**

**一键构建 Claude Code Skills 开发环境的插件**

---

## 为什么需要 Skill Lab？

我们正在进入 **Skill 时代**。

Claude Code 的 Skills 让 AI 拥有了可扩展的能力——你可以从网上下载别人写的 skill，也可以自己编写专属的 skill。但问题来了：

- 下载的 skill 安全吗？直接放进 `~/.claude/skills` 会不会搞坏你的环境？
- 自己写的 skill 还在调试，怎么避免影响正在进行的项目？
- 每次想试验新 skill，都要手动备份、恢复，太麻烦了

**Skill Lab 就是为了解决这些问题而生的。**

它为你提供一个**安全的沙盒环境**，让你可以放心地：
- 试验任何来源的 skill（网上下载的、自己写的）
- 不用担心破坏现有的稳定环境
- 一键同步到生产环境

---

## 核心理念：蓝绿部署

```
你的项目
    │
    │ 需要某个 skill？
    ▼
┌─────────────────────────────────────────────────────┐
│  EXPERIMENTAL (实验版)                               │
│  ~/Desktop/skills-experimental                      │
│                                                     │
│  - 放心试验任何新 skill                              │
│  - 独立的 Python 虚拟环境                            │
│  - 出问题？删掉重来，不影响任何东西                    │
└─────────────────────────────────────────────────────┘
                    │
                    │ 测试通过？一键同步
                    ▼
┌─────────────────────────────────────────────────────┐
│  STABLE (稳定版)                                     │
│  ~/Desktop/skills-stable                            │
│                                                     │
│  - 自动链接到 ~/.claude/skills                       │
│  - 只有验证过的 skill 才能进入                        │
│  - 全局可用，所有项目共享                             │
└─────────────────────────────────────────────────────┘
```

**简单说：先在实验室里折腾，确认没问题再上线。**

---

## 一键开箱

### 安装

> **注意**：以下命令需要在 Claude Code 中执行。请先启动 Claude Code（在终端中运行 `claude`），然后在对话框中输入这些命令。

```bash
# 1. 添加插件源
/plugin marketplace add ltianyi992/skill-lab

# 2. 安装插件
/plugin install skill-lab@ltianyi992-skill-lab

# 3. 初始化环境（只需运行一次）
/skill-lab:setup
```

就这三步，你的 skill 开发环境就搭建好了。

### 初始化后你会得到

| 目录 | 作用 |
|-----|------|
| `~/Desktop/skills-stable` | 稳定版，自动链接到全局 |
| `~/Desktop/skills-experimental` | 实验版，放心折腾 |
| 两个目录各有独立的 `.venv` | 依赖隔离，互不影响 |

---

## 使用场景

### 场景 1：试用网上下载的 skill

```
1. 把下载的 skill 放入 ~/Desktop/skills-experimental/
2. 在你的项目中运行 /skill-lab:link
3. 测试这个 skill 是否好用、是否安全
4. 满意？运行 /skill-lab:sync 同步到稳定版
5. 不满意？直接删除，不影响任何东西
```

### 场景 2：开发自己的 skill

```
1. 在 ~/Desktop/skills-experimental/ 中创建你的 skill
2. 安装依赖：pip install xxx && pip freeze > requirements.txt
3. 链接到项目测试：/skill-lab:link
4. 反复迭代，直到满意
5. 同步到稳定版：/skill-lab:sync（依赖会自动安装到稳定版）
```

### 场景 3：智能匹配

当你打开一个项目时，Skill Lab 会自动检测：

```
"我发现你的项目有 PDF 文件，而你的实验环境有一个 'pdf' skill。
要不要链接它来帮助处理 PDF？"
```

**先问再做，不会擅自行动。**

---

## 命令一览

| 命令 | 作用 |
|------|------|
| `/skill-lab:setup` | 初始化环境（只需一次） |
| `/skill-lab:status` | 查看环境状态 |
| `/skill-lab:sync` | 同步实验版到稳定版（含依赖） |
| `/skill-lab:link` | 链接当前项目到实验版 |
| `/skill-lab:unlink` | 断开链接 |
| `/skill-lab:skill-matcher` | 检测项目与 skill 的匹配度 |

---

## 技术架构

```
~/.claude/skills ◄─── Junction/Symlink
        │
        ▼
skills-stable/                    skills-experimental/
├── .venv/ (生产依赖)              ├── .venv/ (开发依赖)
├── requirements.txt              ├── requirements.txt
├── pdf/                          ├── pdf/
│   └── SKILL.md                  │   └── SKILL.md
└── [其他稳定 skills]              └── [实验中的 skills]
        │                                   │
        │◄────── git merge ◄───────────────┘
        │◄────── pip install -r requirements.txt
```

两个目录通过 **Git Worktree** 共享代码历史，但物理隔离。同步时：
1. 代码通过 `git merge` 合并
2. 依赖通过 `pip install` 自动安装到稳定版

---

## 为什么这很重要？

**Skill 时代的三个趋势：**

1. **Skills 会越来越多** —— 社区会产出大量 skills，你需要一个安全的方式来试用它们
2. **Skills 会越来越复杂** —— 带依赖、带脚本的 skills 需要隔离的运行环境
3. **Skills 会成为标配** —— 就像 VS Code 插件一样，管理 skills 需要专业工具

**Skill Lab 就是这个专业工具。**

它不只是一个"开发环境"，更是一种**工作方式的升级**：

- 从"直接改全局目录"升级为"先实验再上线"
- 从"手动管理依赖"升级为"自动同步依赖"
- 从"出问题再回滚"升级为"隔离测试零风险"

---

## 环境要求

- Claude Code v1.0.33+
- Git
- Python 3.8+

## 项目结构

```
skill-lab/
├── skills/                 # 插件提供的命令
│   ├── setup/             # 初始化环境
│   ├── status/            # 查看状态
│   ├── sync/              # 同步到稳定版
│   ├── link/              # 链接项目
│   ├── unlink/            # 断开链接
│   └── skill-matcher/     # 智能匹配
├── hooks/                  # 自动触发的钩子
├── scripts/               # 核心脚本
│   ├── bootstrap.py       # 环境搭建
│   └── handler.py         # 命令处理
└── references/
    └── architecture.md    # 详细架构文档
```

## License

MIT

---

> **Skill Lab —— 让每一次 skill 实验都安全可控。**
