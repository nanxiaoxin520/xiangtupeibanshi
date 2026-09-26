# 更新日志

本文件记录乡土陪伴师的版本变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---


## [Unreleased]

### 变更

- `SECURITY.md`：安全报告改为以公开 Issue 为主渠道，与 `.github/ISSUE_TEMPLATE/review.md` 的 Security Review 模板保持一致

### 文档

- 新增 `NOTICE.md`：内容引用与版权说明，界定 MIT 授权覆盖范围
- `README.md`、`CONTRIBUTING.md` 的许可证章节同步指向 `NOTICE.md`

---

## [0.1.3] - 2026-09-26 - 知识库扩充与多维分类 / 白盒测试（脚本口径 · 输出编码 · 文档计数）

### 知识库

- 书籍档案卡由 50 张扩充至 **122 张**，分 19 个书架分类；每卡统一为「正文 → 深度理解 → 使用规范 → 相关阅读」四层结构
- 逐本补充「深度理解」（核心模型 / 概念辨析 / 常见误解 / 证据与局限 / 一句话精髓）与「使用规范」（证据等级 / 适用议题 / 对应指南 / 核心可用技术 / 误用警示 / 事实核对）两层，并标注证据等级（A 15 / B 52（含 1 本 B-）/ C 53 / 不评级 1）
- 《乡土中国》《生育制度》《人情、面子与权力的再生产》三本依据**原文全文**复核，篇目结构、概念定义与引语取自原文；新增三份原文核验底稿（`_books/_sources/*-原文核验.md`，仅记版本、结构、篇幅与关键概念索引，不收录原文）
- 全部 122 张卡新增 **五维正交标注**：板块（12）· 读者层次（3）· 取向（8）· 文化圈（3）· 证据等级；分级标签由 8 个命名空间 188 个标签扩展到 12 个命名空间 214 个标签；`_books/README.md` 新增「多维分类总览」（板块 × 读者层次、板块 × 证据等级矩阵与三份分组书单）
- `references/书籍使用规范.md` 新增第 8 节「多维分类体系」，含受控词表、分布与改动入口

### 修复

- **编码**：三个脚本的输出统一为 UTF-8。Windows 控制台默认 cp936 时，调用方按 UTF-8 解码子进程 stderr 会抛 `UnicodeDecodeError`，`CompletedProcess.stderr` 变成 `None`，白盒套件因此报错——这也是交接记录里「测试套件卡死」的真面目（实测 86 用例 9.5 秒跑完，不存在挂起）
- **安全（热线）**：`fix_hotlines.py` 原先只把 `12356-5` 换成 `12356`，遇到 `12356-55` 会产出新错号 `123565`，且校验器只匹配 `12356-5` 前缀从而不再报错——现改为整段吞掉数字后缀，校验器同步放宽为 `12356-\d`
- **安全（热线）**：`400-821-1215` 被标注为「24 小时」（中文写法）时校验器判错而修正器只认 `24h`，形成修不掉的 CI 红；现两端同口径，且修正器保留原文前导空白与括号
- **误判**：否定豁免只认「非」，「不是 24 小时」「不提供 24 小时服务」等正确表述被判错；现豁免 非／不是／不再／未／不提供
- **数据破坏**：`fix_hotlines.py` 会改写 frontmatter、围栏代码块与行内代码段。已发生实例：`references/验证脚本说明.md` 的「禁止 `12356-5`」被改成「禁止 `12356`」（语义反转且校验器放行），同一文件另有一处反引号被 `clean_bold.py` 剥成不配对——两处均已修复
- **误称**：`400-821-1215` 被写作「生命热线」只有修正器管、校验器不查，错误可长期存在；现校验器同查，并把「××中心生命热线」这类机构名排除在改写之外
- **死结**：`check_bold_pollution` 会对行内代码段里的污染反例报错，而 `clean_bold.py` 偏偏不改写代码段——判错却修不了；现该校验豁免行内代码段

### 测试

