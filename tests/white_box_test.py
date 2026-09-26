#!/usr/bin/env python3
"""乡土陪伴师白盒测试套件。

覆盖范围：
  A. validate_skill.py 的 12 类检查——每类均验证「通过」与「失败」分支
  B. clean_bold.py 的清洗规则边界与 CLI 三分支
  C. fix_hotlines.py 的邻近性判断、否定语境与受保护区域
  E. 跨脚本一致性（校验器与修正器同口径、三份受保护行实现同源）
  D. 真实仓库集成验收（结构 / 预算 / 路由可达性 / 热线 / 幂等性 / 密钥 / 输出编码）

已知限制以「characterization」用例显式钉住当前行为，改动即失败，避免悄悄退化。

用法：
    python tests/white_box_test.py            # 运行全部
    python tests/white_box_test.py -v         # 详细输出
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


VS = load_module(SCRIPTS / "validate_skill.py", "vs_mod")
CB = load_module(SCRIPTS / "clean_bold.py", "cb_mod")
FH = load_module(SCRIPTS / "fix_hotlines.py", "fh_mod")


# ---------------------------------------------------------------- fixture
SKILL_OK = """---
name: xiangtupeibanshi
description: 乡土陪伴师——面向家庭创伤经历者的 AI 陪伴 Skill，非医疗工具。
---

# 乡土陪伴师

## 加载协议

本文件是行为内核。

## 角色

乡伴。

## 创伤知情六原则

不追问创伤细节。

## 核心框架：差序格局三圈

| 圈 | 内容 |
|---|---|
| 内圈 | 家人 |

## 5 步单次对话流程

| 步 | 做什么 |
|---|---|
| 1 接住 | 反映情绪 |

## 危机识别与转介

危险信号：自伤、自杀。号码 12356；紧急 110 / 120。

## 伦理边界

| 边界 | 原则 |
|---|---|
| 治疗伦理 | 善行 |

## 按议题查找

| 议题 | 加载 |
|---|---|
| 首次对话 | `guides/00-欢迎与定位.md` |

## 限制

本 Skill 不是专业心理治疗。
"""

CANONICAL_HOTLINE = """---
title: 热线与资源速查
verified_at: 2026-09-18
---

# 热线与资源速查

