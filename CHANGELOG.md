# 更新日志

## [0.1.0] - 2025-09-12 - 初版发布

### 基本信息

- **项目名**：乡土陪伴师 Hometown Companion (xiangtupeiubanshi)
- **定位**：面向家庭创伤经历者的 AI 陪伴 Skill
- **文化底色**：乡土记忆、方言温度、自然意象
- **原则**：创伤知情（不追问/不强迫/不评判/尊重沉默）
- **许可证**：MIT License

### 内容构成

- **SKILL.md**：核心框架 + 安全与伦理声明 + 危机识别与转介
- **README.md**：完整项目介绍 + 使用方式 + 贡献指南 + 许可证 + 推荐 Topics 标签
- **SECURITY.md**：安全报告流程与响应时间
- **CONTRIBUTING.md**：贡献规范与行为准则
- **LICENSE**：MIT 许可证 + 内容引用与版权说明附录
- **agents/openai.yaml**：显示名 + 默认 prompt + 系统提示词
- **.github/**：Issue 模板（bug/feature/content/review）+ PR 模板
- **.github/workflows/**：CI 工作流（validate_skill.py 验证 + 断链检查）
- **.gitignore**：排除 .env / 密钥 / 构建缓存 / 审计文件
- **scripts/**：验证脚本
- **guides/**：操作指南
- **references/**：参考文档索引
- **examples/**：示例对话
- **_books/**：书籍档案卡
- **documentation/**：开发者文档

### 安全声明

- 明确非医疗/非诊断/非替代专业服务（多处声明）
- 提供中国本土危机热线（12356 / 110 / 120）
- 创伤知情原则完整（不追问/不强迫/不评判/尊重沉默）
- 隐私优先声明（不收集不必要的个人信息）

### 验证状态

- `validate_skill.py` 通过
- 无硬编码密钥、无危险操作、无外部依赖
- .gitignore 已配置完整敏感文件排除规则
- GitHub 仓库合规文件齐全（LICENSE/SECURITY/CONTRIBUTING/.gitignore/CI）
