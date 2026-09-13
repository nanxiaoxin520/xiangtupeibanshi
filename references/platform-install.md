# 平台安装指南

本文件说明如何在各 AI 平台安装 xiangtupeibanshi Skill。

## DeepSeek Harness (DSH)

### 路径说明

DSH 的 Skill 目录位于 DSH checkout 下：

```
C:\Users\wu'xin\npm-global\node_modules\@deepseek-ai\dsh\
└── skills\
    └── xiangtupeibanshi\
        ├── SKILL.md
        ├── agents\
        │   └── openai.yaml
        ├── guides\
        ├── references\
        ├── examples\
        ├── scripts\
        └── _books\
```

### 安装步骤

```bash
# 1. 确保 DSH 已安装
# DSH checkout: C:\Users\wu'xin\npm-global\node_modules\@deepseek-ai\dsh

# 2. 复制 Skill 到 DSH skills 目录
cp -r hometown-companion/ "C:/Users/wu'xin/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/"

# 3. 验证安装
ls "C:/Users/wu'xin/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/SKILL.md"

# 4. 在 DSH 对话中使用
# 输入 $xiangtupeibanshi 启用 Skill
```

### DSH 配置验证

```bash
# 检查 DSH 是否识别了 Skill
# 在 DSH 中输入:
$xiangtupeibanshi
```

---

## Claude Code (Anthropic)

### 路径说明

```
~/.claude/skills/xiangtupeibanshi/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── guides/
├── references/
└── ...
```

### 安装步骤

```bash
# 全局安装
mkdir -p ~/.claude/skills/xiangtupeibanshi
cp -r hometown-companion/* ~/.claude/skills/xiangtupeibanshi/

# 或项目级安装
mkdir -p .claude/skills/xiangtupeibanshi
cp -r hometown-companion/* .claude/skills/xiangtupeibanshi/
```

### 使用方式

在 Claude Code 对话中输入 `@xiangtupeibanshi` 启用。

---

## Codex (OpenAI)

### 路径说明

```
~/.codex/skills/xiangtupeibanshi/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── guides/
├── references/
└── ...
```

### 安装步骤

```bash
# 全局安装
mkdir -p ~/.codex/skills/xiangtupeibanshi
cp -r hometown-companion/* ~/.codex/skills/xiangtupeibanshi/

# 或项目级安装
mkdir -p .codex/skills/xiangtupeibanshi
cp -r hometown-companion/* .codex/skills/xiangtupeibanshi/
```

### 使用方式

在 Codex 对话中输入 `$xiangtupeibanshi` 启用。

---

## 通用方式

如果以上平台路径不适用，可以将 `SKILL.md` 内容作为系统提示词直接导入：

```bash
# 查看 SKILL.md 内容并复制到平台的系统提示词
cat SKILL.md
```

---

## 验证安装

安装完成后，验证 Skill 是否正确加载：

1. 输入 `$xiangtupeibanshi` 或 `@xiangtupeibanshi`
2. 确认 Skill 返回正确的角色名（乡土陪伴师）
3. 测试安全声明是否生效（非医疗声明、危机热线）
4. 测试创伤知情原则是否生效（不追问细节、不强迫回忆）

---

## 卸载

```bash
# DSH
rm -rf "C:/Users/wu'xin/npm-global/node_modules/@deepseek-ai/dsh/skills/xiangtupeibanshi/"

# Claude Code
rm -rf ~/.claude/skills/xiangtupeibanshi/

# Codex
rm -rf ~/.codex/skills/xiangtupeibanshi/
```
