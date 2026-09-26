---
title: _sources 目录说明
author: 乡土陪伴师项目
type: index
tags: [说明, 原始素材]
aliases: [sources 说明]
---

# `_books/_sources/` 目录说明

> 本目录存放**原始素材与核验底稿**，供档案卡溯源。**它不是临时文件，请勿随意删除。**

## 一、内容

| 文件 | 作用 |
|---|---|
| 12 个 PubMed 批次文件（`_pubmed_data.md` 与 `_pubmed_batch1` 至 `_pubmed_batch11`） | 项目 v3.5–4.0「书籍升级」阶段抓取的 **PubMed 学术文献摘要**，是各档案卡「真实学术信息（PubMed 验证）」章节的**证据底稿** |
| `乡土中国-原文核验.md` | 《乡土中国》原文结构核验底稿（篇目、篇幅、关键概念索引） |
| `生育制度-原文核验.md` | 《生育制度》原文结构核验底稿（16 章、篇幅、关键概念索引） |
| `人情、面子与权力的再生产-原文核验.md` | 翟学伟本书第二版原文结构核验底稿（四编十四篇、篇幅、关键概念索引） |

## 二、为什么必须保留

- **可溯源**：档案卡的学术论断可回溯到原始文献，是「A 级 / B 级」判定的证据链
- **被项目正式引用**：`README.md`、`INDEX.md` 均将其列为框架组成部分
- **被校验脚本豁免**：scripts 目录下的 validate_skill.py 显式跳过 `_pubmed` 前缀文件（不要求 frontmatter）
- **被测试断言**：tests 目录下的 white_box_test.py 中 test_pubmed_sources_archived 断言本目录存在且 PubMed 批次文件**恰为 12 个** —— **删除会导致测试失败**

## 三、注意

- 本目录文件**不计入书籍数**（`docs/manifest.yaml` 的 `books` 计数已排除）
- 本目录文件**不需要 frontmatter**（校验脚本豁免）
- 主流水线脚本会从备份还原 `_sources/`，因此其中**新增文件须由本脚本在 import 之后重新生成**
