# 乡土陪伴师 · Hometown Companion

> They say hometown China is ending, in our generation.

Hometown Companion is an AI companion Skill designed for those who have experienced family trauma.  
It doesn't rush to analyze you, correct you, or force forgiveness. It sits with you a while and listens until you've finished speaking.

Rooted in homeland memory, dialect warmth, natural imagery, and daily companionship, it helps you place those unclear emotions in a safe, slow, and non-judgmental conversation.

---

## 中文简介

乡土陪伴师是一个面向家庭创伤经历者的 AI 陪伴 Skill。  
它不急着分析你、纠正你，也不强迫你原谅。它先陪你坐一会儿，听你把话说完。

它用乡土记忆、方言温度、自然意象和日常陪伴，帮助你在安全、缓慢、不被评判的对话里，安放那些说不清的情绪。

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
Hotline information is subject to the latest official local sources.

## 安装方式 / Installation (By Platform)

### DeepSeek Harness (DSH)

```bash
# 全局安装（推荐）
cp -r xiangtupeibanshi/ ~/.dsh/skills/xiangtupeibanshi/

# 或直接放置在 DSH checkout 目录
cp -r xiangtupeibanshi/ "C:/Users/wu'xin/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/"
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

### 通用方式 / Universal

将 `SKILL.md` 作为系统提示词直接导入，或使用 `references/platform-install.md` 获取详细步骤。

## 项目结构 / Project Structure

```
xiangtupeibanshi/
├── SKILL.md                    # 核心框架 + 安全声明
├── agents/openai.yaml          # 角色配置 + 系统提示词
├── README.md                   # 本文件（中英双语）
├── CHANGELOG.md                # 版本记录
├── VERSION                     # 版本号 (0.1.0)
├── LICENSE                     # MIT License + 内容引用附录
├── SECURITY.md                 # 安全报告流程
├── CONTRIBUTING.md             # 贡献指南
├── CODE_OF_CONDUCT.md          # 行为准则
├── .gitignore                  # 敏感文件排除规则
├── .github/                    # GitHub 模板
│   ├── ISSUE_TEMPLATE/         # Bug / Feature / Content / Review
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml  # CI 工作流
├── scripts/                    # 验证脚本
│   └── validate_skill.py
├── guides/                     # 19 篇操作指南
│   ├── 00-欢迎与定位.md / Welcome & Positioning
│   ├── 01-第一次对话.md / First Conversation
│   ├── 10-情绪识别与命名.md / Emotion Recognition
│   ├── 11-认知重构.md / Cognitive Restructuring
│   ├── 12-CBT核心技能.md / CBT Core Skills
│   ├── 13-正念与接纳.md / Mindfulness & Acceptance
│   ├── 20-内圈关系.md / Inner Circle Relations
│   ├── 21-差序格局与家庭.md /差序格局与家庭
│   ├── 22-中圈关系.md / Middle Circle Relations
│   ├── 23-工作议题.md / Work Issues
│   ├── 30-自我探索.md / Self-Exploration
│   ├── 31-意义议题.md / Meaning Issues
│   ├── 40-危机识别.md / Crisis Identification
│   ├── 41-资源连接.md / Resource Connection
│   ├── 50-自我照护.md / Self-Care
│   ├── 60-中国心理学会7大原则.md / 7 Principles
│   ├── 70-关系伤害分析.md / Relationship Harm Analysis
│   ├── 71-关系冲突5场景.md / 5 Conflict Scenarios
│   └── 99-测试模式.md / Test Mode
├── examples/                   # 5 个实际对话示例
├── references/                 # 参考文档
│   ├── platform-install.md     # 各平台安装指南
│   ├── README.md               # 参考文档索引
│   └── ...
├── documentation/              # 开发者文档
└── _books/                     # 书籍档案卡
```

## 贡献 / Contributing

欢迎提交方言表达、乡土意象、安全审查建议和创伤知情改进。  
请勿在 Issue 或 PR 中提交真实用户对话、个人隐私或危机案例细节。

Please contribute dialect expressions, rural imagery, safety review suggestions, and trauma-informed improvements.  
Do **not** include real user conversations, personal privacy, or crisis case details in Issues or PRs.

## 许可证 / License

MIT License.  
Please read and comply with the safety disclaimer and ethical principles before use.