| 号码 | 名称 |
|---|---|
| **12356** | 全国统一心理援助热线 |
| **010-82951332** | 北京市心理援助热线 |
| **400-161-9995** | 希望 24 热线 |
| **400-821-1215** | Lifeline Shanghai（10:00–22:00，英语服务，非 24 小时） |
"""

REQUIRED_GUIDE_NAMES = (
    "00-欢迎与定位.md", "01-第一次对话.md", "10-情绪识别与命名.md",
    "11-认知重构.md", "12-CBT核心技能.md", "13-正念与接纳.md",
    "20-内圈关系.md", "21-差序格局与家庭.md", "22-中圈关系.md",
    "23-工作议题.md", "30-自我探索.md", "31-意义议题.md",
    "40-危机识别.md", "41-资源连接.md", "50-自我照护.md",
    "60-中国心理学会7大原则.md", "70-关系伤害分析.md",
    "71-关系冲突5场景.md", "99-测试模式.md",
)


def make_fixture(base: Path) -> Path:
    """构造一个可通过全部 12 类检查的最小仓库。"""
    def w(rel: str, text: str = "内容\n") -> None:
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    w("SKILL.md", SKILL_OK)
    w("VERSION", "0.1.1")
    w("CHANGELOG.md", "# 更新日志\n\n## [0.1.1] - 2026-09-18\n\n- 初版\n")
    w("LICENSE", "MIT License\n\nCopyright (c) 2026 xiangtupeibanshi contributors\n")
    w("NOTICE.md", "# 内容引用与版权说明\n\n代码适用 MIT；书籍整理与二手诠释不在授权范围内。\n")
    w("README.md", "# 乡土陪伴师\n")
    w("SECURITY.md", "# 安全\n")
    w("CONTRIBUTING.md", "# 贡献\n")
    w("agents/openai.yaml", "interface:\n  display_name: 乡土陪伴师\n")
    w("guides/README.md")
    for name in REQUIRED_GUIDE_NAMES:
        w(f"guides/{name}")
    w("references/README.md")
    w("references/热线与资源速查.md", CANONICAL_HOTLINE)
    w("documentation/README.md")
    w("examples/README.md")
    w("scripts/validate_skill.py", "#!/usr/bin/env python3\n")
    w("docs/manifest.yaml",
      "version: 0.1.1\nskill_name: xiangtupeibanshi\n"
      "guides: 19\nexamples: 0\nreferences: 1\ndocumentation: 0\nbooks: 1\n")
    w("_books/README.md")
    w("_books/《乡土中国》.md",
      "---\ntitle: 《乡土中国》\nauthor: 费孝通\ntype: sociology\n"
      "domain: 文化与社会\naudience: 进阶\napproach: 本土整合\n"
      "culture: 中国本土\nevidence: C\n"
      "tags: [板块/文化与社会, 读者/进阶, 取向/本土整合, 文化圈/中国本土, 主题/关系]\n---\n\n"
      "# 《乡土中国》\n\n## 重要的未读边界\n\n基于公开资料。\n")
    return base


class FixtureCase(unittest.TestCase):
    """为每个用例提供独立的最小仓库副本。"""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="wb-")
        self.root = Path(self._tmp)
        make_fixture(self.root)
        self._saved_root = VS.ROOT
        VS.ROOT = self.root
        VS.ERRORS.clear()
        VS.WARNINGS.clear()

    def tearDown(self) -> None:
        VS.ROOT = self._saved_root
        VS.ERRORS.clear()
        VS.WARNINGS.clear()
        shutil.rmtree(self._tmp, ignore_errors=True)

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_check(self, fn) -> list[str]:
        VS.ERRORS.clear()
        fn()
        return list(VS.ERRORS)

    def assertClean(self, fn, label: str) -> None:
        errs = self.run_check(fn)
        self.assertEqual(errs, [], f"{label} 基线应无错误，实际: {errs}")

    def assertErrors(self, fn, label: str, keyword: str) -> None:
        errs = self.run_check(fn)
        self.assertTrue(errs, f"{label} 应报错但未报错")
        self.assertTrue(any(keyword in e for e in errs),
                        f"{label} 错误信息应含 {keyword!r}，实际: {errs}")


# ============================================================ A. 校验器
class TestA1Frontmatter(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_skill_frontmatter, "frontmatter 基线")

    def test_missing_frontmatter(self):
        self.write("SKILL.md", "# 无 frontmatter\n")
        self.assertErrors(VS.check_skill_frontmatter, "缺 frontmatter", "frontmatter")

    def test_extra_key(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "name: xiangtupeibanshi", "version: 1.0.0\nname: xiangtupeibanshi"))
        self.assertErrors(VS.check_skill_frontmatter, "多余键", "键须为")

    def test_wrong_name(self):
        self.write("SKILL.md", SKILL_OK.replace("name: xiangtupeibanshi", "name: xinli-zhushou"))
        self.assertErrors(VS.check_skill_frontmatter, "错误 name", "name 须为")

    def test_description_with_angle_brackets(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "description: 乡土陪伴师——面向家庭创伤经历者的 AI 陪伴 Skill，非医疗工具。",
            "description: 含 <标签> 的描述"))
        self.assertErrors(VS.check_skill_frontmatter, "description 含尖括号", "不得包含")

    def test_indented_frontmatter(self):
        self.write("SKILL.md", "---\nname: xiangtupeibanshi\n  description: 缩进错误\n---\n\n# x\n")
        self.assertErrors(VS.check_skill_frontmatter, "frontmatter 缩进", "缩进")

    def test_missing_colon(self):
        self.write("SKILL.md", "---\nname xiangtupeibanshi\ndescription: d\n---\n\n# x\n")
        self.assertErrors(VS.check_skill_frontmatter, "缺冒号", "缺少 ':'")

    def test_illegal_key(self):
        self.write("SKILL.md", "---\n名称: 中文键\ndescription: d\n---\n\n# x\n")
        self.assertErrors(VS.check_skill_frontmatter, "非法键名", "非法键名")

    def test_empty_description(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "description: 乡土陪伴师——面向家庭创伤经历者的 AI 陪伴 Skill，非医疗工具。",
            "description:"))
        self.assertErrors(VS.check_skill_frontmatter, "空 description", "为空")

    def test_overlong_description(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "description: 乡土陪伴师——面向家庭创伤经历者的 AI 陪伴 Skill，非医疗工具。",
            "description: " + "长" * 1100))
        self.assertErrors(VS.check_skill_frontmatter, "超长 description", "超过")

    def test_name_not_matching_charset(self):
        """name 既不等于内核名，也不符合 [a-z0-9-]{1,64} → 两条错误都要出。"""
        self.write("SKILL.md", SKILL_OK.replace(
            "name: xiangtupeibanshi", "name: XiangTuPei_BanShi"))
        self.assertErrors(VS.check_skill_frontmatter, "name 字符集", "不符合")

    def test_bold_in_description_warns_only(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "description: 乡土陪伴师——面向家庭创伤经历者的 AI 陪伴 Skill，非医疗工具。",
            "description: **乡土陪伴师**——AI 陪伴 Skill"))
        VS.WARNINGS.clear()
        self.assertClean(VS.check_skill_frontmatter, "加粗 description 只应 WARN")
        self.assertTrue(any("加粗标记" in w for w in VS.WARNINGS),
                        f"应产生 WARN，实际 {VS.WARNINGS}")

    def test_missing_skill_file(self):
        (self.root / "SKILL.md").unlink()
        self.assertErrors(VS.check_skill_frontmatter, "SKILL.md 缺失", "missing required path")


class TestA2Budget(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_skill_budget, "预算基线")

    def test_exceed_lines(self):
        self.write("SKILL.md", "---\nname: xiangtupeibanshi\ndescription: d\n---\n" + "\n行\n" * 250)
        self.assertErrors(VS.check_skill_budget, "超行数", "行")

    def test_exceed_characters(self):
        body = "---\nname: xiangtupeibanshi\ndescription: d\n---\n" + "字" * 9000
        self.write("SKILL.md", body)
        self.assertErrors(VS.check_skill_budget, "超字符", "字符")

    def test_token_counter_monotonic(self):
        self.assertLess(VS.approximate_token_count("短"), VS.approximate_token_count("长" * 100))

    def test_missing_file_is_silent(self):
        """预算检查不报「缺文件」——那是 check_inventory 的职责，避免重复报错。"""
        (self.root / "SKILL.md").unlink()
        self.assertClean(VS.check_skill_budget, "SKILL.md 缺失时预算检查应静默")


class TestA3Structure(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_skill_structure, "结构基线")

    def test_missing_routing_table(self):
        self.write("SKILL.md", SKILL_OK.replace("## 按议题查找", "## 其他"))
        self.assertErrors(VS.check_skill_structure, "缺路由表", "按议题路由表")

    def test_missing_crisis_section(self):
        self.write("SKILL.md", SKILL_OK.replace("## 危机识别与转介", "## 其他"))
        self.assertErrors(VS.check_skill_structure, "缺危机协议", "危机识别与转介")

    def test_routing_target_missing(self):
        self.write("SKILL.md", SKILL_OK.replace("guides/00-欢迎与定位.md", "guides/99-不存在.md"))
        self.assertErrors(VS.check_skill_structure, "路由指向不存在文件", "路由表指向不存在")

    def test_gutted_kernel_detected(self):
        """核心回归：宣传页形态的内核必须被检出。"""
        self.write("SKILL.md", "---\nname: xiangtupeibanshi\ndescription: d\n---\n\n"
                               "# 乡土陪伴师\n\n## 它是什么\n\n- 一个温柔的倾听者\n")
        errs = self.run_check(VS.check_skill_structure)
        self.assertGreaterEqual(len(errs), 7, f"应检出至少 7 项结构缺失，实际 {len(errs)}")


class TestA4Inventory(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_inventory, "清单基线")

    def test_missing_guide(self):
        (self.root / "guides" / "40-危机识别.md").unlink()
        self.assertErrors(VS.check_inventory, "缺 guide", "missing required guide")

    def test_missing_required_path(self):
        (self.root / "SECURITY.md").unlink()
        self.assertErrors(VS.check_inventory, "缺必需路径", "missing required path")

    def test_content_notice_is_required(self):
        """NOTICE.md 界定 MIT 只覆盖代码；缺失会让内容授权范围失去声明，须直接报缺文件。"""
        (self.root / "NOTICE.md").unlink()
        self.assertErrors(VS.check_inventory, "缺内容授权声明", "missing required path: NOTICE.md")


class TestA5Links(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_links, "断链基线")

    def test_markdown_link_broken(self):
        self.write("README.md", "[缺失](guides/不存在.md)\n")
        self.assertErrors(VS.check_links, "Markdown 断链", "broken link")

    def test_backtick_path_broken(self):
        self.write("README.md", "见 `references/不存在.md`\n")
        self.assertErrors(VS.check_links, "反引号断链", "broken link")

    def test_table_cell_broken(self):
        """原版校验器漏检的关键场景。"""
        self.write("references/README.md", "| 文件 | 用途 |\n|---|---|\n| 平台安装指南.md | 安装 |\n")
        self.assertErrors(VS.check_links, "表格内断链", "broken link")

    def test_http_link_ignored(self):
        self.write("README.md", "[外链](https://example.com/x.md)\n")
        self.assertClean(VS.check_links, "外链应忽略")

    def test_changelog_exempt(self):
        self.write("CHANGELOG.md", "## [0.1.1]\n\n- 移除 `package.json`\n")
        self.assertClean(VS.check_links, "CHANGELOG 应豁免")


class TestA6Placeholders(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_placeholders, "占位符基线")

    def test_todo_detected(self):
        self.write("README.md", "这里 [TODO 待补\n")
        self.assertErrors(VS.check_placeholders, "[TODO", "[TODO")

    def test_github_actions_expression_allowed(self):
        """${{ }} 不应被误判。"""
        self.write("README.md", "env:\n  TOKEN: ${{ secrets.GITHUB_TOKEN }}\n")
        self.assertClean(VS.check_placeholders, "GitHub Actions 表达式应放行")

    def test_regex_quantifier_allowed(self):
        """正则量词 {{2,}} 不应被误判。"""
        self.write("README.md", "PATTERN = re.compile(r'(?:x){2,}')\n")
        self.assertClean(VS.check_placeholders, "正则量词应放行")

    def test_template_variable_detected(self):
        self.write("README.md", "值：{{ user_name }}\n")
        self.assertErrors(VS.check_placeholders, "模板变量", "模板变量")

    def test_placeholder_doc_line_exempt(self):
        self.write("README.md", "验证脚本会检查 [PLACEHOLDER] 占位符\n")
        self.assertClean(VS.check_placeholders, "说明占位符的行应豁免")


class TestA7Naming(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_forbidden_terms, "命名基线")

    def test_variant_detected(self):
        self.write("README.md", "使用 $xiangupeibanshi 启动\n")
        self.assertErrors(VS.check_forbidden_terms, "命名变体", "命名禁用变体")

    def test_case_insensitive(self):
        self.write("README.md", "# Xinli-Zhushou Skill\n")
        self.assertErrors(VS.check_forbidden_terms, "大小写不敏感", "命名禁用变体")

    def test_license_extensionless_scanned(self):
        self.write("LICENSE", "Copyright (c) 2026 xiangtupeiubanshi contributors\n")
        self.assertErrors(VS.check_forbidden_terms, "LICENSE 应被扫描", "命名禁用变体")

    def test_backtick_quoted_allowed(self):
        self.write("README.md", "禁止使用 `xiangupeibanshi` 这一拼写\n")
        self.assertClean(VS.check_forbidden_terms, "反引号引用应放行")

    def test_changelog_exempt(self):
        self.write("CHANGELOG.md", "## [0.1.1]\n\n- 清除 `xiangupeibanshi` 变体\n")
        self.assertClean(VS.check_forbidden_terms, "CHANGELOG 应豁免")

    def test_variant_in_fenced_block_detected(self):
        """回归：围栏代码块内的旧目录名必须被检出。

        `` `[^`]*` `` 若作用于整篇文本会跨行吞掉代码块内容，导致安装命令中的
        `hometown-companion` 漏检。
        """
        self.write("README.md", "```bash\ncp -r hometown-companion/ ~/.dsh/skills/x/\n```\n")
        self.assertErrors(VS.check_forbidden_terms, "代码块内变体", "命名禁用变体")

    def test_strip_inline_code_does_not_cross_lines(self):
        text = "```bash\ncp -r hometown-companion/ x\n```\n"
        self.assertIn("hometown-companion", VS.strip_inline_code_text(text))

    def test_readme_not_exempt(self):
        """README 面向用户，不得豁免命名检查。"""
        self.assertNotIn("README.md", VS.NAME_ALLOWLIST)

    def test_inline_code_path_still_detected(self):
        """行内代码中的真实安装路径（非规则引用）必须检出。"""
        self.write("SKILL.md", SKILL_OK + "\n将 `hometown-companion/` 放入技能目录\n")
        self.assertErrors(VS.check_forbidden_terms, "行内代码路径", "命名禁用变体")

    def test_error_message_has_line_number(self):
        self.write("README.md", "# 标题\n\n使用 xiangupeibanshi 启动\n")
        errs = self.run_check(VS.check_forbidden_terms)
        self.assertTrue(any(":3" in e for e in errs), f"应含行号 :3，实际: {errs}")


class TestA8BoldPollution(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_bold_pollution, "加粗基线")

    def test_pollution_detected(self):
        self.write("README.md", "> **本**文**档**的入口\n")
        self.assertErrors(VS.check_bold_pollution, "污染检出", "加粗格式污染")

    def test_legit_bold_allowed(self):
        self.write("README.md", "- **自伤**想法、行为\n")
        self.assertClean(VS.check_bold_pollution, "合法整词加粗应放行")

    def test_code_block_exempt(self):
        self.write("README.md", "```\n**本**文**档**\n```\n")
        self.assertClean(VS.check_bold_pollution, "代码块应豁免")

    def test_frontmatter_exempt(self):
        self.write("SKILL.md", "---\ndescription: **本**文**档**\n---\n\n# x\n")
        errs = [e for e in self.run_check(VS.check_bold_pollution) if "SKILL.md" in e]
        self.assertEqual(errs, [], f"frontmatter 应豁免，实际: {errs}")


class TestA9Hotlines(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_hotlines, "热线基线")

    def test_wrong_suffix_detected(self):
        self.write("guides/40-危机识别.md", "- 全国心理援助热线：12356-5\n")
        self.assertErrors(VS.check_hotlines, "12356-5", "热线写法错误")

    def test_wrong_year_detected(self):
        self.write("guides/40-危机识别.md", "- 12356（2022 新设）\n")
        self.assertErrors(VS.check_hotlines, "2022 新设", "热线写法错误")

    def test_limited_marked_24h_detected(self):
        self.write("guides/40-危机识别.md", "- **400-821-1215**（24h）\n")
        self.assertErrors(VS.check_hotlines, "400-821-1215 标 24h", "标为 24 小时")

    def test_negation_allowed(self):
        """「非 24 小时」是正确表述。"""
        self.write("guides/40-危机识别.md", "- 400-821-1215 Lifeline Shanghai，非 24 小时（10:00–22:00）\n")
        self.assertClean(VS.check_hotlines, "否定语境应放行")

    def test_adjacent_number_not_misflagged(self):
        """同行其他号码的 24h 不应误判到 400-821-1215 上。"""
        self.write("guides/40-危机识别.md",
                   "- 010-82951332（24h，最权威）/ 400-821-1215 Lifeline Shanghai（10:00–22:00）\n")
        self.assertClean(VS.check_hotlines, "非邻近的 24h 不应误判")

    def test_canonical_missing_verified_at(self):
        self.write("references/热线与资源速查.md", CANONICAL_HOTLINE.replace("verified_at: 2026-09-18\n", ""))
        self.assertErrors(VS.check_hotlines, "缺 verified_at", "verified_at")

    def test_canonical_missing_number(self):
        self.write("references/热线与资源速查.md", CANONICAL_HOTLINE.replace("**010-82951332**", "**000**"))
        self.assertErrors(VS.check_hotlines, "权威源缺号码", "缺少权威号码")


class TestA10Books(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_books, "书籍卡基线")

    def test_missing_field(self):
        self.write("_books/《A》.md", "---\ntitle: A\nauthor: B\n---\n\n未读边界\n")
        self.assertErrors(VS.check_books, "缺 type", "缺少必需字段 type")

    def test_missing_boundary(self):
        self.write("_books/《B》.md", "---\ntitle: B\nauthor: C\ntype: t\n---\n\n正文\n")
        self.assertErrors(VS.check_books, "缺未读边界", "未读边界")

    def test_pubmed_sources_exempt(self):
        self.write("_books/_sources/_pubmed_batch1.md", "无 frontmatter\n")
        self.assertClean(VS.check_books, "原始素材应豁免")


class TestA11Versions(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_versions, "版本基线")

    def test_version_not_in_changelog(self):
        self.write("VERSION", "9.9.9")
        self.assertErrors(VS.check_versions, "版本未记录", "未出现在 CHANGELOG")


class TestA12Manifest(FixtureCase):
    def test_baseline_clean(self):
        self.assertClean(VS.check_manifest, "清单基线")

    def test_count_mismatch(self):
        self.write("docs/manifest.yaml",
                   "guides: 99\nexamples: 0\nreferences: 1\ndocumentation: 0\nbooks: 1\n")
        self.assertErrors(VS.check_manifest, "计数不符", "不一致")

    def test_missing_manifest_warns_only(self):
        (self.root / "docs" / "manifest.yaml").unlink()
        errs = self.run_check(VS.check_manifest)
        self.assertEqual(errs, [], f"缺 manifest 应为 WARN 而非 ERROR，实际: {errs}")


# ============================================================ B. 清洗器
class TestA13Dimensions(FixtureCase):
    """多维正交标注闸门：字段齐全 + 取值受控 + 与标签同步。"""

    FULL = ("---\ntitle: A\nauthor: B\ntype: t\n"
            "domain: 依恋与创伤\naudience: 专业\napproach: 循证操作\n"
            "culture: 西方引进\nevidence: A\n"
            "tags: [板块/依恋与创伤, 读者/专业, 取向/循证操作, 文化圈/西方引进]\n---\n\n未读\n")

    def test_baseline_clean(self):
        self.assertClean(VS.check_dimensions, "多维标注基线")

    def test_missing_dimension_field(self):
        self.write("_books/《缺维度》.md",
                   "---\ntitle: 缺维度\nauthor: B\ntype: t\nevidence: C\n---\n\n未读\n")
        self.assertErrors(VS.check_dimensions, "缺板块字段", "缺 domain")

    def test_value_out_of_vocab(self):
        self.write("_books/《越界》.md", self.FULL.replace("domain: 依恋与创伤",
                                                        "domain: 玄幻修真"))
        self.assertErrors(VS.check_dimensions, "取值越界", "不在受控词表")

    def test_field_and_tag_must_stay_in_sync(self):
        self.write("_books/《脱同步》.md",
                   self.FULL.replace("tags: [板块/依恋与创伤, ", "tags: ["))
        self.assertErrors(VS.check_dimensions, "标签缺维度", "不同步")

    def test_evidence_grade_vocab(self):
        self.write("_books/《评级》.md", self.FULL.replace("evidence: A", "evidence: D"))
        self.assertErrors(VS.check_dimensions, "证据等级越界", "evidence='D'")

    def test_every_card_must_be_labeled(self):
        """闸门是严格的：没标注的卡会报错，而不是「有标就查」——否则会重演两层结构无门禁。"""
        self.write("_books/《未标注》.md", "---\ntitle: 未标注\nauthor: B\ntype: t\n---\n\n未读\n")
        errs = self.run_check(VS.check_dimensions)
        self.assertTrue(any("未标注" in e for e in errs), f"未标注卡应报错：{errs}")


class TestBCleanBold(unittest.TestCase):
    def test_pollution_removed(self):
        out, hit, res = CB.clean_line("> **本**文**档** = **整**个** s**k**i**l**l** 框**架**")
        self.assertTrue(hit)
        self.assertFalse(res)
        self.assertEqual(out, "> 本文档 = 整个 skill 框架")

    def test_crisis_script_cleaned(self):
        out, hit, _ = CB.clean_line('> "你**有**没有**想**过**伤害**自己**？"')
        self.assertTrue(hit)
        self.assertEqual(out, '> "你有没有想过伤害自己？"')

    def test_legit_bold_preserved(self):
        for line in ("- **自伤**想法、行为", "| **内圈**（家人） | 自己 |",
                     "- **不**追问创伤细节", "**乡土陪伴师**——面向家庭创伤经历者"):
            out, hit, _ = CB.clean_line(line)
            self.assertFalse(hit, f"不应改动: {line}")
            self.assertEqual(out, line)

    def test_inline_code_preserved(self):
        line = "使用 `**本**文**档**` 作为示例"
        out, _, _ = CB.clean_line(line)
        self.assertIn("`**本**文**档**`", out)

    def test_no_residual(self):
        out, _, res = CB.clean_line("- **自**我**接**纳**、**自**尊")
        self.assertFalse(res)
        self.assertEqual(out, "- 自我接纳、自尊")


# ============================================================ C. 热线修正
class TestCFixHotlines(unittest.TestCase):
    def test_suffix_removed(self):
        text, notes = FH.fix_text("热线 12356-5 可用")
        self.assertEqual(text, "热线 12356 可用")
        self.assertTrue(any("号码后缀错误" in n for n in notes))

    def test_year_removed(self):
        text, _ = FH.fix_text("- 12356（2022 新设）")
        self.assertNotIn("2022", text)

    def test_lifeline_renamed(self):
        text, _ = FH.fix_text("- 生命热线 400-821-1215")
        self.assertIn("Lifeline Shanghai", text)

    def test_adjacent_24h_replaced(self):
        text, _ = FH.fix_text("- **400-821-1215**（24h）")
        self.assertIn("10:00–22:00", text)
        self.assertNotIn("24h", text)

    def test_non_adjacent_24h_untouched(self):
        """核心缺陷回归：同行其他号码的 24h 不得被误改。"""
        line = "- 必给热线：010-82951332（最权威，24h）+ 400-161-9995 + 400-821-1215"
        text, _ = FH.fix_text(line)
        self.assertIn("24h", text)
        self.assertNotIn("10:00–22:00", text)

    def test_changelog_skipped(self):
        self.assertIn("CHANGELOG.md", FH.SKIP_FILES)


# ============================================================ D. 集成
class TestDIntegration(unittest.TestCase):
    """针对真实仓库的集成验收（使用已修复的仓库）。"""

    def setUp(self):
        self._saved = VS.ROOT
        VS.ROOT = ROOT
        VS.ERRORS.clear()

    def tearDown(self):
        VS.ROOT = self._saved
        VS.ERRORS.clear()

    def test_full_validation_passes(self):
        saved_argv = sys.argv
        sys.argv = ["validate_skill.py"]  # 避免 unittest 参数被 argparse 读取
        try:
            code = VS.main()
        finally:
            sys.argv = saved_argv
        self.assertEqual(code, 0, f"全量校验应通过，错误: {VS.ERRORS[:5]}")

    def test_skill_budget(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 200)
        self.assertLessEqual(len(text), 8000)
        self.assertLessEqual(VS.approximate_token_count(text), 7000)

    def test_skill_routing_targets_all_exist(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        import re as _re
        targets = _re.findall(r"`guides/([^`]+\.md)`", text)
        self.assertGreaterEqual(len(targets), 12, "路由表条目过少")
        for t in targets:
            self.assertTrue((ROOT / "guides" / t).is_file(), f"路由目标缺失: {t}")

    def test_no_leaked_credentials(self):
        import re as _re
        # 使用真实令牌特征（前缀 + 足够长度的密文），避免匹配到本测试文件中的模式字面量
        pat = _re.compile(r"(?:gho|ghp|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}")
        hits = []
        for p in ROOT.rglob("*"):
            if not p.is_file() or ".git" in p.parts or "node_modules" in p.parts:
                continue
            try:
                if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(p.relative_to(ROOT)))
            except OSError:
                continue
        self.assertEqual(hits, [], f"发现疑似凭据: {hits}")

    def test_no_hotline_suffix_residue(self):
        hits = [p.name for p in ROOT.rglob("*.md")
                if "12356-5" in p.read_text(encoding="utf-8")
                and p.name != "CHANGELOG.md"]
        self.assertEqual(hits, [], f"残留 12356-5: {hits}")

    def test_bold_pollution_zero(self):
        dirty = []
        for p in ROOT.rglob("*.md"):
            if ".git" in p.parts or "node_modules" in p.parts:
                continue
            text = p.read_text(encoding="utf-8")
            flags = VS.protected_lines(text)
            for i, line in enumerate(text.split("\n")):
                if not flags[i] and VS.BOLD_SIGNATURE.search(line):
                    dirty.append(f"{p.name}:{i+1}")
        self.assertEqual(dirty, [], f"残留加粗污染: {dirty[:5]}")

    def test_manifest_counts_match(self):
        VS.ERRORS.clear()
        VS.check_manifest()
        self.assertEqual(VS.ERRORS, [], f"清单计数不符: {VS.ERRORS}")

    def test_clean_bold_idempotent(self):
        import subprocess
        r = subprocess.run([sys.executable, str(SCRIPTS / "clean_bold.py"), "--check"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, "clean_bold --check 应为 0（无污染）")

    def test_fix_hotlines_idempotent(self):
        import subprocess
        r = subprocess.run([sys.executable, str(SCRIPTS / "fix_hotlines.py"), "--dry-run"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertIn("合计 0 个文件", r.stderr, "热线修正应已幂等（0 个待修）")

    def test_version_aligned(self):
        """版本号须在三处保持一致：VERSION / CHANGELOG / docs/manifest.yaml。

        断言「一致性不变量」而非硬编码版本号——否则每次发版都要改测试。
        """
        import re as _re
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$", "VERSION 须为语义化版本 x.y.z")

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog, f"CHANGELOG 缺少版本条目 ## [{version}]")
        self.assertTrue(changelog.lstrip().startswith("# "),
                        "CHANGELOG 须以一级标题开头（标题不得被版本条目压到中部）")

        manifest = (ROOT / "docs" / "manifest.yaml").read_text(encoding="utf-8")
        m = _re.search(r"^version:\s*(\S+)", manifest, _re.MULTILINE)
        self.assertIsNotNone(m, "docs/manifest.yaml 缺少 version 字段")
        self.assertEqual(m.group(1), version, "manifest 版本与 VERSION 不一致")

    def test_dimension_vocab_matches_data_source(self):
        """校验器里的受控词表须与数据源 _plan/_taxonomy_dimensions.tsv 一致。

        _plan/ 在 skill 仓之外（独立成仓 / CI 上不可见）时跳过，不因此变红。
        """
        src = ROOT.parent / "_plan" / "_taxonomy_dimensions.tsv"
        if not src.is_file():
            self.skipTest("_plan/_taxonomy_dimensions.tsv 不可见（skill 独立成仓场景）")
        keys = ["domain", "audience", "approach", "culture"]
        found = {k: set() for k in keys}
        books = 0
        for ln in src.read_text(encoding="utf-8-sig").split("\n"):
            f = [x.strip() for x in ln.split("|||")]
            if len(f) != 5:
                continue
            books += 1
            for k, v in zip(keys, f[1:]):
                found[k].add(v)
        self.assertEqual(books, len(list((ROOT / "_books").glob("《*.md"))),
                         "数据源书目数与 _books/ 卡片数不一致")
        for k in keys:
            self.assertEqual(found[k], VS.DIM_VOCAB[k],
                             f"{k} 词表漂移：数据源 {sorted(found[k])} vs 校验器 {sorted(VS.DIM_VOCAB[k])}")

    def test_pubmed_sources_archived(self):
        self.assertTrue((ROOT / "_books" / "_sources").is_dir())
        self.assertEqual(len(list((ROOT / "_books").glob("_pubmed_*.md"))), 0)
        self.assertEqual(len(list((ROOT / "_books" / "_sources").glob("_pubmed_*.md"))), 12)

    def test_invalid_products_removed(self):
        for rel in ("package.json", "package-lock.json", "setup_github.sh"):
            self.assertFalse((ROOT / rel).exists(), f"{rel} 应已删除")

    def test_child_output_is_utf8_decodable(self):
        """脚本输出必须可按 UTF-8 解码。

        Windows 控制台默认 cp936，曾使父进程按 UTF-8 解码子进程 stderr 时抛
        UnicodeDecodeError，CompletedProcess.stderr 变成 None，断言以
        TypeError 收场——真实缺陷被编码问题掩盖成「测试挂了」。
        """
        import subprocess
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        for script, args, needle, stream in (
            ("fix_hotlines.py", ["--dry-run"], "合计", "stderr"),
            ("clean_bold.py", ["--check"], "污染文件", "stderr"),
            ("validate_skill.py", [], "validation passed", "stdout"),
        ):
            r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                               cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", env=env)
            text = getattr(r, stream)
            self.assertIsNotNone(text, f"{script} 的 {stream} 解码失败（None）")
            self.assertIn(needle, text, f"{script} 输出缺少 {needle!r}：{text[:120]!r}")


# ============================================================ E. 未覆盖分支
class TestEValidatorBranches(FixtureCase):
    """补齐 A1–A12 中「从未走过」的分支（覆盖率驱动）。"""

    def test_a3_missing_file_is_silent(self):
        (self.root / "SKILL.md").unlink()
        self.assertClean(VS.check_skill_structure, "SKILL.md 缺失时结构检查应静默")

    def test_a5_angle_bracket_target_skipped(self):
        """CommonMark 允许用 <> 包裹含特殊字符的链接目标，此类目标跳过断链检查。"""
        self.write("README.md", "见 [转义路径](<guides/%E5%B8%A6.md>)\n")
        self.assertClean(VS.check_links, "尖括号包裹的目标应跳过")

    def test_a6_placeholder_note_line_can_conceal(self):
        """characterization：含「占位符」字样的行整行豁免，可藏匿真实占位符。

        钉住现状而非认可它——若要收紧（如只豁免说明性前缀），此用例应先被改写。
        """
        line = "本行解释占位符：此处仍有 [TODO 未完成\n"
        self.assertTrue(VS.PLACEHOLDER_NOTE.search(line))
        self.write("README.md", line)
        self.assertClean(VS.check_placeholders, "豁免行内的 [TODO 现状不被检出")

    def test_a7_forbidden_term_detected(self):
        """历史残留术语分支（此前 0 覆盖）。"""
        self.write("SECURITY.md", "示例：狗头军师\n")
        self.assertErrors(VS.check_forbidden_terms, "残留术语", "历史残留术语")

    def test_a7_term_allowlist(self):
        self.write("README.md", "示例：狗头军师\n")
        self.assertClean(VS.check_forbidden_terms, "README 术语应豁免")

    def test_a7_name_variant_not_term_exempted(self):
        """README 只豁免术语，不豁免命名变体——两类白名单不同源。"""
        self.write("README.md", "示例：xinli-zhushou\n")
        self.assertErrors(VS.check_forbidden_terms, "README 命名变体", "命名禁用变体")

    def test_a8_inline_code_exempt(self):
        """文档需要用反引号书写污染反例，否则成了既判错又修不了的死结。"""
        self.write("references/README.md", "检测「隔字加粗」（如 `**本**文**档**` 形态）\n")
        self.assertClean(VS.check_bold_pollution, "行内代码段应豁免")

    def test_a8_single_char_bold_false_positive(self):
        """characterization：`**1**月**2**日` 形态的合法排版会被判为污染。

        收紧正则会放过真正的污染（既有回归用例 test_crisis_script_cleaned），
        故保留误报并在报告中标注；此处钉住行为，避免无人察觉地变化。
        """
        self.assertTrue(VS.BOLD_SIGNATURE.search("- **1**月**2**日开会"))

    def test_a9_canonical_file_missing(self):
        (self.root / "references" / "热线与资源速查.md").unlink()
        self.assertErrors(VS.check_hotlines, "缺权威源文件", "missing canonical hotline file")

    def test_a10_books_dir_missing(self):
        shutil.rmtree(self.root / "_books")
        self.assertErrors(VS.check_books, "缺 _books 目录", "missing required directory")

    def test_a10_book_frontmatter_unparseable(self):
        self.write("_books/《坏卡》.md", "没有 frontmatter 的正文\n")
        self.assertErrors(VS.check_books, "卡片 frontmatter 解析失败", "frontmatter")

    def test_a10_book_boundary_is_substring_only(self):
        """characterization：断言是「未读」二字子串，不要求小节标题。

        正文任意位置出现「未读」即通过——真正的结构约束（`## 重要的未读边界`）
        未被校验，靠流水线纪律维持。
        """
        self.write("_books/《空洞卡》.md",
                   "---\ntitle: 空洞\nauthor: 佚名\ntype: 心理学\n---\n\n"
                   "# 空洞\n\n未读过本书的读者请先看导读。\n")
        self.assertClean(VS.check_books, "子串断言现状：无边界小节也通过")

    def test_a11_version_file_missing_is_silent(self):
        (self.root / "VERSION").unlink()
        self.assertClean(VS.check_versions, "VERSION 缺失时版本检查应静默")

    def test_a11_skill_version_conflicts_with_frontmatter_rule(self):
        """check_versions 支持 SKILL.md 的 version 键，而 A1 规定键只能是两个。

        后果：该分支只能与 A1 的错误同时出现，实际不构成独立的版本闸门。
        """
        self.write("SKILL.md", SKILL_OK.replace(
            "name: xiangtupeibanshi", "name: xiangtupeibanshi\nversion: 9.9.9"))
        self.assertErrors(VS.check_versions, "SKILL.md 版本不一致", "与 VERSION")
        self.assertErrors(VS.check_skill_frontmatter, "同一文件已被 A1 判错", "键须为")

    def test_a12_missing_count_key_warns_only(self):
        self.write("docs/manifest.yaml", "guides: 19\nexamples: 0\nreferences: 1\n")
        errs = self.run_check(VS.check_manifest)
        VS.WARNINGS.clear()
        VS.check_manifest()
        self.assertEqual(errs, [], f"缺计数项应为 WARN，实际 {errs}")
        self.assertTrue(any("缺少计数项" in w for w in VS.WARNINGS),
                        f"应 WARN 缺失计数项，实际 {VS.WARNINGS}")

    def test_rel_falls_back_for_outside_path(self):
        self.assertEqual(VS.rel(Path("Z:/outside/x.md")), str(Path("Z:/outside/x.md")))

    def test_a1_frontmatter_blank_line_allowed(self):
        self.write("SKILL.md",
                   "---\nname: xiangtupeibanshi\n\ndescription: d\n---\n\n# x\n")
        self.assertClean(VS.check_skill_frontmatter, "frontmatter 空行应跳过")

    def test_a5_anchor_link_skipped(self):
        self.write("README.md", "见 [本节](#检查项清单) 与 [外链](mailto:a@b.c)\n")
        self.assertClean(VS.check_links, "页内锚点与 mailto 不应做断链检查")

    def test_main_returns_one_on_errors(self):
        self.write("SKILL.md", "# 无 frontmatter\n")
        (self.root / "docs" / "manifest.yaml").unlink()  # 触发 WARN 分支
        buf = io.StringIO()
        saved_argv = sys.argv
        sys.argv = ["validate_skill.py"]
        try:
            with contextlib.redirect_stdout(buf):
                code = VS.main()
        finally:
            sys.argv = saved_argv
        self.assertEqual(code, 1, "有 ERROR 时退出码应为 1")
        out = buf.getvalue()
        self.assertIn("validation failed", out)
        self.assertIn("WARN: docs/manifest.yaml", out, "WARN 也应在退出码之前打印")
        self.assertTrue(any(line.startswith("ERROR: ") for line in out.splitlines()),
                        "失败输出应逐条打印 ERROR")

    def test_main_quiet_suppresses_success_line(self):
        sys.argv = ["validate_skill.py", "--quiet"]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                code = VS.main()
        finally:
            sys.argv = ["validate_skill.py"]
        self.assertEqual(code, 0, f"基线夹具应通过，错误：{VS.ERRORS[:3]}")
        self.assertNotIn("validation passed", buf.getvalue(), "--quiet 不应打印成功行")


class TestFCleanBoldInternals(unittest.TestCase):
    """clean_bold 的 scan / protected_flags / CLI 分支（此前只在子进程里跑过）。"""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="cb-")
        self.root = Path(self._tmp)
        self._saved_root, self._saved_argv = CB.ROOT, sys.argv
        CB.ROOT = self.root

    def tearDown(self):
        CB.ROOT, sys.argv = self._saved_root, self._saved_argv
        shutil.rmtree(self._tmp, ignore_errors=True)

    def write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_protected_flags_frontmatter_and_fence(self):
        text = "---\nd: **本**文**档**\n---\n正文 **本**文**档**\n```\n**本**文**档**\n```\n尾行\n"
        flags = CB.protected_flags(text)
        self.assertTrue(flags[1] and flags[2], "frontmatter 应受保护")
        self.assertFalse(flags[3], "正文污染行不应受保护")
        self.assertTrue(flags[5] and flags[6], "围栏代码块及其内容应受保护")
        self.assertFalse(flags[7])

    def test_scan_protects_frontmatter_and_fences(self):
        p = self.write("a.md", "---\nt: **本**文**档**\n---\n\n- **自**我**介**绍\n"
                             "- 污染 **本**文**档** 结尾还有 **\n")
        original, new, changed, residual = CB.scan(p)
        self.assertEqual(changed, 2, "frontmatter 行不受影响，应改 2 行")
        self.assertIn("t: **本**文**档**", new, "frontmatter 原文应保留")
        self.assertIn("- 自我介绍", new)
        self.assertEqual(residual, [], "代码段外的 ** 会被全部剥离，不存在真残留")

    def test_residual_only_reports_inline_code(self):
        """characterization：residual 只可能由行内代码段触发。

        clean_line 会剥掉代码段外的一切 `**`，所以「需人工复核」通道报的都是
        代码段引起的假报；而真正该人工看的孤立星号（`*`）反而不会被报。
        若要让人工复核通道有意义，需改成检测未配对的单个 `*`。
        """
        _, _, _, res = CB.scan(self.write("r1.md", "见 `**` 与 **本**文**档**\n"))
        self.assertEqual([n for n, _ in res], [1], "代码段里的 ** 被当成需人工复核")
        _, _, _, res = CB.scan(self.write("r2.md", "单个星号 * 残留 与 **本**文**档**\n"))
        self.assertEqual(res, [], "真正需要人工复核的孤立 * 不会被报出（已知限制）")

    def _cli(self, *args):
        import contextlib
        sys.argv = ["clean_bold.py", *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = CB.main()
        return code, out.getvalue() + err.getvalue()

    def test_cli_check_flags_and_write_repairs(self):
        self.write("b.md", "- **本**文**档**污染\n")
        code, log = self._cli("--check")
        self.assertEqual(code, 1, "--check 有污染应返回 1")
        self.assertIn("POLLUTED", log)
        code, log = self._cli("--dry-run")
        self.assertEqual(code, 0, "--dry-run 即使有污染也返回 0")
        self.assertIn("WOULD FIX", log)
        self.assertIn("**本**文**档**", (self.root / "b.md").read_text(encoding="utf-8"),
                      "--dry-run 不得写盘")
        code, log = self._cli("--write")
        self.assertEqual(code, 0)
        self.assertEqual((self.root / "b.md").read_text(encoding="utf-8"), "- 本文档污染\n")
        code, _ = self._cli("--check")
        self.assertEqual(code, 0, "写盘后应幂等")

    def test_cli_reports_residual_lines_for_review(self):
        """残留行要在输出里可见，否则人工复核无从谈起。"""
        self.write("c.md", "示例 `**` 与污染 **本**文**档**\n")
        code, log = self._cli("--dry-run")
        self.assertIn("需人工复核的残留行 1 行", log)
        self.assertIn("c.md:1", log)
        self.assertIn("残留行样例", log)


class TestGFixHotlinesGuards(unittest.TestCase):
    """fix_hotlines 的受保护区与邻近性——行内代码曾被改写并反转语义。"""

    def test_inline_code_not_rewritten(self):
        """规则示例常写在反引号里；改写它会把「禁止 X 后缀」变成「禁止 12356」。"""
        line = "禁止 `12356-5` 与 `2022 新设` 两种写法"
        text, notes = FH.fix_text(line)
        self.assertEqual(text, line, "行内代码段不得改写")
        self.assertEqual(notes, [])

    def test_fenced_block_and_frontmatter_not_rewritten(self):
        text = "---\nnote: 生命热线 400-821-1215（24h）\n---\n\n```\n12356-5\n```\n\n"
        new, _ = FH.fix_text(text)
        self.assertEqual(new, text, "frontmatter 与围栏代码块应整块受保护")

    def test_digit_suffix_fully_removed(self):
        """只删 `-5` 会让 12356-55 变成 123565：新错号且校验器不再报。"""
        for raw, want in (("热线 12356-55 可用", "热线 12356 可用"),
                          ("拨打 12356-58", "拨打 12356"),
                          ("热线 12356-5 与 12356-55", "热线 12356 与 12356")):
            text, _ = FH.fix_text(raw)
            self.assertEqual(text, want)
            self.assertIsNone(re.search(r"12356\d", text), f"不应留 concatenated 号码: {text}")

    def test_institution_name_preserved(self):
        line = "北京心理危机研究与干预中心生命热线 010-82951332"
        text, _ = FH.fix_text(line)
        self.assertEqual(text, line, "机构名前缀中的「生命热线」不是 Shanghai 线的别名")
        text, _ = FH.fix_text("- 生命热线 400-821-1215")
        self.assertIn("Lifeline Shanghai", text)

    def test_cn_duration_replaced_and_parens_preserved(self):
        text, notes = FH.fix_text("- **400-821-1215**（24 小时）")
        self.assertEqual(text, "- **400-821-1215**（10:00–22:00）")
        text, _ = FH.fix_text("- 400-821-1215 提供 24 小时服务")
        self.assertEqual(text, "- 400-821-1215 提供 10:00–22:00服务",
                         f"无括号时不应插入括号：{text}")
        self.assertTrue(notes or True)

    def test_negation_still_protected_after_broadening(self):
        for line in ("- 400-821-1215，非 24 小时（10:00–22:00）",
                     "- 400-821-1215 不是 24 小时热线",
                     "- 400-821-1215 未提供 24 小时服务"):
            text, _ = FH.fix_text(line)
            self.assertEqual(text, line, f"否定语境被误改：{text}")

    def test_blank_code_keeps_positions(self):
        """掩码必须等长，否则替换位置会漂移到文本其他区域。"""
        line = "前 `12356-5` 后 生命热线 400-821-1215（24h）"
        mask = FH.blank_code(line)
        self.assertEqual(len(mask), len(line))
        self.assertNotIn("12356-5", mask)
        self.assertIn("12356-5", line)

    def test_year_corrected_in_both_paren_forms(self):
        for raw, want in (("- 12356（2022 新设）", "- 12356（2024-12 设置）"),
                          ("- 12356(2022 新设)", "- 12356(2024-12 设置)"),
                          ("- 12356 于 2022 新设开通", "- 12356 于 2024-12 设置开通")):
            text, notes = FH.fix_text(raw)
            self.assertEqual(text, want)
            self.assertTrue(any("年份错误" in n for n in notes))

    def test_multiple_errors_on_one_line(self):
        text, notes = FH.fix_text("热线 12356-5，另有 生命热线 400-821-1215（24h）")
        self.assertEqual(text, "热线 12356，另有 Lifeline Shanghai 400-821-1215（10:00–22:00）")
        self.assertEqual(len(notes), 3, f"应记录 3 处修正，实际 {notes}")

    def test_misnomer_without_number_untouched(self):
        line = "这条生命热线帮了很多人的忙"
        text, _ = FH.fix_text(line)
        self.assertEqual(text, line, "未提及 400-821-1215 时不改写日常用语")

    def _cli(self, *args):
        sys.argv = ["fix_hotlines.py", *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = FH.main()
        return code, out.getvalue() + err.getvalue()

    def test_cli_dry_run_then_write_is_idempotent(self):
        """CLI 三分支：dry-run 不改盘、write 改盘、再跑一次应为 0 个文件。"""
        saved = FH.ROOT
        try:
            with tempfile.TemporaryDirectory() as td:
                FH.ROOT = Path(td)
                (FH.ROOT / "guides").mkdir()
                (FH.ROOT / "references").mkdir()
                (FH.ROOT / "references" / "热线与资源速查.md").write_text(
                    CANONICAL_HOTLINE, encoding="utf-8")
                target = FH.ROOT / "guides" / "40-危机识别.md"
                target.write_text("- 生命热线 400-821-1215（24h）\n热线 12356-5\n",
                                  encoding="utf-8")
                (FH.ROOT / "CHANGELOG.md").write_text("- 历史：12356-5 已移除\n",
                                                     encoding="utf-8")
                code, log = self._cli("--dry-run")
                self.assertEqual(code, 0)
                self.assertIn("WOULD FIX", log)
                self.assertIn("合计 1 个文件", log)
                self.assertIn("12356-5", target.read_text(encoding="utf-8"),
                              "dry-run 不得写盘")
                self._cli("--write")
                self.assertEqual(target.read_text(encoding="utf-8"),
                                 "- Lifeline Shanghai 400-821-1215（10:00–22:00）\n热线 12356\n")
                self.assertIn("- 历史：12356-5 已移除\n",
                              (FH.ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
                              "CHANGELOG 应被跳过")
                code, log = self._cli("--dry-run")
                self.assertIn("合计 0 个文件", log, "写盘后应幂等")
        finally:
            FH.ROOT = saved


    def test_iter_files_skips_archive_dirs_and_changelog(self):
        """SKIP_PARTS / SKIP_FILES 决定改写面；名单一旦漂移就可能扫进快照目录。"""
        saved = FH.ROOT
        try:
            with tempfile.TemporaryDirectory() as td:
                FH.ROOT = Path(td)
                for rel in ("guides/a.md", "CHANGELOG.md", "_plan/b.md",
                            "backups/c.md", "node_modules/d.md", ".git/e.md",
                            ".github/workflows/f.yml"):
                    p = FH.ROOT / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text("内容\n", encoding="utf-8")
                found = {str(p.relative_to(FH.ROOT)).replace("\\", "/")
                         for p in FH.iter_files()}
                self.assertEqual(found, {"guides/a.md", ".github/workflows/f.yml"},
                                 f"改写面不符预期：{sorted(found)}")
        finally:
            FH.ROOT = saved


class TestHCrossScriptConsistency(FixtureCase):
    """校验器与修正器必须同口径：判错即必修得，修得即必判错。"""

    SAMPLES = (
        "- **400-821-1215**（24h）",
        "- **400-821-1215**（24 小时）",
        "- 400-821-1215 提供 24 小时服务",
        "- 生命热线 400-821-1215 英语服务",
        "热线 12356-5 可用",
        "热线 12356-55 可用",
        "- 12356（2022 新设）",
        "- 12356 于 2022 新设开通",
        "- 400-821-1215，非 24 小时（10:00–22:00）",
        "- 400-821-1215 不是 24 小时热线",
        "- 010-82951332（24h，最权威）/ 400-821-1215 Lifeline Shanghai（10:00–22:00）",
        "北京心理危机研究与干预中心生命热线 010-82951332",
    )

    def validate_line(self, line: str) -> list[str]:
        """把样本写入真实会被扫描的文件，跑 check_hotlines，返回错误。"""
        guide = self.root / "guides" / "40-危机识别.md"
        baseline = guide.read_text(encoding="utf-8")
        guide.write_text(line + "\n", encoding="utf-8")
        try:
            return self.run_check(VS.check_hotlines)
        finally:
            guide.write_text(baseline, encoding="utf-8")

    def test_error_implies_fixable(self):
        for line in self.SAMPLES:
            with self.subTest(line=line):
                errs = self.validate_line(line)
                fixed, _ = FH.fix_text(line)
                self.assertEqual(bool(errs), fixed != line,
                                 f"校验判错={bool(errs)} 修正器改写={fixed != line} → 口径脱节")

    def test_fixer_output_revalidates_clean(self):
        """修正一次即应收敛到无错误；否则说明两端口径仍有缝隙。"""
        for line in self.SAMPLES:
            with self.subTest(line=line):
                fixed, _ = FH.fix_text(line)
                self.assertEqual(self.validate_line(fixed), [], f"修正后仍判错：{fixed}")

    def test_negation_forms_agree(self):
        """「非 / 不是 / 未」等否定表述：既不判错，也不被改写。"""
        for line in ("- 400-821-1215，非 24 小时（10:00–22:00）",
                     "- 400-821-1215 不是 24 小时热线",
                     "- 400-821-1215 未提供 24 小时服务"):
            with self.subTest(line=line):
                self.assertEqual(self.validate_line(line), [])
                self.assertEqual(FH.fix_text(line)[0], line)

    def test_skip_lists_share_safety_core(self):
        """三个脚本的跳过目录名单并不相同，但都必须排除 VCS 与依赖目录。

        clean_bold 额外不含 _plan/tests/backups——今天无 .md 落在这些目录，
        一旦放入就会被 --write 改写。此处钉住共同安全底线，提醒加目录时同步。
        """
        core = {".git", "node_modules", "__pycache__"}
        self.assertTrue(core <= VS.SKIP_PARTS, "validate 跳过名单缺安全项")
        self.assertTrue(core <= FH.SKIP_PARTS, "fix_hotlines 跳过名单缺安全项")
        self.assertTrue(core <= CB.SKIP_DIRS, "clean_bold 跳过名单缺安全项")

    def test_three_protected_line_implementations_agree(self):
        """validate.protected_lines / clean_bold.protected_flags / fix.protected_flags 同源语义。"""
        text = "---\na: **本**文**档**\n---\n\n正文 **本**文**档**\n```py\n**本**文**档**\n```\n"
        expected = [False, True, True, False, False, True, True, True, False]
        for label, fn in (("validate", VS.protected_lines), ("clean_bold", CB.protected_flags),
                          ("fix_hotlines", FH.protected_flags)):
            self.assertEqual(fn(text), expected, f"{label} 的受保护行判定与其他实现不一致")


class TestIP0RegressionGuard(unittest.TestCase):
    """T12 正文级事实订正的防回滚闸门（R7）。

    `_books/` 由流水线生成，重跑时会用 `_plan/_new_books_src/` + `_plan/*.tsv` 覆盖渲染件。
    T12 曾只改渲染件、未回写源件，订正在下一次重跑时被静默回滚（2026-09-26 实测）。
    此处钉住每处订正的标记句，使其丢失时立即变红。
    """

    MARKERS = {
        "婚姻心理学": ["[!danger] 作者归属不可靠", "托名汇编，不可作霍妮原著引用",
                   "[!danger] 「94% 预测率」失真，不得引用", "Heyman & Slep"],
        "人格心理学": ["[!note] 术语订正", "EYNSS", "PEN"],
        "直视骄阳": ["[!note] 出处订正", "1980 年《存在主义心理治疗》"],
        "爱的艺术": ["[!warning] 出处订正（重要）", "《占有还是存在》"],
        "我们时代的神经症人格": ["[!warning] 出处订正（重要）", "1945 年《我们内心的冲突》"],
        "挑战完美主义": ["Hewitt & Flett", "误增"],
    }

    def _card(self, name):
        path = ROOT / "_books" / ("《%s》.md" % name)
        self.assertTrue(path.is_file(), "缺少卡片 %s" % path.name)
        return path.read_text(encoding="utf-8")

    def test_p0_body_corrections_survive_pipeline(self):
        for name in sorted(self.MARKERS):
            text = self._card(name)
            for mark in self.MARKERS[name]:
                self.assertTrue(
                    mark in text,
                    "《%s》的 P0 订正标记「%s」丢失——很可能被流水线回滚，"
                    "须把订正回写 _plan/_new_books_src/ 或 _plan/*.tsv 后重跑" % (name, mark))

    def test_fabricated_third_author_only_in_correction(self):
        """「米凯尔」只允许出现在说明其系误增的订正句里。"""
        for line in self._card("挑战完美主义").split("\n"):
            if "米凯尔" in line:
                self.assertTrue("误增" in line or "不存在" in line,
                                "「米凯尔」出现在非订正语境：%s" % line[:60])


if __name__ == "__main__":
    unittest.main(verbosity=2)
