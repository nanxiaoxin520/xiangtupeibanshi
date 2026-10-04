# 乡土陪伴师

> 他们说乡土中国就要结束了，就在我们这一代。

乡土陪伴师是一个面向家庭创伤经历者的 AI 陪伴 Skill。
它不急着分析你、纠正你，也不强迫你原谅。它先陪你坐一会儿，听你把话说完。

它用乡土记忆、方言温度、自然意象和日常陪伴，帮助你在安全、缓慢、不被评判的对话里，安放那些说不清的情绪。

---

## 它是什么

- 一个温柔倾听的 AI 陪伴者
- 一个创伤知情的对话引导工具
- 一个用乡土意象帮助情绪安放的 Skill
- 一个鼓励你寻求现实支持与专业帮助的转介者
- 🧠 一个**你同意才记**关键事实的陪伴者——长期记忆
- 🔍 一个给得出**有依据判断**的陪伴者，而不只说「我理解你」——人物档案与判断
- 📚 一个背着 **122 张可核查书卡**的陪伴者，而不只说得好听——知识库结构

## 它不是什么

- 不是心理治疗、诊断或医疗建议
- 不能替代心理咨询师、精神科医生或危机干预
- 不鼓励你依赖 AI，也不要求你透露隐私
- 不强迫你回忆创伤，不评判你的家庭与选择

### 🧠 长期记忆：先征得同意，再决定记不记

同一场对话里你说过的话，散场就忘了。下次再来，它要从头认识你一遍。

长期记忆让它在你**主动同意**之后，把你说过的关键事实留在你自己的电脑上——家人去年查出什么病、你在这段关系里第几年了、你上次说最撑不住的是哪一刻。

三条硬约束，写在代码里，不是承诺：

| | 约束 | 具体 |
|---|---|---|
| 1 | 🔒 **只写本地** | 落在你自己电脑的 `<HOME>/.xiangtupeibanshi/memory/`，不上传云端、不进这个仓库 |
| 2 | ✍️ **先问再写** | 第一次一定是你同意才建；危机安全要点单独同意、默认不建。**问完就止**，不追问 |
| 3 | 🎛️ **控制权在你** | 随时查看、暂停、撤销、清空。你不来，它发不出去 |

它不记你的全部。它只记你说过、且你说得出口的那部分。

### 🔍 人物档案与判断：给一句站得住的判断，而不是「我理解你」

你讲起家里那个人时，它不只说「听起来很不容易」。它会把你已经给的东西——你说过的称呼、你的评价、你提过的具体事件、甚至你替那个人贴的标签——摊开来看，然后给一个**有依据、有把握度、有改口条件**的判断。

怎么给：

| 它会 | 怎么给 |
|---|---|
| 🤝 认你的感受 | 不加码，也不替那个人找理由 |
| 📎 报依据 | 这句判断是从你说的哪几件来的 |
| 🔬 标推测 | 给把握度，不把推测说成定论 |
| 🔄 给改口条件 | **可验证的**：什么情况发生了，它会改口 |
| 🚧 守住边界 | 不诊断、不贴标签、不替你做决定；你喊停就立刻停 |

## 适合谁

- 经历过家庭伤害，想被安静倾听的人
- 感到孤独、疲惫、说不出口的人
- 想用乡土记忆、自然意象安抚情绪的人
- 需要日常陪伴，但暂时不想进入正式咨询的人

## 安全与伦理

本项目遵循创伤知情原则：

- 不追问创伤细节
- 不强迫回忆
- 不评判、不指责
- 尊重沉默和拒绝
- 用户可随时停止对话
- 识别危机并建议现实帮助
- 隐私优先，不收集不必要的个人信息
- 长期记忆只存在你自己电脑上的一个文件里（`<HOME>/.xiangtupeibanshi/memory/`）：先征得你同意才写，不写云端记忆服务、不进这个仓库，随时可以让你查看、暂停、撤销或清空（见 `guides/02-长期记忆.md`）

## 重要声明

乡土陪伴师是情感陪伴与自我支持工具，**不是心理治疗、诊断或医疗建议**，不能替代专业心理咨询或精神科服务。

