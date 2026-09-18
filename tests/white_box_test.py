#!/usr/bin/env python3
"""乡土陪伴师白盒测试套件。

覆盖范围：
  A. validate_skill.py 的 12 类检查——每类均验证「通过」与「失败」分支
  B. clean_bold.py 的清洗规则边界
  C. fix_hotlines.py 的邻近性判断与否定语境
  D. 真实仓库集成验收（结构 / 预算 / 路由可达性 / 热线 / 幂等性 / 密钥）

用法：
    python tests/white_box_test.py            # 运行全部
    python tests/white_box_test.py -v         # 详细输出
"""

from __future__ import annotations

import importlib.util
import shutil
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
      "---\ntitle: 《乡土中国》\nauthor: 费孝通\ntype: sociology\n---\n\n"
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
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1.1")
        self.assertIn("0.1.1", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_pubmed_sources_archived(self):
        self.assertTrue((ROOT / "_books" / "_sources").is_dir())
        self.assertEqual(len(list((ROOT / "_books").glob("_pubmed_*.md"))), 0)
        self.assertEqual(len(list((ROOT / "_books" / "_sources").glob("_pubmed_*.md"))), 12)

    def test_invalid_products_removed(self):
        for rel in ("package.json", "package-lock.json", "setup_github.sh"):
            self.assertFalse((ROOT / rel).exists(), f"{rel} 应已删除")


if __name__ == "__main__":
    unittest.main(verbosity=2)
