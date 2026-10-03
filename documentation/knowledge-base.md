# 知识库治理

> 本页只做一件事：**告诉你去哪里找权威口径**。内容本身不在这里复述——复述就会漂移，而漂移正是这一页过去的样子。

## 事实源（Single Source of Truth）

| 管什么 | 权威在哪 | 谁校验 |
|---|---|---|
| 书籍分类：书架（19）× 板块（12）、映射与例外 | `docs/taxonomy.md` | `check_dimensions`（板块受控词表） |
| 档案卡结构：13 个骨架节、自由带、标题受控词表 | `docs/card-schema.md` | `check_card_schema` |
| 标签命名空间：4 个受控正交维度 ＋ 8 个自由标注 | `docs/tag-vocabulary.md` | `check_tag_namespace` ＋ `TestDIntegration`（三处词表比对） |
| 内容计数：guides / examples / references / documentation / books | `docs/manifest.yaml` | `check_manifest` |
| 内容边界与逐本引用规范 | `references/书籍使用规范.md` | 人工复核 |
| 校验器有哪几类检查、怎么跑 | `references/验证脚本说明.md` | `TestA19DocCheckRegistry`（文档行序＝`CHECKS` 注册序） |
| 索引面：导航表是否漏收、文档计数是否等于实测 | `scripts/validate_skill.py` 的 `check_index_plane` | 同上 |

## 三层保护

每张档案卡对同一本书给出三层不同性质的陈述，引用时不要混用：

1. **来源与核验状态** — 卡内「真实学术信息」一节，括注写明依据（公开资料 / PubMed 验证 / 原文核验 …）
2. **常见误解与概念辨析** — 卡内「深度理解」一节
3. **诚实边界** — 卡内「重要的未读边界」一节，说明哪些取自原文、哪些是本项目的整合、哪些不能当结论用

## 改东西之前

- 卡片与 `_books/README.md`（MOC）都是**派生产物**，手工改会被下一次流水线覆盖——正确改法见上表「权威在哪」一列。
- 改完跑 `python scripts/validate_skill.py`，期望输出 `xiangtupeibanshi validation passed`。
- 新增检查项、改分类、改卡片骨架，都必须同步对应的 `docs/` 事实源，否则 CI 会红。