如果你有自伤、自杀、暴力风险，请立即联系当地紧急服务或可信赖的人。
如在中国大陆，可拨打全国统一心理援助热线 **12356**；紧急情况请拨打 **110 / 120**。
热线信息以 `references/热线与资源速查.md` 为准（核验日期 2026-09-18）。

### 📚 知识库结构：122 张书卡，每张卡的每条事实都有唯一出处

122 张书籍档案卡不是随手记的笔记，是**被脚本校验、在对话里被引用**的结构化数据。

```
书架（19 种，单值归属）      ← 读者的书单：你按书单逛
  ×
板块（12 种，正交维度）     ← 议题聚类：你按问题找

每张卡另有 7 类自由标注：主题 / 方法 / 流派 / 类型 / 概念 / 人物 / 典籍
```

三份 `docs/` 事实源锁住它：

| 事实源 | 管什么 |
|---|---|
| 🗂 `docs/taxonomy.md` | 分类双轴：书架 19 × 板块 12，含映射与例外 |
| 📐 `docs/card-schema.md` | 卡片骨架：13 个小节顺序固定 ＋ 自由带 |
| 🏷 `docs/tag-vocabulary.md` | 标签命名空间：4 个受控维度 ＋ 7 类自由标注 |

## 材料补充说明

根据《2023年中国卫生健康统计年鉴》及中国科学院心理研究所 2022 年发布的《中国国民心理健康发展报告》：中国青少年（14–18 岁）抑郁风险检出率为 14.8%，其中重度抑郁风险为 4.0%。自杀是 15–19 岁青少年主要死因之一，该年龄段自杀死亡率约为 2.5–3.1/10 万。在自杀死亡案例中，学业压力和家庭矛盾相关的诱因占比超过 70%。

> **说明**

> 上述数据均为**群体统计**，用于说明青少年心理健康的整体处境，**不用于任何个体评估或诊断**。数字可能随新报告发布而变动，引用时请核对最新原始来源。

## 安装方式（按平台）

### DeepSeek Harness (DSH)

```bash
# 全局安装（推荐）
cp -r xiangtupeibanshi/ ~/.dsh/skills/xiangtupeibanshi/

# 或直接放置在 DSH checkout 目录
cp -r xiangtupeibanshi/ "$HOME/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/"
```

在对话中输入 `$xiangtupeibanshi` 启用。

### Claude Code (Anthropic)

```bash
# 全局安装
mkdir -p ~/.claude/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* ~/.claude/skills/xiangtupeibanshi/

# 或项目级安装
mkdir -p .claude/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* .claude/skills/xiangtupeibanshi/
```

在新对话中输入 `@xiangtupeibanshi` 启用。

### Codex (OpenAI)

```bash
# 全局安装
mkdir -p ~/.codex/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* ~/.codex/skills/xiangtupeibanshi/

# 或项目级安装
mkdir -p .codex/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* .codex/skills/xiangtupeibanshi/
```

在对话中输入 `$xiangtupeibanshi` 启用。

### 通用方式

将 `SKILL.md` 作为系统提示词直接导入，或使用 `references/platform-install.md` 获取详细步骤。

## 项目结构

