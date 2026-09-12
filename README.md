# 乡土陪伴师 · Hometown Companion

> 他们说乡土中国就要结束了，就在我们这一代。

乡土陪伴师是一个面向家庭创伤经历者的 AI 陪伴 Skill。  
它不急着分析你、纠正你，也不强迫你原谅。它先陪你坐一会儿，听你把话说完。

它用乡土记忆、方言温度、自然意象和日常陪伴，帮助你在安全、缓慢、不被评判的对话里，安放那些说不清的情绪。

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
如在中国大陆，可拨打全国心理援助热线 **12356**；紧急情况请拨打 **110 / 120**。  
热线信息请以当地最新官方信息为准。

## 安装方式（按平台）

### DeepSeek Harness (DSH)

将 `hometown-companion/` 目录复制到 DSH 的 Skill 目录：

```bash
# 方式一：全局安装（推荐）
cp -r hometown-companion/ ~/.dsh/skills/xiangtupeiubanshi/

# 方式二：通过 npm 包安装
npm install -g xiangtupeiubanshi

# 方式三：直接放置在 DSH checkout 目录
cp -r hometown-companion/ "C:/Users/wu'xin/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeiubanshi/"
```

安装后，在对话中输入 `$xiangtupeiubanshi` 即可启用。

### Claude Code (Anthropic)

将 Skill 安装到 Claude Code 的全局 Skill 目录：

```bash
# 全局安装（所有项目可用）
mkdir -p ~/.claude/skills/xiangtupeiubanshi
cp -r hometown-companion/* ~/.claude/skills/xiangtupeiubanshi/

# 或项目级安装（仅当前项目可用）
mkdir -p .claude/skills/xiangtupeiubanshi
cp -r hometown-companion/* .claude/skills/xiangtupeiubanshi/
```

安装后，重启 Claude Code 或在新对话中输入 `@xiangtupeiubanshi` 即可启用。

### Codex (OpenAI)

将 Skill 安装到 Codex 的 Skill 目录：

```bash
# 全局安装
mkdir -p ~/.codex/skills/xiangtupeiubanshi
cp -r hometown-companion/* ~/.codex/skills/xiangtupeiubanshi/

# 或项目级安装
mkdir -p .codex/skills/xiangtupeiubanshi
cp -r hometown-companion/* .codex/skills/xiangtupeiubanshi/
```

安装后，在 Codex 对话中输入 `$xiangtupeiubanshi` 或在设置中启用该 Skill。

### 通用方式（任何平台）

将 `SKILL.md` 作为系统提示词直接导入：

```
# 在平台的系统提示词或自定义指令中添加：
将 SKILL.md 的完整内容作为系统提示词导入。
```

或使用以下方式导入：

```bash
# 将 SKILL.md 内容复制到平台的系统提示词中
cat hometown-companion/SKILL.md
```

## 项目结构

```
xiangtupeiubanshi/
├── SKILL.md              # 核心框架 + 安全声明（≤200行）
├── agents/openai.yaml    # 角色配置 + 系统提示词
├── README.md             # 本文件
├── CHANGELOG.md          # 版本记录
├── VERSION               # 版本号
├── LICENSE               # MIT License + 内容引用附录
├── SECURITY.md           # 安全报告流程
├── CONTRIBUTING.md       # 贡献指南
├── CODE_OF_CONDUCT.md    # 行为准则
├── .gitignore            # 敏感文件排除规则
├── .github/              # GitHub 模板（Issue/PR/CI）
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/validate_skill.yml
├── scripts/              # 验证脚本
│   └── validate_skill.py
├── guides/               # 19 篇操作指南
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
├── examples/             # 5 个实际对话示例
├── references/           # 8 个参考文档
├── documentation/        # 开发者文档
└── _books/               # 书籍档案卡
```

## 贡献

欢迎提交方言表达、乡土意象、安全审查建议和创伤知情改进。  
请勿在 Issue 或 PR 中提交真实用户对话、个人隐私或危机案例细节。

## 许可证

MIT License。  
使用前请阅读并遵守安全声明与伦理原则。

---

## 推荐 Topics 标签

在 GitHub 仓库设置里添加：

```text
ai-skill
mental-health
emotional-support
trauma-informed
companion
hometown
rural
chinese
llm
safety
privacy
psychology
cbt
mindfulness
crisis-support
```
