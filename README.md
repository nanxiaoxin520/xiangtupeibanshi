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

## 它不是什么

- 不是心理治疗、诊断或医疗建议
- 不能替代心理咨询师、精神科医生或危机干预
- 不鼓励你依赖 AI，也不要求你透露隐私
- 不强迫你回忆创伤，不评判你的家庭与选择

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

## 重要声明

乡土陪伴师是情感陪伴与自我支持工具，**不是心理治疗、诊断或医疗建议**，不能替代专业心理咨询或精神科服务。

如果你有自伤、自杀、暴力风险，请立即联系当地紧急服务或可信赖的人。
如在中国大陆，可拨打全国统一心理援助热线 **12356**；紧急情况请拨打 **110 / 120**。
热线信息以 `references/热线与资源速查.md` 为准（核验日期 2026-09-18）。

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
├── SKILL.md                    # 行为内核：加载协议 + 差序格局框架 + 危机转介 + 按议题路由表
├── agents/openai.yaml          # 角色配置 + 系统提示词
├── README.md                   # 本文件（中英双轨）
├── CHANGELOG.md                # 版本记录
├── VERSION                     # 版本号 (0.1.2)
├── LICENSE                     # MIT License + 内容引用附录
├── SECURITY.md                 # 安全报告流程
├── CONTRIBUTING.md             # 贡献指南
├── CODE_OF_CONDUCT.md          # 行为准则
├── .gitignore                  # 敏感文件排除规则
├── .github/                    # GitHub 模板与 CI
│   ├── ISSUE_TEMPLATE/         # Bug / Feature / Content / Review
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml
├── docs/
│   └── manifest.yaml           # 内容计数唯一事实源
├── scripts/
│   ├── validate_skill.py       # 12 类内容校验
│   ├── clean_bold.py           # 加粗格式污染清洗
│   └── fix_hotlines.py         # 热线写法批量修正
├── tests/
│   └── white_box_test.py       # 白盒测试（86 项用例）
├── guides/                     # 19 篇操作指南
│   ├── 00-欢迎与定位.md
│   ├── 01-第一次对话.md
│   ├── 10-情绪识别与命名.md
│   ├── 11-认知重构.md
│   ├── 12-CBT核心技能.md
│   ├── 13-正念与接纳.md
│   ├── 20-内圈关系.md
│   ├── 21-差序格局与家庭.md
│   ├── 22-中圈关系.md
│   ├── 23-工作议题.md
│   ├── 30-自我探索.md
│   ├── 31-意义议题.md
│   ├── 40-危机识别.md
│   ├── 41-资源连接.md
│   ├── 50-自我照护.md
│   ├── 60-中国心理学会7大原则.md
│   ├── 70-关系伤害分析.md
│   ├── 71-关系冲突5场景.md
│   └── 99-测试模式.md
├── examples/                   # 4 个实际对话示例
├── references/                 # 9 篇参考文档
│   ├── 热线与资源速查.md        # 热线唯一权威源（含核验日期与复核周期）
│   ├── platform-install.md     # 各平台安装指南
│   └── ...
├── documentation/              # 5 篇开发者文档
└── _books/                     # 50 张书籍档案卡
    └── _sources/               # 12 个原始素材（PubMed 批次）
```

## 贡献

欢迎提交方言表达、乡土意象、安全审查建议和创伤知情改进。
请勿在 Issue 或 PR 中提交真实用户对话、个人隐私或危机案例细节。

## 许可证

MIT License。
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
├── SKILL.md                    # Behavioral core: load protocol + differential-mode framework + crisis referral + topic routing table
├── agents/openai.yaml          # Role config + system prompt
├── README.md                   # This file (bilingual)
├── CHANGELOG.md                # Version history
├── VERSION                     # Version number (0.1.2)
├── LICENSE                     # MIT License + content attribution appendix
├── SECURITY.md                 # Security reporting process
├── CONTRIBUTING.md             # Contributing guide
├── CODE_OF_CONDUCT.md          # Code of conduct
├── .gitignore                  # Sensitive-file exclusion rules
├── .github/                    # GitHub templates and CI
│   ├── ISSUE_TEMPLATE/         # Bug / Feature / Content / Review
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml
├── docs/
│   └── manifest.yaml           # Single source of truth for content counts
├── scripts/
│   ├── validate_skill.py       # 12 categories of content validation
│   ├── clean_bold.py           # Bold-format pollution cleaner
│   └── fix_hotlines.py         # Bulk hotline-notation corrector
├── tests/
│   └── white_box_test.py       # White-box test suite (86 cases)
├── guides/                     # 19 operational guides
│   ├── 00-欢迎与定位.md / Welcome & Positioning
│   ├── 01-第一次对话.md / First Conversation
│   ├── 10-情绪识别与命名.md / Emotion Recognition & Naming
│   ├── 11-认知重构.md / Cognitive Restructuring
│   ├── 12-CBT核心技能.md / CBT Core Skills
│   ├── 13-正念与接纳.md / Mindfulness & Acceptance
│   ├── 20-内圈关系.md / Inner Circle Relations
│   ├── 21-差序格局与家庭.md / Differential Mode of Association & Family
│   ├── 22-中圈关系.md / Middle Circle Relations
│   ├── 23-工作议题.md / Work Issues
│   ├── 30-自我探索.md / Self-Exploration
│   ├── 31-意义议题.md / Meaning Issues
│   ├── 40-危机识别.md / Crisis Identification
│   ├── 41-资源连接.md / Resource Connection
│   ├── 50-自我照护.md / Self-Care
│   ├── 60-中国心理学会7大原则.md / 7 Principles of the Chinese Psychological Society
│   ├── 70-关系伤害分析.md / Relationship Harm Analysis
│   ├── 71-关系冲突5场景.md / 5 Relationship Conflict Scenarios
│   └── 99-测试模式.md / Test Mode
├── examples/                   # 4 real conversation examples
├── references/                 # 9 reference documents
│   ├── 热线与资源速查.md        # Sole authoritative source for hotlines (with verification date and review cycle)
│   ├── platform-install.md     # Platform installation guide
│   └── ...
├── documentation/              # 5 developer documents
└── _books/                     # 50 book profile cards
    └── _sources/               # 12 raw source files (PubMed batches)
```

## Contributing

Please contribute dialect expressions, rural imagery, safety review suggestions, and trauma-informed improvements.
Do **not** include real user conversations, personal privacy, or crisis case details in Issues or PRs.

## License

MIT License.
Please read and comply with the safety disclaimer and ethical principles before use.