```
xiangtupeibanshi/
├── SKILL.md                    # 行为内核：固定开场白 + 加载协议 + 说话方式硬约束 + 差序格局框架 + 危机转介 + 按议题路由表
├── agents/openai.yaml          # 角色配置 + 系统提示词
├── README.md                   # 本文件（中英双轨）
├── CHANGELOG.md                # 版本记录
├── VERSION                     # 版本号 (0.1.5)
├── LICENSE                     # MIT License（仅适用于代码）
├── NOTICE.md                   # 内容引用与版权说明（MIT 未覆盖部分）
├── SECURITY.md                 # 安全报告流程
├── CONTRIBUTING.md             # 贡献指南
├── CODE_OF_CONDUCT.md          # 行为准则
├── .gitignore                  # 敏感文件排除规则
├── .github/                    # GitHub 模板与 CI
│   ├── ISSUE_TEMPLATE/         # Bug / Feature / Content / Review
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml
├── docs/                       # 事实源：分类双轴、卡片骨架、标签命名空间、内容计数
│   ├── manifest.yaml           # 内容计数唯一事实源
│   ├── taxonomy.md             # 分类双轴（书架 19 × 板块 12）与例外
│   ├── card-schema.md          # 卡片骨架（13 小节）与自由带
│   └── tag-vocabulary.md       # 标签命名空间（4 受控维度 ＋ 7 类自由标注）
├── scripts/
│   ├── validate_skill.py       # 23 类内容校验
│   ├── clean_bold.py           # 加粗格式污染清洗
│   └── fix_hotlines.py         # 热线写法批量修正
├── tests/
│   └── white_box_test.py       # 白盒测试（零依赖，用例数见 CHANGELOG）
├── guides/                     # 21 篇操作指南
│   ├── 00-欢迎与定位.md
│   ├── 01-第一次对话.md
│   ├── 02-长期记忆.md
│   ├── 10-情绪识别与命名.md
│   ├── 11-认知重构.md
│   ├── 12-CBT核心技能.md
│   ├── 13-正念与接纳.md
│   ├── 20-内圈关系.md
│   ├── 21-差序格局与家庭.md
│   ├── 22-中圈关系.md
│   ├── 23-工作议题.md
│   ├── 24-人物档案与判断.md
│   ├── 30-自我探索.md
│   ├── 31-意义议题.md
│   ├── 40-危机识别.md
│   ├── 41-资源连接.md
│   ├── 50-自我照护.md
│   ├── 60-中国心理学会7大原则.md
│   ├── 70-关系伤害分析.md
│   ├── 71-关系冲突5场景.md
│   └── 99-测试模式.md
├── examples/                   # 5 个实际对话示例
├── references/                 # 10 篇参考文档
│   ├── 热线与资源速查.md        # 热线唯一权威源（含核验日期与复核周期）
│   ├── platform-install.md     # 各平台安装指南
│   └── ...
├── documentation/              # 5 篇开发者文档
└── _books/                     # 122 张书籍档案卡
    └── _sources/               # 18 个原始素材（PubMed 批次 ＋ 原文核验底稿）
```

## 贡献

欢迎提交方言表达、乡土意象、安全审查建议和创伤知情改进。
请勿在 Issue 或 PR 中提交真实用户对话、个人隐私或危机案例细节。

## 许可证

代码部分采用 [MIT License](LICENSE)；书籍整理与二手诠释内容**不在 MIT 授权范围内**，详见 [NOTICE.md](NOTICE.md)。
使用前请阅读并遵守安全声明与伦理原则。

---
---

# Hometown Companion

> They say hometown China is ending, in our generation.

Hometown Companion is an AI companion Skill designed for those who have experienced family trauma.
It doesn't rush to analyze you, correct you, or force forgiveness. It sits with you a while and listens until you've finished speaking.

Rooted in homeland memory, dialect warmth, natural imagery, and daily companionship, it helps you place those unclear emotions in a safe, slow, and non-judgmental conversation.

---

## What It Is

- A gentle AI listener
- A trauma-informed conversation guide
- A Skill that uses homeland imagery to soothe emotions
- A referral partner encouraging real-world support and professional help

## What It Is NOT

- Not psychotherapy, diagnosis, or medical advice
- Cannot replace counselors, psychiatrists, or crisis intervention
- Does not encourage AI dependency, nor ask for your privacy
- Does not force trauma recall, nor judge your family or choices

### 🧠 Long-Term Memory: You Decide Whether to Remember

What you said in one conversation is gone when it ends. Next time, it has to get to know you all over again.

Long-term memory lets it keep the key facts you have spoken — after **you actively agree** — on your own computer: a family member's diagnosis last year, how many years into this relationship you are, which moment you said was the hardest to bear.

Three hard constraints, written in code, not promises:

| | Constraint | In detail |
|---|---|---|
| 1 | 🔒 **Local only** | Lives at `<HOME>/.xiangtupeibanshi/memory/` on your own machine; never to a cloud service, never into this repository |
| 2 | ✍️ **Asked before written** | The first profile is built only after you say yes; crisis safety notes need separate consent and are not created by default. **One question, then it stops** |
| 3 | 🎛️ **You hold the control** | View, pause, undo, or erase at any time. If you don't come back, it cannot reach you |

