# xiangtupeibanshi Skill — 完整索引

> 本文档 = 整个 skill 框架的入口。  
> 用于开发者/AI 助手快速导航——来访者不应直接看到此文档。

## 核心文件（按优先级）

| 优先级 | 文件 | 作用 |
|---|---|---|
| **P0** | `SKILL.md` | 核心框架（≤200 行 / 8000 字） |
| **P0** | `agents/openai.yaml` | 角色配置（乡伴） |
| **P1** | `guides/README.md` | 指南导**航** |
| P1 | `references/README.md` | 参考文档导航 |
| P1 | `references/评估量表速查.md` | 工具（PHQ-9、GAD-7 等） |
| P1 | `references/热线与资源速查.md` | 中国本土热线 |
| P1 | `references/书籍档案索引.md` | 50+ 本书索引 |
| P1 | `references/关系伤害分析SOP.md` | 关系伤害分析 |
| P2 | `_books/README.md` | 书籍档案索引（详细） |
| P2 | `documentation/README.md` | 文档导航 |
| P2 | `scripts/validate_skill.py` | 自动验证工具 |

## 数据统计

| 维度 | 数量 |
|---|---|
| 书籍档案卡 | 50 本 |
| 指南（guides） | 19 篇 |
| 例子（examples） | 4 个 |
| 参考文档（references） | 9 篇 |
| 文档（documentation） | 5 篇 |
| 学术信息批次（_pubmed_batch*.md） | 12 个 |

## 验证状态

```bash
# 运行验证
python scripts/validate_skill.py
# 预期输出：xiangtupeibanshi validation passed
```

## 框架核心

- 角色：乡土中国陪伴师（乡伴）
- 文化框架：差序格局（费孝通《乡土中国》）
- 核心：治疗 + 陪伴（不是纯治疗、不是纯陪伴）
- 评估：3 维差序（内圈 / 中圈 / 外圈）
- 资源：5 层差序资源（自我 / 近关系 / 中关系 / 专业陪伴 / 专业治疗）
- 对话：5 步单次流程（接住 / 差序评估 / 心理教育 / 技能 / 行动）
- 伦理：4 大边界映射中国心理学会7 大原则

## 最后更新

- **v4.0**（关系伤害主题）：创建 `guides/71-关系冲突5场景.md`、`examples/04-关系伤害.md`、`references/关系伤害分析SOP.md`
- **v3.5-4.0**（书籍升级）：升级 50+ 本档案卡，整合 PubMed 学术信息
- **v4.1**（框架优化）：创建 `references/` 目录和完整索引
