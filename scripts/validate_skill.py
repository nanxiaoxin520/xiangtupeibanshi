#!/usr/bin/env python3
"""Validate the xiangtupeibanshi skill.

零外部依赖（不使用 PyYAML），以保持仓库「无依赖」的设计声明。

用法：
    python scripts/validate_skill.py            # 全部检查
    python scripts/validate_skill.py --quiet    # 仅输出失败项
退出码：0 = 通过；1 = 存在 ERROR。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []
# 非「技能内容」目录：测试代码含夹具字面量，不参与内容格式检查
SKIP_PARTS = {".git", "node_modules", "__pycache__", "_plan", "tests"}

# ---------- 预算与规范常量 ----------
SKILL_MAX_LINES = 200
SKILL_MAX_CHARACTERS = 8_000
SKILL_MAX_APPROX_TOKENS = 7_000
SKILL_NAME = "xiangtupeibanshi"
DESCRIPTION_MAX_CHARS = 1024

# 命名禁用变体（历史名 / 错误拼写 / 英文目录名）
FORBIDDEN_NAMES = (
    "xiangupeibanshi",
    "xiangtupeiubanshi",
    "hometown-companion",
    "xinli-zhushou",
)
# 历史残留术语（白名单文件除外）
FORBIDDEN_TERMS = ("goutoujunshi", "狗头军师", "shengjidaguai", "中国语境心理治疗师")
# 历史残留术语（goutoujunshi 等）白名单：这些文件可能合法叙述历史
TERM_ALLOWLIST = {"CHANGELOG.md", "CONTRIBUTING.md", "README.md"}
# 命名变体白名单：仅变更日志需记录「已移除的错误拼写」，README 等面向用户文件不得豁免
NAME_ALLOWLIST = {"CHANGELOG.md"}
# 变更日志会合法引用已删除的文件（如 package.json），不做断链检查
LINK_CHECK_SKIP = {"CHANGELOG.md"}

# 热线禁用写法（安全关键）
FORBIDDEN_HOTLINE_PATTERNS = (
    (re.compile(r"12356-5"), "「12356-5」为错误号码，应为 12356"),
    (re.compile(r"2022\s*新设"), "12356 于 2024-12 由国家卫健委设置，非 2022"),
)
CANONICAL_HOTLINE_FILE = "references/热线与资源速查.md"
CANONICAL_HOTLINES = ("12356", "010-82951332", "400-161-9995")
LIMITED_HOTLINE = "400-821-1215"  # Lifeline Shanghai：英语服务、10:00–22:00

# SKILL.md 必需结构标记（保证行为内核未被清空）
SKILL_REQUIRED_MARKERS = {
    "加载协议": "加载协议",
    "角色定义": "角色",
    "创伤知情原则": "创伤知情",
    "差序格局框架": "差序格局",
    "五步对话流程": "5 步单次对话流程",
    "危机识别与转介": "危机识别与转介",
    "伦理边界": "伦理边界",
    "按议题路由表": "按议题查找",
    "限制声明": "## 限制",
}

REQUIRED_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "README.md",
    "CHANGELOG.md",
    "VERSION",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "guides/README.md",
    "references/README.md",
    "documentation/README.md",
    "examples/README.md",
    "scripts/validate_skill.py",
)

REQUIRED_GUIDES = (
    "00-欢迎与定位.md",
    "01-第一次对话.md",
    "10-情绪识别与命名.md",
    "11-认知重构.md",
    "12-CBT核心技能.md",
    "13-正念与接纳.md",
    "20-内圈关系.md",
    "21-差序格局与家庭.md",
    "22-中圈关系.md",
    "23-工作议题.md",
    "30-自我探索.md",
    "31-意义议题.md",
    "40-危机识别.md",
    "41-资源连接.md",
    "50-自我照护.md",
    "60-中国心理学会7大原则.md",
    "70-关系伤害分析.md",
    "71-关系冲突5场景.md",
    "99-测试模式.md",
)

# 污染特征：连续 >=2 组「**单字符**」
BOLD_SIGNATURE = re.compile(r"\*\*(?:[^\s*]\*\*){2,}")


# ---------- 工具 ----------
def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def walk(patterns: tuple[str, ...] = ("*.md",), extra: tuple[str, ...] = ()) -> list[Path]:
    out: list[Path] = []
    for pat in patterns:
        for p in ROOT.rglob(pat):
            if SKIP_PARTS & set(p.relative_to(ROOT).parts):
                continue
            out.append(p)
    for name in extra:
        p = ROOT / name
        if p.is_file():
            out.append(p)
    return sorted(set(out))


TEXT_EXTRA = ("LICENSE", "VERSION")


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """极简扁平 YAML frontmatter 解析（零依赖）。"""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", text, re.DOTALL)
    if not m:
        return None, "缺少或格式错误的 YAML frontmatter（首行须为 ---）"
    data: dict[str, str] = {}
    for offset, raw in enumerate(m.group(1).split("\n"), start=2):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            return None, f"frontmatter 第 {offset} 行存在意外缩进（本仓库约定为扁平键值）"
        if ":" not in line:
            return None, f"frontmatter 第 {offset} 行缺少 ':' → {line.strip()!r}"
        key, value = line.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
            return None, f"frontmatter 第 {offset} 行非法键名 → {key!r}"
        data[key] = value.strip().strip('"').strip("'")
    return data, None


# ---------- 检查项 ----------
def check_skill_frontmatter() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        err("missing required path: SKILL.md")
        return
    data, problem = parse_frontmatter(read(skill))
    if data is None:
        err(f"SKILL.md: {problem}")
        return
    keys = list(data)
    if keys != ["name", "description"]:
        err(f"SKILL.md frontmatter 键须为 [name, description]，实际 {keys}")
    name = data.get("name", "")
    if name != SKILL_NAME:
        err(f"SKILL.md frontmatter name 须为 {SKILL_NAME!r}，实际 {name!r}")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        err(f"SKILL.md frontmatter name 不符合 [a-z0-9-]{{1,64}}：{name!r}")
    desc = data.get("description", "")
    if not desc:
        err("SKILL.md frontmatter description 为空")
    if len(desc) > DESCRIPTION_MAX_CHARS:
        err(f"SKILL.md description 超过 {DESCRIPTION_MAX_CHARS} 字符：{len(desc)}")
    if "<" in desc or ">" in desc:
        err("SKILL.md description 不得包含 '<' 或 '>'")
    if "**" in desc:
        warn("SKILL.md description 含 Markdown 加粗标记，部分平台不渲染")


def approximate_token_count(content: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    latin = len(re.findall(r"[A-Za-z0-9_]+", content))
    other = len(re.findall(r"[^\sA-Za-z0-9_\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    return cjk + int(latin * 1.3) + int(other / 4)


def check_skill_budget() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return
    content = read(skill)
    lines = len(content.splitlines())
    if lines > SKILL_MAX_LINES:
        err(f"SKILL.md 超过 {SKILL_MAX_LINES} 行：{lines}")
    if len(content) > SKILL_MAX_CHARACTERS:
        err(f"SKILL.md 超过 {SKILL_MAX_CHARACTERS} 字符：{len(content)}")
    tokens = approximate_token_count(content)
    if tokens > SKILL_MAX_APPROX_TOKENS:
        err(f"SKILL.md 近似 token 超预算：{tokens} > {SKILL_MAX_APPROX_TOKENS}")


def check_skill_structure() -> None:
    """确保行为内核未被清空（路由表 / 框架 / 危机协议存在）。"""
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return
    content = read(skill)
    for label, marker in SKILL_REQUIRED_MARKERS.items():
        if marker not in content:
            err(f"SKILL.md 缺少必需结构「{label}」（未找到 {marker!r}）")
    # 路由表必须真实指向存在的 guides
    for m in re.finditer(r"`guides/([^`]+\.md)`", content):
        target = ROOT / "guides" / m.group(1)
        if not target.is_file():
            err(f"SKILL.md 路由表指向不存在的文件：guides/{m.group(1)}")


def check_inventory() -> None:
    for path in REQUIRED_PATHS:
        if not (ROOT / path).exists():
            err(f"missing required path: {path}")
    for name in REQUIRED_GUIDES:
        if not (ROOT / "guides" / name).is_file():
            err(f"missing required guide: guides/{name}")


# 引用路径可解析的基准目录（仓库约定：文档中以仓库相对路径或同名子目录文件名引用）
LINK_BASES = ("", "guides", "references", "_books", "documentation", "examples", "scripts", "agents", ".github")


def resolve_reference(source: Path, target: str) -> bool:
    if (source.parent / target).exists() or (ROOT / target).exists():
        return True
    return any((ROOT / base / target).exists() for base in LINK_BASES if base)


def check_links() -> None:
    """检查 Markdown 链接、反引号路径、表格内裸文件名。"""
    md_link = re.compile(r"\]\(([^)\s]+)\)")
    tick_path = re.compile(r"`([^`\s]+\.(?:md|yaml|yml|py|json|txt))`")
    table_path = re.compile(r"\|\s*([^\s|]+\.(?:md|yaml|yml|py|json))\s*\|")
    for md in walk():
        if rel(md) in LINK_CHECK_SKIP:
            continue  # 变更日志会合法引用已删除的文件
        text = read(md)
        candidates = [m.group(1) for m in md_link.finditer(text)]
        candidates += [m.group(1) for m in tick_path.finditer(text)]
        candidates += [m.group(1) for m in table_path.finditer(text)]
        for raw in candidates:
            target = raw.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:|#)", target):
                continue
            if "<" in target or ">" in target:
                continue
            if not resolve_reference(md, target):
                err(f"broken link in {rel(md)}: {raw}")


SELF = Path(__file__).resolve()
# 说明占位符检查的文档行（含「占位符」字样）不计入
PLACEHOLDER_NOTE = re.compile(r"占位符|placeholder", re.IGNORECASE)
# 占位符模式：{{ 需排除 GitHub Actions 的 ${{ }} 与正则量词 {{2,}}
PLACEHOLDER_PATTERNS = (
    (re.compile(r"\[TODO"), "[TODO"),
    (re.compile(r"\[PLACEHOLDER\]"), "[PLACEHOLDER]"),
    (re.compile(r"(?<!\$)\{\{\s*[A-Za-z_]"), "{{ 模板变量"),
    (re.compile(r"\bFIXME\b"), "FIXME"),
    (re.compile(r"\bXXX\b"), "XXX"),
)


def check_placeholders() -> None:
    for path in walk(("*.md", "*.yaml", "*.yml", "*.py")):
        if path.resolve() == SELF:
            continue  # 校验器自身包含模式字面量
        for i, line in enumerate(read(path).split("\n"), start=1):
            if PLACEHOLDER_NOTE.search(line):
                continue
            bare = re.sub(r"`[^`]*`", "", line)  # 行内代码段内的示例不算
            for pattern, label in PLACEHOLDER_PATTERNS:
                if pattern.search(bare):
                    err(f"占位符残留 {label!r} in {rel(path)}:{i}")


def is_history(path: Path) -> bool:
    """变更日志需合法记录「已移除的旧名与错误写法」，予以豁免。"""
    return rel(path) in LINK_CHECK_SKIP


def strip_inline_code(line: str) -> str:
    """去除行内代码段。

    必须逐行调用：`` `[^`]*` `` 会跨行匹配围栏代码块定界符，
    若作用于整篇文本将连带吞掉代码块内容（曾导致漏检安装命令中的旧目录名）。
    """
    return re.sub(r"`[^`]*`", "", line)


def strip_inline_code_text(text: str) -> str:
    return "\n".join(strip_inline_code(line) for line in text.split("\n"))


# 规则说明语境：此类行中的反引号内容是「被引用的禁用写法」，不算违规。
# 反之，行内代码中的真实安装路径（如 `hometown-companion/`）仍须检出。
RULE_HINT = re.compile(r"禁用|禁止|变体|残留|移除|清除|拼写|旧名|forbidden", re.IGNORECASE)


def check_forbidden_terms() -> None:
    for path in walk(("*.md", "*.yaml", "*.yml"), extra=TEXT_EXTRA):
        name = rel(path)
        check_names = name not in NAME_ALLOWLIST
        check_terms = name not in TERM_ALLOWLIST
        if not check_names and not check_terms:
            continue
        for i, line in enumerate(read(path).split("\n"), start=1):
            hay = strip_inline_code(line) if RULE_HINT.search(line) else line
            hay = hay.lower()
            if check_names:
                for variant in FORBIDDEN_NAMES:
                    if variant in hay:
                        err(f"命名禁用变体 {variant!r} in {name}:{i}")
            if check_terms:
                for term in FORBIDDEN_TERMS:
                    if term.lower() in hay:
                        err(f"历史残留术语 {term!r} in {name}:{i}")


def check_bold_pollution() -> None:
    """检测「隔字加粗」污染（**本**文**档**）。"""
    for path in walk():
        text = read(path)
        flags = protected_lines(text)
        for i, line in enumerate(text.split("\n")):
            if flags[i]:
                continue
            if BOLD_SIGNATURE.search(line):
                err(f"加粗格式污染 in {rel(path)}:{i + 1}")


def protected_lines(text: str) -> list[bool]:
    lines = text.split("\n")
    flags = [False] * len(lines)
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            flags[i] = True
            if lines[i].strip() == "---":
                break
    in_fence = False
    for i, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            flags[i] = True
            in_fence = not in_fence
            continue
        if in_fence:
            flags[i] = True
    return flags


# 400-821-1215（Lifeline Shanghai）真实服务时间为 10:00–22:00
H24 = re.compile(r"24\s*(?:h|小时)", re.IGNORECASE)
NEGATION = re.compile(r"非\s*$")


def check_hotlines() -> None:
    canonical = ROOT / CANONICAL_HOTLINE_FILE
    if not canonical.is_file():
        err(f"missing canonical hotline file: {CANONICAL_HOTLINE_FILE}")
        return
    ctext = read(canonical)
    if "verified_at" not in ctext:
        err(f"{CANONICAL_HOTLINE_FILE} 缺少 verified_at 核验日期")
    for number in CANONICAL_HOTLINES:
        if number not in ctext:
            err(f"{CANONICAL_HOTLINE_FILE} 缺少权威号码 {number}")

    for path in walk(("*.md", "*.yaml", "*.yml")):
        if is_history(path):
            continue  # CHANGELOG 需记录历史错误写法
        name = rel(path)
        for i, line in enumerate(read(path).split("\n"), start=1):
            line = strip_inline_code(line)
            for pattern, reason in FORBIDDEN_HOTLINE_PATTERNS:
                if pattern.search(line):
                    err(f"热线写法错误 in {name}:{i} → {reason}")
            if LIMITED_HOTLINE not in line:
                continue
            for m in H24.finditer(line):
                context = line[max(0, m.start() - 8):m.start()]
                if NEGATION.search(context):
                    continue  # 「非 24 小时」为正确表述
                window = line[max(0, m.start() - 40):m.end() + 10]
                if LIMITED_HOTLINE in window:
                    err(f"{name}:{i} 将 {LIMITED_HOTLINE} 标为 24 小时"
                        f"（实为 10:00–22:00）")


def check_books() -> None:
    books = ROOT / "_books"
    if not books.is_dir():
        err("missing required directory: _books/")
        return
    for path in sorted(books.glob("*.md")):
        if path.name == "README.md" or path.name.startswith("_pubmed"):
            continue
        name = rel(path)
        data, problem = parse_frontmatter(read(path))
        if data is None:
            err(f"{name}: {problem}")
            continue
        for key in ("title", "author", "type"):
            if not data.get(key):
                err(f"{name}: frontmatter 缺少必需字段 {key}")
        if "未读" not in read(path):
            err(f"{name}: 缺少「重要的未读边界」声明")


def check_versions() -> None:
    version_file = ROOT / "VERSION"
    if not version_file.is_file():
        return
    version = read(version_file).strip()
    changelog = ROOT / "CHANGELOG.md"
    if changelog.is_file():
        ctext = read(changelog)
        if version not in ctext:
            err(f"VERSION ({version}) 未出现在 CHANGELOG.md 中")
    skill = ROOT / "SKILL.md"
    if skill.is_file():
        data, _ = parse_frontmatter(read(skill))
        if data and "version" in data and data["version"] != version:
            err(f"SKILL.md version ({data['version']}) 与 VERSION ({version}) 不一致")


def check_manifest() -> None:
    manifest = ROOT / "docs" / "manifest.yaml"
    if not manifest.is_file():
        warn("docs/manifest.yaml 不存在，跳过计数一致性检查")
        return
    text = read(manifest)
    for key, actual in (
        ("guides", len(list((ROOT / "guides").glob("*.md"))) - 1),
        ("examples", len(list((ROOT / "examples").glob("*.md"))) - 1),
        ("references", len(list((ROOT / "references").glob("*.md"))) - 1),
        ("documentation", len(list((ROOT / "documentation").glob("*.md"))) - 1),
        ("books", len([p for p in (ROOT / "_books").glob("*.md")
                       if p.name != "README.md" and not p.name.startswith("_pubmed")])),
    ):
        m = re.search(rf"^\s*{key}\s*:\s*(\d+)", text, re.MULTILINE)
        if not m:
            warn(f"manifest.yaml 缺少计数项 {key}")
            continue
        declared = int(m.group(1))
        if declared != actual:
            err(f"manifest.yaml {key}={declared} 与实际 {actual} 不一致")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="仅输出失败项")
    args = ap.parse_args()

    for check in (
        check_skill_frontmatter,
        check_skill_budget,
        check_skill_structure,
        check_inventory,
        check_links,
        check_placeholders,
        check_forbidden_terms,
        check_bold_pollution,
        check_hotlines,
        check_books,
        check_versions,
        check_manifest,
    ):
        check()

    for w in WARNINGS:
        print(f"WARN: {w}")
    for e in ERRORS:
        print(f"ERROR: {e}")

    if ERRORS:
        print(f"\n{SKILL_NAME} validation failed（{len(ERRORS)} 项错误）")
        return 1
    if not args.quiet:
        print(f"{SKILL_NAME} validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