- 白盒套件从 86 用例扩充到 146：补齐校验器各类检查中从未走过的分支（术语禁用、空/超长 description、缺权威源文件、缺 `_books/`、`main()` 失败与 `--quiet` 路径等），新增 `clean_bold` / `fix_hotlines` 的 CLI 与受保护区用例，并加入「校验判错 ⇔ 修正器改写」「三份受保护行实现同源」「跳过名单安全底线」三项跨脚本一致性检查
- 校验器新增第 13 类检查 `check_dimensions`：逐卡校验五维字段齐全、取值落在受控词表内、且与 `板块/读者/取向/文化圈` 标签同步；配套 7 个用例（含基线、缺字段、越界值、字段与标签脱同步、词表漂移比对、严格性）
- 新增 `TestIP0RegressionGuard`，为已发布的正文级事实订正钉住标记句，防止后续导入覆盖
- 行覆盖率：`validate_skill.py` 97%，`clean_bold.py` 97%，`fix_hotlines.py` 95%（未覆盖部分为函数文档字符串与 `sys.exit(main())` 入口行）

### 文档

- 修正计数漂移：`README.md`（references 9→10 两处、英文 `_books` 50→122）、`INDEX.md`（references 9→10、`_pubmed_batch*.md`→`_pubmed_*.md`）、`CLAUDE.md`（结构树补 `99-测试模式.md`、`版本介绍.md`、`platform-install.md`、`书籍使用规范.md`、`tests/`、`docs/`；验证内容改为真实 12 类；测试流程补白盒套件命令）
- `references/验证脚本说明.md` 新增「如何引用被禁写法」一节：三类内容检查只认白名单文件与行内代码段两种豁免

## [0.1.2] - 2026-09-18 - 资源链接修正

### 修复

- **昭阳医生**：`zhaoyangyisheng.com`（域名 NXDOMAIN，已失效）→ `https://www.zhaoyang.cn`（官方域名，实测 HTTP 200，证书有效至 2026-10-10）
- **KnowYourself**：`knowyourself.cc`（HTTPS 证书已过期 145 天）→ `https://www.knowyourself.com.cn`（官方域名，实测 HTTP 200，证书有效至 2026-12-03），共 2 处
- **移除「心理学空间网」**：`psybook.cn` 经公共 DNS 查询返回 NXDOMAIN，域名已失效且无替代入口
- **保留「中国心理学会」** `cpsbeijing.org`：经核验站点完全正常（HTTP 200，证书有效至 2026-11-06，TLS 1.2/1.3 均支持）。海外 CI runner 报 `HandshakeFailure` 属跨境网络策略拦截，**非站点故障**，不应据此删除该权威资源

### CI

- `links` 作业增加 `--exclude`，排除经实测确认被跨境拦截的域名；排除项必须附带实测依据，不得为「让 CI 变绿」随意添加
- 移除 `continue-on-error`，使外链检查恢复为真实阻断（实测其可正确捕获真实死链）

### 文档

- `references/热线与资源速查.md` §9 增加链接核验说明，记录核验方式、已知跨境拦截域名及其判定依据
- 修正 `CHANGELOG.md` 结构：`# 更新日志` 标题此前被 0.1.1 条目压至文件中部，现已归位至文首

---

## [0.1.1] - 2026-09-18 - 安全与一致性修复

### 安全修复

- 移除含明文访问令牌的 `setup_github.sh`
- 修正危机热线事实性错误：`12356-5` → `12356`；Lifeline Shanghai 标注英语服务与 10:00–22:00；补全座机 `800-810-1117`
- `references/热线与资源速查.md` 确立为热线唯一权威源，附核验日期与复核周期

### 功能修复

- 恢复 `SKILL.md` 行为内核：差序格局框架、3 维评估、5 步流程、危机转介、伦理边界、按议题路由表
- 恢复渐进式披露路由层，使 19 篇 guides 与 9 篇 references 可被按需加载

### 一致性修复

- 统一命名：清除 `xiangupeibanshi` / `xiangtupeiubanshi` / `hometown-companion` / `xinli-zhushou` 变体
- 新增 `docs/manifest.yaml` 作为内容计数唯一事实源
- 修正文档与实际不符的计数（guides / examples / references / books / documentation）
- 修复 `references/README.md` 指向不存在文件、`examples/README.md` 重复行

### 质量修复

- 清理全仓库「隔字加粗」格式污染（79 个文件）
- `validate_skill.py` 扩展至 12 类检查（frontmatter / 结构 / 预算 / 断链 / 占位符 / 命名 / 加粗 / 热线 / 书籍卡 / 版本 / 清单）
- CI 精简为单一校验入口，新增密钥扫描与外链检查
- 移除未被引用的 `package.json`

---

## [0.1.0] - 2025-09-12 - 初版发布

### 基本信息

- **项目名**：乡土陪伴师 Hometown Companion (xiangtupeibanshi)
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