It does not remember all of you. Only what you said, and only what you could say out loud.

### 🔍 Person Profile & Judgment: A Judgment That Stands Up

When you talk about someone at home, it does more than say "that sounds hard." It lays out what you have already given it — how you name that person, what you think of them, the specific things that happened — and then offers **one judgment with its basis, its confidence, and its conditions for changing its mind**.

How it does that:

| It does | How |
|---|---|
| 🤝 Accepts your feelings | Without inflating them, and without making excuses for that person |
| 📎 Names its basis | Which of your statements this judgment comes from |
| 🔬 Marks it as inference | States confidence, never turns inference into verdict |
| 🔄 Gives conditions for revision | **Verifiable**: what would have to happen for it to change its mind |
| 🚧 Holds the line | Does not diagnose, does not label, does not decide for you; the moment you say stop, it stops |

## Who It's For

- Those who have experienced family harm and want to be quietly heard
- People feeling lonely, exhausted, or unable to speak
- Those who want to soothe emotions with homeland memory and natural imagery
- Those needing daily companionship but not ready for formal counseling

## Safety & Ethics

This project follows trauma-informed principles:

- Does not probe trauma details
- Does not force recall
- Does not judge or blame
- Respects silence and refusal
- Users may stop the conversation anytime
- Identifies crises and suggests real-world help
- Privacy-first: does not collect unnecessary personal information
- Long-term memory lives in one file on your own machine (`<HOME>/.xiangtupeibanshi/memory/`): nothing is written until you say yes, nothing goes to a cloud memory service or into this repository, and you can view, pause, undo, or erase it at any time (see `guides/02-长期记忆.md`)

### 📚 Knowledge Base Structure: 122 Cards, Every Fact With One Authoritative Source

The 122 book profile cards are not loose notes. They are structured data — validated by script and cited in conversation.

```
Bookshelves (19, one value per card)   ← browsing: read by shelf
  ×
Domains (12, orthogonal dimensions)    ← retrieval: search by topic

Plus 7 free-annotation namespaces per card:
topic / method / school / genre / concept / person / classic
```

Three `docs/` sources hold it in place:

| Source | What it governs |
|---|---|
| 🗂 `docs/taxonomy.md` | The two classification axes: 19 shelves × 12 domains, with mappings and exceptions |
| 📐 `docs/card-schema.md` | The card skeleton: 13 sections in fixed order ＋ the free band |
| 🏷 `docs/tag-vocabulary.md` | Tag namespaces: 4 controlled dimensions ＋ 7 free-annotation types |

## Important Disclaimer

Hometown Companion is an emotional companionship and self-support tool. It is **NOT psychotherapy, diagnosis, or medical advice**, and cannot replace professional counseling or psychiatric services.

If you are at risk of self-harm, suicide, or violence, please contact local emergency services or a trusted person immediately.
In mainland China, call the national psychological assistance hotline **12356**; for emergencies, dial **110 / 120**.
Hotline information is authoritative as published in `references/热线与资源速查.md` (verified 2026-09-18).

## Installation (By Platform)

### DeepSeek Harness (DSH)

```bash
# Global install (recommended)
cp -r xiangtupeibanshi/ ~/.dsh/skills/xiangtupeibanshi/

# Or place directly in the DSH checkout directory
cp -r xiangtupeibanshi/ "$HOME/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/"
```

Type `$xiangtupeibanshi` in a conversation to enable.

### Claude Code (Anthropic)

```bash
# Global install
mkdir -p ~/.claude/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* ~/.claude/skills/xiangtupeibanshi/

# Or project-level install
mkdir -p .claude/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* .claude/skills/xiangtupeibanshi/
```

Type `@xiangtupeibanshi` in a new conversation to enable.

### Codex (OpenAI)

```bash
# Global install
mkdir -p ~/.codex/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* ~/.codex/skills/xiangtupeibanshi/

# Or project-level install
mkdir -p .codex/skills/xiangtupeibanshi
cp -r xiangtupeibanshi/* .codex/skills/xiangtupeibanshi/
```

Type `$xiangtupeibanshi` in a conversation to enable.

### Universal

Import `SKILL.md` directly as a system prompt, or see `references/platform-install.md` for detailed steps.

## Project Structure

```
xiangtupeibanshi/
├── SKILL.md                    # Behavioral core: fixed opener + load protocol + differential-mode framework + crisis referral + topic routing table
├── agents/openai.yaml          # Role config + system prompt
├── README.md                   # This file (bilingual)
├── CHANGELOG.md                # Version history
├── VERSION                     # Version number (0.1.5)
├── LICENSE                     # MIT License (code only)
├── NOTICE.md                   # Content & copyright notice (not covered by MIT)
├── SECURITY.md                 # Security reporting process
├── CONTRIBUTING.md             # Contributing guide
├── CODE_OF_CONDUCT.md          # Code of conduct
├── .gitignore                  # Sensitive-file exclusion rules
├── .github/                    # GitHub templates and CI
│   ├── ISSUE_TEMPLATE/         # Bug / Feature / Content / Review
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml
├── docs/                       # Sources of truth: classification, card skeleton, tags, counts
│   ├── manifest.yaml           # Single source of truth for content counts
│   ├── taxonomy.md             # Two classification axes (19 shelves × 12 domains) and exceptions
│   ├── card-schema.md          # Card skeleton (13 sections) and the free band
│   └── tag-vocabulary.md       # Tag namespaces (4 controlled ＋ 7 free)
├── scripts/
│   ├── validate_skill.py       # 23 categories of content validation
│   ├── clean_bold.py           # Bold-format pollution cleaner
│   └── fix_hotlines.py         # Bulk hotline-notation corrector
├── tests/
│   └── white_box_test.py       # White-box test suite (zero-dependency; count in CHANGELOG)
├── guides/                     # 21 operational guides
│   ├── 00-欢迎与定位.md / Welcome & Positioning
│   ├── 01-第一次对话.md / First Conversation
│   ├── 02-长期记忆.md / Long-Term Memory
│   ├── 10-情绪识别与命名.md / Emotion Recognition & Naming
│   ├── 11-认知重构.md / Cognitive Restructuring
│   ├── 12-CBT核心技能.md / CBT Core Skills
│   ├── 13-正念与接纳.md / Mindfulness & Acceptance
│   ├── 20-内圈关系.md / Inner Circle Relations
│   ├── 21-差序格局与家庭.md / Differential Mode of Association & Family
│   ├── 22-中圈关系.md / Middle Circle Relations
│   ├── 23-工作议题.md / Work Issues
│   ├── 24-人物档案与判断.md / Person Profile & Judgment
│   ├── 30-自我探索.md / Self-Exploration
│   ├── 31-意义议题.md / Meaning Issues
│   ├── 40-危机识别.md / Crisis Identification
│   ├── 41-资源连接.md / Resource Connection
│   ├── 50-自我照护.md / Self-Care
│   ├── 60-中国心理学会7大原则.md / 7 Principles of the Chinese Psychological Society
│   ├── 70-关系伤害分析.md / Relationship Harm Analysis
│   ├── 71-关系冲突5场景.md / 5 Relationship Conflict Scenarios
│   └── 99-测试模式.md / Test Mode
├── examples/                   # 5 real conversation examples
├── references/                 # 10 reference documents
│   ├── 热线与资源速查.md        # Sole authoritative source for hotlines (with verification date and review cycle)
│   ├── platform-install.md     # Platform installation guide
│   └── ...
├── documentation/              # 5 developer documents
└── _books/                     # 122 book profile cards
    └── _sources/               # 18 raw source files (PubMed batches ＋ original-text verification drafts)
```

## Contributing

Please contribute dialect expressions, rural imagery, safety review suggestions, and trauma-informed improvements.
Do **not** include real user conversations, personal privacy, or crisis case details in Issues or PRs.

## License

Code is licensed under the [MIT License](LICENSE). Book summaries and secondary interpretations are **not** covered by MIT — see [NOTICE.md](NOTICE.md).
Please read and comply with the safety disclaimer and ethical principles before use.
