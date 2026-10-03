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
# 中文输出须可被 CI / 调用方按 UTF-8 解析：Windows 控制台默认 cp936 会破坏重定向内容
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")
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

# 热线禁用写法（安全关键）。后缀用 \d 而非固定 5，避免 12356-55 之类变体漏检。
FORBIDDEN_HOTLINE_PATTERNS = (
    (re.compile(r"12356-\d"), "「12356-数字」为错误号码，全国统一心理援助热线是 12356，无后缀"),
    (re.compile(r"2022\s*新设"), "12356 于 2024-12 由国家卫健委设置，非 2022"),
)
# 误称仅在「同一行提到该号码」时判定，与 fix_hotlines 同口径；
# 否则「××中心生命热线」这类机构名会被判错却无从修正。
LIMITED_MISNOMER = re.compile(r"(?<!中心)生命热线")
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
    "NOTICE.md",
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
    "02-长期记忆.md",
    "10-情绪识别与命名.md",
    "11-认知重构.md",
    "12-CBT核心技能.md",
    "13-正念与接纳.md",
    "20-内圈关系.md",
    "21-差序格局与家庭.md",
    "22-中圈关系.md",
    "23-工作议题.md",
    "24-人物档案与判断.md",
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
# 污染的第二种形态：被双字词隔开的单字加粗（**不**替来访者**做**决定）。
# BOLD_SIGNATURE 要求相邻，看不见这种；改用「一行内被加粗的单个汉字 ≥2 处」判定。
BOLD_SPAN = re.compile(r"\*\*(.+?)\*\*")
CJK_ONE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def bold_polluted(line: str) -> bool:
    """隔字加粗判定（两种形态取并集）。

    只加粗单个拉丁字母（**P**sychoticism 这类首字母强调）属正常排版，不计入。
    """
    if BOLD_SIGNATURE.search(line):
        return True
    return sum(1 for m in BOLD_SPAN.finditer(line)
               if len(m.group(1)) == 1 and CJK_ONE.fullmatch(m.group(1))) >= 2


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
    """检测「隔字加粗」污染（**本**文**档** 与 **不**替来访者**做**决定 两态）。

    行内代码段豁免：文档需用反引号书写该形态的反例，而 clean_bold.py 也不改写
    代码段——若此处仍报错，就成了一处既判错又无法修复的死结。
    """
    for path in walk():
        text = read(path)
        flags = protected_lines(text)
        for i, line in enumerate(text.split("\n")):
            if flags[i]:
                continue
            if bold_polluted(strip_inline_code(line)):
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
# 否定语境：这些前缀表明「不是 24 小时」，属正确表述
NEGATION = re.compile(r"(?:非|不是|不再|未|不)\s*(?:提供|含)?\s*$")


def _claims_24h(text: str) -> bool:
    """text 是否把范围断言为 24 小时（「非 24 小时」这类否定写法不算）。"""
    for m in H24.finditer(text):
        if not NEGATION.search(text[max(0, m.start() - 8):m.start()]):
            return True
    return False


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
        heading = ""        # 当前行所属的小节标题，用于接住「标题写 24h、号码在下面的条目里」
        fence = False
        for i, line in enumerate(read(path).split("\n"), start=1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            if line.lstrip().startswith("#"):
                heading = line
                continue
            line = strip_inline_code(line)
            for pattern, reason in FORBIDDEN_HOTLINE_PATTERNS:
                if pattern.search(line):
                    err(f"热线写法错误 in {name}:{i} → {reason}")
            if LIMITED_HOTLINE not in line:
                continue
            if LIMITED_MISNOMER.search(line):
                err(f"热线写法错误 in {name}:{i} → 400-821-1215 的正式名称是 "
                    f"Lifeline Shanghai，不得写作「生命热线」")
            if heading and _claims_24h(heading) and "10:00" not in line:
                err(f"{name}:{i} 把 {LIMITED_HOTLINE} 列在小节「{heading.strip()}」下"
                    f"（实为 10:00–22:00，英语服务）")
            for m in H24.finditer(line):
                context = line[max(0, m.start() - 8):m.start()]
                if NEGATION.search(context):
                    continue  # 「非 24 小时」为正确表述
                window = line[max(0, m.start() - 40):m.end() + 10]
                if LIMITED_HOTLINE in window:
                    err(f"{name}:{i} 将 {LIMITED_HOTLINE} 标为 24 小时（"
                        f"实为 10:00–22:00，英语服务）")


# ---------- 口吻回归门禁（「说话方式」里可计数的三条） ----------
# 只扫 examples/：内核第 1 条前提就是「模型模仿示例胜过模仿规则」；
# guides 与 references 里的问句是候选清单，由各自开头的护栏约束，不参与本门禁。
TONE_EXEMPT_HEADINGS = ("反面", "不要模仿", "要是", "岔开")
TONE_SKIP_PREFIXES = ("> **相关", "> **本例")          # 篇首导读块，不是发给用户的句子
BANNED_COMFORT = (
    "别难过", "想开点", "这有什么大不了", "加油", "会好起来的", "你已经很棒了",
    "一切都是最好的安排", "痛苦是成长的礼物", "吃亏是福", "感谢那段经历",
    "要学会爱自己", "你得先顾好自己", "你真坚强", "你真棒",
    "我嘴笨", "我比你更糟", "谁不是这么过来的",
    # 空洞安慰：接不上她说过的任何一件事，只把人往外推（正文 3xf5j84ek8bvbqe：
    # 「安慰人只会说没事的、没事的，只会把他往外推」）
    "没事的", "会过去的", "别想太多",
)
# 禁句作为反例出现时的就近否定标记（如「不说"想开点"」）
COMFORT_NEGATION = ("不说", "不写", "不用", "不聊", "不念", "别", "不要",
                    "没写成", "禁止", "撤回", "不是")
INTERNAL_PATH = re.compile(r"(?:guides|_books|references|documentation)/[^\s`]*\.md")
QUESTION = re.compile(r"[？?]")


def _comfort_used_as_line(text: str) -> str | None:
    """禁句是否被当成话术端出来（而非作为反例提及）。命中则返回该禁句。"""
    for word in BANNED_COMFORT:
        pos = text.find(word)
        while pos >= 0:
            before = text[max(0, pos - 4):pos]
            if not any(cue in before for cue in COMFORT_NEGATION):
                return word
            pos = text.find(word, pos + len(word))
    return None


def check_tone_in_examples() -> None:
    """一轮最多一问、不把内部路径说给用户、不端有毒鸡汤——示例是模仿源，先钉住示例。

    句式是否雷同、是否真的接住了人，机器判不了；此处只管数得出的那三条。
    """
    d = ROOT / "examples"
    if not d.is_dir():
        return
    for path in sorted(d.glob("*.md")):
        name = rel(path)
        text = read(path)
        flags = protected_lines(text)
        heading = ""
        reply: list[tuple[int, str]] = []

        def flush(block: list[tuple[int, str]]) -> None:
            if not block:
                return
            joined = "".join(t for _, t in block)
            count = len(QUESTION.findall(joined))
            if count >= 2:
                err(f"口吻回归 in {name}:{block[0][0]} 一条回复 {count} 问"
                    f"（说话方式第 4 条：一轮最多一问）「{joined[:36]}」")

        for i, line in enumerate(text.split("\n")):
            if flags[i]:
                flush(reply); reply = []
                continue
            if line.startswith("#"):
                flush(reply); reply = []
                heading = line
                continue
            if not line.startswith(">"):
                flush(reply); reply = []
                continue
            if any(line.startswith(p) for p in TONE_SKIP_PREFIXES):
                flush(reply); reply = []
                continue
            if any(k in heading for k in TONE_EXEMPT_HEADINGS):
                flush(reply); reply = []
                continue
            reply.append((i, line))
            for m in INTERNAL_PATH.finditer(line):
                err(f"口吻回归 in {name}:{i + 1} 把内部路径说给用户"
                    f"（说话方式开篇约定）「{m.group(0)}」")
            word = _comfort_used_as_line(line)
            if word:
                err(f"口吻回归 in {name}:{i + 1} 端出有毒鸡汤「{word}」"
                    f"（说话方式第 7 条）")
        flush(reply)


# ---------- 长期记忆约定（guides/02）----------
MEMORY_GUIDE = "guides/02-长期记忆.md"
MEMORY_STORE_MARKER = ".xiangtupeibanshi"          # 档案落点标记（用户主目录下）
MEMORY_COMMAND_HEADINGS = ("### 查看", "### 暂停", "### 撤销", "### 清空")
MEMORY_HARD_RULES = ("**只写本地**", "**不上传**", "**不进 git**")
MEMORY_CONSENT_MARKS = ("单独同意", "默认不建")      # 危机项那一层：单独问、默认不开
MEMORY_DOWNGRADE_MARKS = ("云端", "降档")           # 云端宿主只记零隐私骨架
# 档案本体出现在仓库里 = 隐私外泄（落点约定在用户主目录，且 .gitignore 已挡）。
# 文件用前缀通配：换人另建一份 profile-<代号>.md，带后缀的档也得抓住。
MEMORY_REPO_TRACE_DIRS = (".xiangtupeibanshi", "memory")
MEMORY_REPO_TRACE_GLOBS = ("profile*.md", "safety*.md")
MEMORY_LEGACY_TERM = "画像"                        # 旧称，已被「长期记忆档案」取代
# D-1：一台电脑不止一个人——必须有分档办法，否则会把 A 的创伤念给 B 听
MEMORY_MULTIUSER_HEADING = "## 一台电脑不止一个人"
MEMORY_MULTIUSER_MARKS = ("代号", "不念、不引用、不改", "改代号")
MEMORY_HONESTY_MARKS = ("留存", "训练")                    # D-12 她问对话本身
MEMORY_THIRD_PARTY_MARKS = ("## 别人来要呢", "不念给任何人")  # D-13 旁人在场
MEMORY_REOPEN_MARKS = ("重新同意", "不追补")                # D-15 撤回后重开
# D-5：冷启动读档必须在内核的**入口节**里有触发点，不能只指望模型自己想起去加载 guides/02。
# 只查「内核里有没有这几个字」是不够的——写在限制一节里照样等于没有。
MEMORY_COLD_START_MARK = "静默读"
MEMORY_COLD_START_SECTIONS = ("## 加载协议", "## 开场白（固定）")


def _kernel_section(text: str, head: str) -> str:
    """取内核某一节的正文；该节不存在时返回空串。"""
    if head not in text:
        return ""
    return text.split(head, 1)[1].split("\n## ", 1)[0]


def check_memory_spec() -> None:
    """长期记忆：只落本机、先同意再写、两层默认不开、四条口令齐、云端降档。

    这一节写的是承诺，承诺就得能被机器查——否则又是一处「文档写了、没人执行」。
    """
    guide = ROOT / MEMORY_GUIDE
    if not guide.is_file():
        err(f"missing memory guide: {MEMORY_GUIDE}")
        return
    gtext = read(guide)

    skill_path = ROOT / "SKILL.md"
    skill = read(skill_path) if skill_path.is_file() else ""
    if MEMORY_GUIDE not in skill:
        err(f"SKILL.md 未把跨会话记忆路由到 {MEMORY_GUIDE}")

    missing = [h for h in MEMORY_COMMAND_HEADINGS if h not in gtext]
    if missing:
        err(f"{MEMORY_GUIDE} 口令小节不全：{missing}")
    absent = [p for p in MEMORY_HARD_RULES if p not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 存储硬账缺失：{absent}")
    absent = [p for p in MEMORY_CONSENT_MARKS if p not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 同意层级缺失：{absent}（危机要点须单独同意、默认不开）")
    absent = [p for p in MEMORY_DOWNGRADE_MARKS if p not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 宿主降档口径缺失：{absent}")
    if MEMORY_STORE_MARKER not in gtext:
        err(f"{MEMORY_GUIDE} 未声明档案落点（须含 {MEMORY_STORE_MARKER}，且落在仓库之外）")

    if MEMORY_MULTIUSER_HEADING not in gtext:
        err(f"{MEMORY_GUIDE} 缺「一台电脑不止一个人」一节——单档案换人即串档")
    else:
        absent = [m for m in MEMORY_MULTIUSER_MARKS if m not in gtext]
        if absent:
            err(f"{MEMORY_GUIDE} 分档办法不全：{absent}")

    absent = [m for m in MEMORY_HONESTY_MARKS if m not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 缺「她问起对话本身」的诚实口径：{absent}"
            f"（对话是否被宿主留存／训练，不由本 Skill 承诺）")
    absent = [m for m in MEMORY_THIRD_PARTY_MARKS if m not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 缺「别人来要呢」一节：{absent}"
            f"（第三人索要与她问别人的档，两种旁人在场都得有依据）")
    absent = [m for m in MEMORY_REOPEN_MARKS if m not in gtext]
    if absent:
        err(f"{MEMORY_GUIDE} 缺撤回后重开的口径：{absent}（不追补已删条目，清空才不会是假的）")

    if not any(MEMORY_COLD_START_MARK in _kernel_section(skill, h)
               for h in MEMORY_COLD_START_SECTIONS):
        err(f"SKILL.md 的「加载协议」或「开场白（固定）」内缺冷启动读档触发点"
            f"（未找到「{MEMORY_COLD_START_MARK}」）——只在议题命中时才路由 {MEMORY_GUIDE}，"
            f"第二次会话读不到档")

    traces = [d for d in MEMORY_REPO_TRACE_DIRS if (ROOT / d).exists()]
    traces += sorted({str(p.relative_to(ROOT))
                      for pat in MEMORY_REPO_TRACE_GLOBS for p in ROOT.glob(pat)})
    if traces:
        err(f"仓库内出现记忆档案，档案只能落在用户主目录：{traces}")

    gitignore = ROOT / ".gitignore"
    if gitignore.is_file() and MEMORY_STORE_MARKER not in read(gitignore):
        err(".gitignore 未忽略记忆档案目录")

    t99 = ROOT / "guides" / "99-测试模式.md"
    if not t99.is_file():
        return
    for name, text in (("SKILL.md", skill), ("guides/99-测试模式.md", read(t99))):
        if "长期记忆" not in text:
            err(f"{name} 未同步长期记忆口径（测试模式须声明不写档案）")
        if MEMORY_LEGACY_TERM in text:
            err(f"{name} 仍用旧称「{MEMORY_LEGACY_TERM}」，应改为长期记忆档案")


# ---------- 人物档案与判断（guides/24）----------
PERSON_GUIDE = "guides/24-人物档案与判断.md"
# 五路进料：少一路，判断就退化成「凭她一句话定罪」
PERSON_INPUT_MARKS = ("人物信息", "类型标签", "她的评分", "现实事件", "她自己的行为")
# 三层口径：没有解释层的竞争解释，判断层就成了贴标签
PERSON_LAYER_MARKS = ("事实层", "解释层", "判断层", "竞争")
# 判断句三硬要求：定性可执行、带把握度、带改口条件
PERSON_VERDICT_MARKS = ("把握度", "改口条件")
# 分级落点：默认判行为；给人定性只在她明确索要，且标成推测
PERSON_TIER_MARKS = ("第 1 层", "第 2 层", "只在她自己明确要这一句", "标成推测")
# 证据不足即拒判；不许拿类型标签补事实空缺
PERSON_REFUSE_MARKS = ("不足以下判断", "不许用 MBTI 补事实的空缺")
# 判断不用诊断词，且不替她答「打分在护什么」之外的结论
PERSON_NO_DIAGNOSIS_MARKS = ("不用诊断词", "本 Skill 不诊断")
# 推类型：默认在推，但不主动问、不主动说；跟要逐轮更新；停分「停嘴」与「停推」
PERSON_INFER_HEADING = "## 推类型：默认在推，不主动说"
PERSON_INFER_MARKS = ("推，默认开着", "说，要她先开口", "话里不出现", "不主动询问",
                      "只从她说出的现实事件推", "当场改口", "重复不是跟进",
                      "本场不再自行重启", "**停推**", "跨会话生效", "给她本人推",
                      "不拿推断替她做决定", "不替她贴四字标签", "不替她总结品格",
                      "既不说也不推", "至多两句", "不超 60 字", "过程不出口", "报流程",
                      "连「我不给」都不出口", "替代的检索词", "同一句反问",
                      "你／我二人称", "只说她说过的事")
# 同句绑定：只查「词在不在全文」会被别处同词顶包（check_decision_balance 同教训），
# 说了不问、停嘴不重启、停推不入档这三类裂缝都得靠位置判据堵住。
PERSON_INFER_SAME_LINE_PAIRS = (
    ("说，要她先开口", "话里不出现"),      # 不主动说的两半必须一句说完
    ("不主动询问", "不把话头"),            # 不问 ＆ 不引话题
    ("当场改口", "重复不是跟进"),          # 跟：有新事才改，没新事不复读
    ("停嘴", "本场不再自行重启"),          # 停嘴：本场不重启
    ("**停推**", "跨会话生效"),            # 停推：连后台停并入档
    ("既不说也不推", "安全评估"),          # 危机轮让路
    ("至多两句", "把话头交回给她"),        # 简洁：上限与「说完就交回」一句说完
    ("至多两句", "也算在内"),              # 不豁免：共情／接住句一并计入（2026-10-02 她定）
    ("过程不出口", "报流程"),              # 后台的账不念：依据／把握度／改口条件一说就成汇报
    ("连「我不给」都不出口", "替代的检索词"),  # 拒绝句与检索词同样是把类型再摆一遍（三批她再裁）
    ("短是省字", "削薄"),                  # 反向条款：防把简洁写成削薄处境／轮轮同一句反问
    ("你／我二人称", "旁观者"),            # 五批：光称「你」不够，得同时禁旁白口吻
    ("只说她说过的事", "她没讲"),          # 五批：光讲「有依据」不够，得写明她没讲的不补
)
# 她（产品负责人）逐字定稿的四条回复：长度与句式本身就是验收标准，改写＝改口径。
# 「这例」一类的疑似笔误**也不代她改字**——2026-10-02 她答「定稿句不改字」。
# 首条取代同日更早那句「你眼里这位朋友，是哪一点让你觉得他像 INTJ？」（她 15:4x 看图改判，见 #27 日志）。
PERSON_INFER_REPLY_LOCKS = (
    "他哪件事落在你眼里了，让你觉得他像那样？",
    "这例我判断不了，我硬凑不了一个人格给你。要不你把关于他的事说给我听听，让我猜猜他的人格。",
    "我只能推测他像是看不见你的难受，不是存心晾你。还有哪回你也这样一个人扛着？",
    "你想从哪件跟他开口？",
)
# 运行时镜像里有人物档案这一节时，简洁上限必须在场——只写在 guides 里，运行时读不到就等于没写
PERSON_RUNTIME_BLOCK = "【人物档案与判断】"
PERSON_RUNTIME_MARKS = ("至多两句", "不超 60 字", "过程不出口", "连「我不给」都不出口",
                        "替代的检索词", "把话头交回给她", "同一句反问")
# 时机：第一轮只做接住，判断在其后
PERSON_TIMING_MARK = "第一轮只做接住"
# 危机路径优先，命中危险信号时不走本篇
PERSON_CRISIS_MARK = "guides/40-危机识别.md"
# guides/02 须与本篇同口径：档案里记她的说法，不记我的定性
PERSON_ARCHIVE_MARKS = ("她的评分", "她的类型标签", "我给谁的定性都不落档",
                        "我推出来的类型倾向同样不落档", "长期停")


def check_person_judgment() -> None:
    """人物判断口径：五路进料齐、三层齐、判断句带把握度与改口条件、给人定性须她索要。

    这一节把「明确判断」写成了行为，就得防止它退化成两种老毛病：
    凭四个字母定罪，和骑墙到什么都不判。
    """
    guide = ROOT / PERSON_GUIDE
    if not guide.is_file():
        err(f"missing person-judgment guide: {PERSON_GUIDE}")
        return
    gtext = read(guide)

    skill_path = ROOT / "SKILL.md"
    skill = read(skill_path) if skill_path.is_file() else ""
    if PERSON_GUIDE not in skill:
        err(f"SKILL.md 未把人物判断路由到 {PERSON_GUIDE}——内核不路由，本篇永远不会被加载")

    absent = [m for m in PERSON_INPUT_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 进料不全：缺 {absent}（判断只能落在这五路上）")
    absent = [m for m in PERSON_LAYER_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 三层口径不全：{absent}（事实层／解释层／判断层须分开走）")
    absent = [m for m in PERSON_VERDICT_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 判断句要求缺失：{absent}"
            f"（无把握度与改口条件的判断等于信仰）")
    absent = [m for m in PERSON_TIER_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 分级落点不全：{absent}"
            f"（给人定性只在她明确索要那一问之后，且须标成推测）")
    absent = [m for m in PERSON_REFUSE_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 缺证据不足时的拒判口径：{absent}（不许拿类型标签补事实空缺）")
    absent = [m for m in PERSON_NO_DIAGNOSIS_MARKS if m not in gtext]
    if absent:
        err(f"{PERSON_GUIDE} 缺诊断边界：{absent}（判行为不判人格障碍，与本 Skill 不诊断同口径）")
    if PERSON_TIMING_MARK not in gtext:
        err(f"{PERSON_GUIDE} 未钉住时机：判断不得出现在第一轮接住里（缺「{PERSON_TIMING_MARK}」）")
    if PERSON_CRISIS_MARK not in gtext:
        err(f"{PERSON_GUIDE} 未让路给危机流程：命中危险信号先走 {PERSON_CRISIS_MARK}")

    if PERSON_INFER_HEADING not in gtext:
        err(f"{PERSON_GUIDE} 缺「推类型：默认在推，不主动说」一节——"
            f"这一格空着，模型要么没处推，要么没问就把类型结论倒给她")
    else:
        absent = [m for m in PERSON_INFER_MARKS if m not in gtext]
        if absent:
            err(f"{PERSON_GUIDE} 推类型口径不全：{absent}"
                f"（缺「说，要她先开口」或「话里不出现」＝没问就说；缺「不主动询问」＝逢人就问 MBTI；"
                f"缺「本场不再自行重启」或「**停推**」＝她的停不生效；"
                f"缺「至多两句／不超 60 字」＝类型话的长度上限被拆；缺「过程不出口／报流程」＝把后台的账念给她听；"
                f"缺「同一句反问」＝没有防死板的反向条款）")
        glines = gtext.splitlines()
        for left, right in PERSON_INFER_SAME_LINE_PAIRS:
            if not any(left in ln and right in ln for ln in glines):
                err(f"{PERSON_GUIDE} 推类型同句绑定断裂：「{left}」与「{right}」未落在同一句——"
                    f"分开写就等于这条没写")
        lost = [q for q in PERSON_INFER_REPLY_LOCKS if q not in gtext]
        if lost:
            err(f"{PERSON_GUIDE} 定稿句被改写：{lost}"
                f"（这两句逐字由她定的：一句问完就把话头交回，不把「为什么不能给」讲成一段）")
        runtime = ROOT / "agents" / "openai.yaml"
        if runtime.is_file():
            rtext = read(runtime)
            if PERSON_RUNTIME_BLOCK in rtext:
                absent = [m for m in PERSON_RUNTIME_MARKS if m not in rtext]
                if absent:
                    err(f"agents/openai.yaml {PERSON_RUNTIME_BLOCK} 未落地简洁上限：{absent}"
                        f"（运行时提示里没有这句，guides 里的长度约束在真实宿主上不会被执行）")

    memory = ROOT / MEMORY_GUIDE
    if memory.is_file():
        absent = [m for m in PERSON_ARCHIVE_MARKS if m not in read(memory)]
        if absent:
            err(f"{MEMORY_GUIDE} 人物档案字段未与本篇同步：{absent}"
                f"（档案只记她的说法，不记我给的定性）")


# ---------- 行动前的权衡（「分析利弊」这一环）----------
DECISION_KERNEL_MARK = "摊开两头的代价"
DECISION_STEP_HEAD = "## 5 步单次对话流程"
DECISION_GUIDE = "guides/12-CBT核心技能.md"
DECISION_GUIDE_HEADING = "## 摊开两头的代价"
# 两条不许退化：替她选（关系主义下最容易滑过去的那一步）、把暴力与危机也当成一门利弊来摊。
# 后者钉在**同一句**里——只查全节有没有「安全评估」四个字太松，抹掉那条禁则、
# 剩下资料出处里的引用照样能顶过去（2026-10-01 反证实测：新增 0 项）。
DECISION_GUIDE_MARKS = ("不替她选", "不进第一轮")   # 少一条，摊账就会抢在接住前面、或滑成替她定
# 必须**同句出现**的成对判据：光在全节里找得到这些字不算写了规则。
# 三次假绿换来的：①「安全评估」在资料出处那行还有第二次命中，抹掉危机禁则仍报 0 项；
# ②D-H4 那条 bullet 没写时，「先摊账」与「不替她选」分躺两行，机器照样绿；
# ③抹掉「摊完不替她选」时，D-H4 句里的「不替她选」把子串判定顶住了。
DECISION_SAME_LINE_PAIRS = (
    ("不摊利弊", "安全评估"),          # 危机与暴力场景不收这一环
    ("先摊账", "不替她选"),            # 被逼要结论时：先摊账，再拒绝替她定
    ("不替她选", "落点只问一句"),      # 摊完那一轮的落点问句，不许由别处的「不替她选」顶包
)
DECISION_EXAMPLE_MARK = "更付不起哪一笔"


def check_decision_balance() -> None:
    """接住情绪 → 分析利弊 → 给下一步：中间这一环此前整仓 0 命中。

    判据按位置取——第 5 步那一节里必须有，写在「限制」或某篇 guides 里都不算；
    内核还得把做法路由出去，guides 那节得留着两条禁则，示例里得有一处给模型模仿的落点问句。
    """
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return
    step = _kernel_section(read(skill), DECISION_STEP_HEAD)
    if DECISION_KERNEL_MARK not in step:
        err(f"SKILL.md「5 步单次对话流程」第 5 步缺「{DECISION_KERNEL_MARK}」——"
            f"这一环不落在步上，走到行动时就只剩一个小行动")
    if DECISION_GUIDE not in step:
        err(f"SKILL.md 第 5 步未把权衡做法路由到 {DECISION_GUIDE}")

    guide = ROOT / DECISION_GUIDE
    if not guide.is_file():
        err(f"missing decision-balance guide: {DECISION_GUIDE}")
        return
    body = _kernel_section(read(guide), DECISION_GUIDE_HEADING)
    if not body:
        err(f"{DECISION_GUIDE} 缺「{DECISION_GUIDE_HEADING}」一节")
        return
    absent = [m for m in DECISION_GUIDE_MARKS if m not in body]
    if absent:
        err(f"{DECISION_GUIDE}「摊开两头的代价」一节缺护栏：{absent}（这一环不进第一轮）")
    lines = body.split("\n")
    for pair in DECISION_SAME_LINE_PAIRS:
        if not any(all(k in ln for k in pair) for ln in lines):
            err(f"{DECISION_GUIDE}「摊开两头的代价」一节没把「{pair[0]}」与「{pair[1]}」写成一句——"
                f"这两个词分开出现在别处不算同一条规则（反证实测：拆开后破坏报 0 项）")

    d = ROOT / "examples"
    if d.is_dir() and not any(DECISION_EXAMPLE_MARK in read(p) for p in sorted(d.glob("*.md"))):
        err(f"examples/ 里没有一处摊代价的落点问句「{DECISION_EXAMPLE_MARK}」——"
            f"模型模仿示例胜过模仿规则，示例不给样就等于没这一环")


# ---------- 运行时镜像一致性 ----------
KERNEL_TONE_HEAD = "## 说话方式（硬约束）"
RUNTIME_TONE_HEAD = "【说话方式（硬约束）】"
KERNEL_OPENER_HEAD = "## 开场白（固定）"
# 固定开场句在两处各有包法：内核用 **…**，运行时提示词用 「…」
OPENER_KERNEL = re.compile(r"新对话的第一句固定为：\*\*(.+?)\*\*")
OPENER_RUNTIME = re.compile(r"新对话的第一句固定为：「(.+?)」")


def _kernel_tone_numbers() -> list[str] | None:
    """行为内核「说话方式」的条目编号，取不到返回 None。"""
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return None
    text = read(skill)
    if KERNEL_TONE_HEAD not in text:
        return None
    section = text.split(KERNEL_TONE_HEAD, 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^### (\d+)\s", section, re.MULTILINE)


def _runtime_tone_numbers() -> list[str] | None:
    """运行时提示词里的同一条目清单，取不到返回 None。"""
    yaml_path = ROOT / "agents" / "openai.yaml"
    if not yaml_path.is_file():
        return None
    text = read(yaml_path)
    if RUNTIME_TONE_HEAD not in text:
        return None
    tail = text.split(RUNTIME_TONE_HEAD, 1)[1]
    block = re.split(r"^\s*【", tail, maxsplit=1, flags=re.MULTILINE)[0]
    return re.findall(r"^\s*-\s+(\d+)\s", block, re.MULTILINE)


def _kernel_opener() -> str | None:
    """内核里那句固定开场白；没有「开场白（固定）」一节时返回 None（夹具与旧版走这条路）。"""
    skill = ROOT / "SKILL.md"
    if not skill.is_file() or KERNEL_OPENER_HEAD not in read(skill):
        return None
    m = OPENER_KERNEL.search(read(skill))
    return m.group(1) if m else ""


# 五批（2026-10-02 她裁「对话应该是你我的人称和视角，没有第三方的视角…不能多加推测没有的事」）：
# 二人称与非编造这两条只写在 guides/24 里管不到日常陪伴，只写内核则运行时读不到——两处都得在场。
# 同句绑定：光有「二人称」而没点名禁旁观者口吻＝没禁；光有「只说她说过的事」而没写「她没讲的不补」＝照样能编。
VOICE_SAME_LINE_PAIRS = (
    ("你／我二人称", "旁观者"),
    ("只说她说过的事", "她没讲"),
)
VOICE_FILES = ("SKILL.md", "agents/openai.yaml")


def check_runtime_mirror() -> None:
    """运行时的 system_prompt 是口吻的落地通道，与内核脱钩就等于口吻规则形同虚设。

    只比条目编号序列——措辞按平台长度需要精简，比对措辞会把合理的压缩判成漂移。
    开场句例外：它是要一字不改对外说出口的第一句话，两处必须完全一致。
    """
    yaml_path = ROOT / "agents" / "openai.yaml"
    if not yaml_path.is_file():
        return
    top_keys = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*) *:", read(yaml_path), re.MULTILINE)
    dups = sorted({k for k in top_keys if top_keys.count(k) > 1})
    if dups:
        err(f"agents/openai.yaml 顶层键重复：{dups}（后者覆盖前者，前者静默失效）")

    opener = _kernel_opener()
    if opener:
        ytext = read(yaml_path)
        m = OPENER_RUNTIME.search(ytext)
        if not m:
            err(f"agents/openai.yaml 未写固定开场句，应为「{opener}」")
        elif m.group(1) != opener:
            err(f"固定开场句两处不一致：SKILL.md「{opener}」vs "
                f"agents/openai.yaml「{m.group(1)}」")
        if "不介绍自己" not in ytext:
            err("agents/openai.yaml 缺「用过开场句后不介绍自己」的约定，运行时仍会自报家门")
        # D-H3（2026-10-01 真实宿主行为测试照出来的）：开场白前面不许带「我先读内核文件」
        # 这类过程话。这条禁令两处都得写——只写内核，另一侧的宿主照样先播报再说话。
        skill_file = ROOT / "SKILL.md"
        if skill_file.is_file() and "过程话" not in _kernel_section(read(skill_file), KERNEL_OPENER_HEAD):
            err("SKILL.md「开场白（固定）」没写「不加过程话」这条禁令"
                "（宿主会把「我先读内核文件」透进第一句，用户看见的是两句）")
        if "过程话" not in ytext:
            err("agents/openai.yaml【开场白（固定）】没写「不加过程话」，运行时侧仍会先播报")

    kernel = _kernel_tone_numbers()
    runtime = _runtime_tone_numbers()
    if kernel is None:
        warn("SKILL.md 未找到「说话方式（硬约束）」条目，跳过运行时镜像比对")
        return
    if runtime is None:
        err("agents/openai.yaml 缺少【说话方式（硬约束）】段，运行时与内核无对应关系")
        return
    if kernel != runtime:
        err(f"运行时口吻与内核脱节：SKILL.md 条目 {kernel} vs "
            f"agents/openai.yaml 条目 {runtime}")

    for rel in VOICE_FILES:
        path = ROOT / rel
        if not path.is_file():
            continue
        vlines = read(path).splitlines()
        broken = [f"「{left}」＋「{right}」" for left, right in VOICE_SAME_LINE_PAIRS
                  if not any(left in ln and right in ln for ln in vlines)]
        if broken:
            err(f"{rel} 人称与非编造条款未落地：{broken} 未落在同一句——"
                f"运行时把对话者称作「她」、或替她补一句她没说的细节，这两处判据各管一半")


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


# ── 多维正交分类的受控词表 ──
# 仓内事实源是 docs/tag-vocabulary.md §2；生成侧是 _plan/_taxonomy_dimensions.tsv。
# 词表刻意**不读仓外 TSV**（本仓须能独立成仓、CI 上 _plan 不可见），
# 漂移由 tests/white_box_test.py 的 TestDimensionVocabMatchesSource 双向比对三处，
# 且该测试在 _plan 不可见时**报红而非 skip**——2026-10-03 之前它是 skip，
# 造成「本地全绿＝CI 有守护」的错觉。
DIM_NS = {"板块": "domain", "读者": "audience", "取向": "approach", "文化圈": "culture"}
# 自由标注命名空间（开集，不设受控词表）。docs/tag-vocabulary.md §3 有定义与实测分布。
FREE_NS = {"主题", "方法", "流派", "类型", "概念", "人物", "文化", "典籍"}
TAG_VOCAB_DOC = "docs/tag-vocabulary.md"
DIM_VOCAB = {
    "domain": {"文化与社会", "关系与婚姻", "依恋与创伤", "循证疗法", "理论与诊断",
               "人格成长", "情绪身心", "发展与育儿", "危机与临终", "特殊人群",
               "本土临床", "专业规范"},
    "audience": {"专业", "进阶", "大众自助"},
    "approach": {"循证操作", "临床指南", "理论建构", "实证研究",
                 "自助练习", "人文思辨", "本土整合", "叙事纪实"},
    "culture": {"中国本土", "西方引进", "跨文化"},
}
EVIDENCE_GRADES = {"A", "B", "B-", "C", "不评级"}


def check_dimensions() -> None:
    """书卡的多维正交标注：字段齐全、取值受控、与标签同步。

    维度值由 _plan/obsidian_import.py 从 _plan/_taxonomy_dimensions.tsv 注入；
    本校验器不读 _plan（skill 须能独立成仓），故在此重复受控词表，
    并由 test_dimension_vocab_matches_source 在 _plan 可见时比对两处是否漂移。
    """
    books = ROOT / "_books"
    if not books.is_dir():
        return
    for path in sorted(books.glob("*.md")):
        if path.name == "README.md" or path.name.startswith("_pubmed"):
            continue
        name = rel(path)
        data, problem = parse_frontmatter(read(path))
        if data is None:
            continue                    # frontmatter 本身的问题由 check_books 报
        tags = data.get("tags", "")
        for ns, key in DIM_NS.items():
            val = data.get(key, "").strip().strip('"')
            if not val:
                err(f"{name}: 多维分类缺 {key}（{ns}）字段")
                continue
            if val not in DIM_VOCAB[key]:
                err(f"{name}: {key}={val!r} 不在受控词表 {sorted(DIM_VOCAB[key])} 内")
            if f"{ns}/{val}" not in tags:
                err(f"{name}: 标签缺「{ns}/{val}」，与 {key}={val} 不同步")
        ev = data.get("evidence", "").strip().strip('"')
        if not ev:
            err(f"{name}: 多维分类缺 evidence 字段")
        elif ev not in EVIDENCE_GRADES:
            err(f"{name}: evidence={ev!r} 不在 {sorted(EVIDENCE_GRADES)} 内")


def _tag_list(data: dict) -> list[str]:
    """从 frontmatter 的 tags 里取出标签数组（YAML 行内列表与裸字符串都吃）。"""
    raw = data.get("tags", "")
    if isinstance(raw, list):
        return [str(t).strip().strip('"\'') for t in raw]
    return [t.strip().strip('"\'') for t in raw.strip("[]").split(",") if t.strip()]


def check_tag_namespace() -> None:
    """标签命名空间：归属受控/自由两档、形态合规、仓内词表事实源在场。

    为什么要有这一条：`check_dimensions` 只遍历 `DIM_NS` 那 4 个受控命名空间，
    而 122 张卡实际用了 **12 个**。剩下 8 个（主题／方法／流派／类型／概念／人物／
    文化／典籍）此前**既无词表、也无门禁、也不在任何 docs 文件里登记**——
    事实存在但机器看不见。拼错前缀（如 `方法论/CBT`）不会被任何一道闸发现。

    只守形态与归属，**不守自由标注的取值**——那是开集，按定义没有受控词表。
    """
    books = ROOT / "_books"
    if not books.is_dir():
        return

    doc = ROOT / TAG_VOCAB_DOC
    if not doc.is_file():
        err(f"标签：缺仓内词表事实源 {TAG_VOCAB_DOC}")
    else:
        text = read(doc)
        # 按表格行匹配而非全文子串：`主题/` 在正文里出现多次（§1 总表、§2 说明、§3 表行），
        # 用 `ns/ in text` 判会把「删掉 §3 那一行」这种真破坏顶包掉（2026-10-03 反证 G5 实测）。
        # 行首 `| \`ns/\` |` 才是「已登记」的唯一形态。
        registered = set(re.findall(r"^\|\s*`([^`]+/)`\s*\|", text, re.M))
        for ns in sorted(set(DIM_NS) | FREE_NS):
            if ns + "/" not in registered:
                err(f"标签：{TAG_VOCAB_DOC} 的表格里未登记命名空间 {ns}/")

    for path in sorted(books.glob("*.md")):
        if path.name == "README.md" or path.name.startswith("_pubmed"):
            continue
        name = rel(path)
        data, problem = parse_frontmatter(read(path))
        if data is None:
            continue                    # frontmatter 本身的问题由 check_books 报
        tags = _tag_list(data)

        counts: dict[str, int] = {}
        for tag in tags:
            if not tag:
                continue
            ns = tag.split("/", 1)[0]
            if ns not in DIM_NS and ns not in FREE_NS:
                err(f"{name}: 标签 {tag!r} 的命名空间 {ns!r} 既不在受控维度 {sorted(DIM_NS)} "
                    f"也不在自由标注 {sorted(FREE_NS)} 内——新增命名空间须先登记 "
                    f"{TAG_VOCAB_DOC}")
                continue
            counts[ns] = counts.get(ns, 0) + 1
            if ns in DIM_NS:
                field_val = data.get(DIM_NS[ns], "").strip().strip('"')
                if tag != f"{ns}/{field_val}":
                    err(f"{name}: 受控标签 {tag!r} 与字段 {DIM_NS[ns]}={field_val!r} 不同步")

        for ns in DIM_NS:
            if counts.get(ns, 0) > 1:
                err(f"{name}: 受控命名空间 {ns}/ 出现 {counts[ns]} 个值，"
                    f"每卡只准一个（四个受控维度互斥）")


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


# ── 档案卡骨架（口径见 docs/card-schema.md）──
# 13 个骨架节，顺序固定；「真实学术信息」与「核心问题」之间是**自由带**（标题自由，至少一节）。
CARD_SKELETON = (
    "目录", "基础信息", "真实学术信息", "核心问题", "基本矛盾点", "根本矛盾点",
    "安慰和治疗", "解决方向", "心理咨询热线", "重要的未读边界",
    "深度理解", "使用规范", "相关阅读",
)
# 「真实学术信息」允许的括注。括注写的是「这张卡的依据是什么来源」，有信息量，故只收敛同义写法。
CARD_SOURCE_QUALIFIERS = {"公开资料", "PubMed 验证", "原文核验", "双重验证", "百度百科验证"}


def check_card_schema() -> None:
    """书卡骨架：13 个骨架节齐备且顺序固定、自由带非空、目录逐条等于正文、括注受控。

    为什么要有这一条：`check_books` 只查 frontmatter 三字段与「未读边界」子串，
    `check_dimensions` 只查多维标注——**卡内小节结构此前无任何门禁**，
    于是「真实学术信息」长出了 7 种标题、「未读边界」长出 2 种、
    122/122 张卡的目录都缺后注入的三节而无人发现。
    """
    books = ROOT / "_books"
    if not books.is_dir():
        return
    for path in sorted(books.glob("*.md")):
        if path.name == "README.md" or path.name.startswith("_pubmed"):
            continue
        name = rel(path)
        text = read(path)
        heads = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)]

        # 1) 括注受控词表
        for h in heads:
            if h.startswith("真实学术信息（") and h.endswith("）"):
                q = h[len("真实学术信息（"):-1]
                if q not in CARD_SOURCE_QUALIFIERS:
                    err(f"{name}: 「真实学术信息」括注 {q!r} 不在受控词表 "
                        f"{sorted(CARD_SOURCE_QUALIFIERS)} 内")

        # 2) 骨架节齐备 + 相对顺序
        pos_of: list[tuple[str, int]] = []
        missing = []
        for s in CARD_SKELETON:
            hit = [i for i, h in enumerate(heads) if h == s or h.startswith(s + "（")]
            if hit:
                pos_of.append((s, hit[0]))
            else:
                missing.append(s)
        if missing:
            err(f"{name}: 骨架节缺失 {missing}（口径见 docs/card-schema.md）")
        else:
            seq = [p for _, p in pos_of]
            if seq != sorted(seq):
                bad = [s for (s, p), (_, q) in zip(pos_of, pos_of[1:]) if p > q]
                err(f"{name}: 骨架节顺序错误——{bad} 排在了更靠后的骨架节之后")

        # 3) 自由带非空
        src_i = next((i for i, h in enumerate(heads)
                      if h == "真实学术信息" or h.startswith("真实学术信息（")), None)
        core_i = heads.index("核心问题") if "核心问题" in heads else None
        if src_i is not None and core_i is not None and core_i - src_i < 2:
            err(f"{name}: 「真实学术信息」与「核心问题」之间没有自由带小节"
                f"（卡片实质内容无处安放）")

        # 4) 目录逐条等于正文
        toc = re.findall(r"^- \[\[#(.+?)\]\]\s*$", text, re.M)
        body = [h for h in heads if h != "目录"]
        if toc != body:
            err(f"{name}: 卡内目录与正文不一致（目录 {len(toc)} 条 / 正文 {len(body)} 节）"
                f"——跑 `python _plan/rebuild_toc.py` 重建")


# 导航表必须覆盖的目录（README.md 自身不计）
INDEX_PLANE_DIRS = ("guides", "references", "examples", "documentation")


def check_index_plane() -> None:
    """索引面：导航表覆盖每一篇、索引书名用卡名、README 的中英计数等于**脚本现算**值。

    为什么要有这一条：18 类检查全在**内容面**，索引面 0 覆盖。于是
    `guides/README.md` 漏收 1 篇、`references/README.md` 漏收 2 篇、
    `README.md` 中英两段的篇数与类数互相矛盾且都与实测不符——
    这些漂移没有任何一道闸能发现。
    计数一律由脚本现算（`glob` 与 `len(CHECKS)`），**不读文档里的数字**，
    这样文档与代码不会再各自漂移。
    """
    for d in INDEX_PLANE_DIRS:
        nav = ROOT / d / "README.md"
        if not nav.is_file():
            err(f"索引面：缺 {d}/README.md")
            continue
        text = read(nav)
        for p in sorted((ROOT / d).glob("*.md")):
            if p.name == "README.md":
                continue
            if p.name not in text:
                err(f"索引面：{d}/README.md 未收录 {p.name}")

    # 书籍档案索引：表格第一列书名须逐字命中档案卡名（限定语应写进作者列或议题列）
    idx = ROOT / "references" / "书籍档案索引.md"
    books = ROOT / "_books"
    if idx.is_file() and books.is_dir():
        stems = {p.stem for p in books.glob("*.md")
                 if p.name != "README.md" and not p.name.startswith("_pubmed")}
        covered = set()
        for m in re.finditer(r"^\|\s*\d+\s*\|\s*([^|]*?)\s*\|", read(idx), re.M):
            cell = m.group(1).strip()
            names = re.findall(r"《[^《》]+》", cell)
            if not names:
                continue
            tail = cell[cell.rindex("》") + 1:].strip()
            if tail:
                err(f"索引面：references/书籍档案索引.md 第一列 {cell!r} 的书名后带了限定语 "
                    f"{tail!r}——限定语请写进作者列或议题列，否则按卡名检索会落空")
            for nm in names:
                if nm not in stems:
                    err(f"索引面：references/书籍档案索引.md 的书名 {nm} 不对应任何档案卡")
                else:
                    covered.add(nm)
        absent = sorted(stems - covered)
        if absent:
            err(f"索引面：references/书籍档案索引.md 未收录 {len(absent)} 张卡：{absent[:6]}")

    # README.md 中英两段的计数须相等，且等于现算值
    readme = ROOT / "README.md"
    if readme.is_file():
        text = read(readme)
        n_guides = len([p for p in (ROOT / "guides").glob("*.md") if p.name != "README.md"])
        for label, pat, actual in (
            ("中文段", r"guides/\s*#\s*(\d+)\s*篇操作指南", n_guides),
            ("英文段", r"guides/\s*#\s*(\d+)\s*operational guides", n_guides),
            ("中文段", r"validate_skill\.py\s*#\s*(\d+)\s*类内容校验", len(CHECKS)),
            ("英文段", r"validate_skill\.py\s*#\s*(\d+)\s*categories", len(CHECKS)),
        ):
            m = re.search(pat, text)
            if not m:
                err(f"索引面：README.md {label}未写计数（模式 {pat}）")
            elif int(m.group(1)) != actual:
                err(f"索引面：README.md {label}写 {m.group(1)}，实测 {actual}")

    # INDEX.md 数据统计表须等于现算值
    index = ROOT / "INDEX.md"
    if index.is_file():
        text = read(index)
        n_books = len([p for p in (ROOT / "_books").glob("*.md")
                       if p.name != "README.md" and not p.name.startswith("_pubmed")])
        for label, pat, actual in (
            ("书籍档案卡", r"书籍档案卡\s*\|\s*(\d+)", n_books),
            ("指南", r"指南（guides）\s*\|\s*(\d+)", n_guides),
            ("参考文档", r"参考文档（references）\s*\|\s*(\d+)",
             len([p for p in (ROOT / "references").glob("*.md") if p.name != "README.md"])),
        ):
            m = re.search(pat, text)
            if not m:
                err(f"索引面：INDEX.md 数据统计缺「{label}」行")
            elif int(m.group(1)) != actual:
                err(f"索引面：INDEX.md「{label}」写 {m.group(1)}，实测 {actual}")


# ---------- 安慰的立场·不端方案·禁问·回访（2026-10-02 两条口播材料对照出的四处空白）----------
# 这四条都是「说得出也数得清」的：条款在不在、同句绑定断没断、运行时镜像跟没跟。
# 「站得够不够真诚」机器判不了，留给逐轮端到端稿。
STANCE_HEAD = "### 10 先站在她这边"
STANCE_PAIRS = (
    ("只用她自己用过的那几个字", "不加码"),
    ("和稀泥", "中立"),
    ("站她这边是站她的处境", "不是替她定罪"),
    # 2026-10-03 正文 3xf5j84ek8bvbqe「重要的是对的人而不是技巧」（279 万播放）：
    # 不许劝她把「他为什么这样对我」想通，也不许拿一套解释把她糊弄过去。
    ("不劝她去把原因想明白", "你不是那种人，所以你不需要懂他"),
    # 同一条视频：技巧是末位，人才是前提——不是谦辞，是顺序。
    ("技巧是末位，人才是前提", "没有「我应该更会安慰」这回事"),
)
STANCE_RUNTIME_PAIRS = (
    ("只用她自己用过的字", "不加码"),
    ("和稀泥", "中立"),
    ("你不是那种人，所以你不需要懂他", "和稀泥不算中立"),
)
NO_SOLUTION_MARK = "她没开口要办法"
SILENCE_MARKS = ("一个问题都别问", "我不催")
SELF_PITY_BANNED = ("我嘴笨", "我比你更糟", "谁不是这么过来的")
# 空洞安慰（第 7 条）：只说通用句、接不上她说过的任何一件事。
# 进了 BANNED_COMFORT 才有 examples/ 门禁；这里守的是第 7 条有没有把这条禁令写出来。
EMPTY_COMFORT_MARKS = ("空洞安慰", "把人往外推")
EMPTY_COMFORT_WORDS = ("没事的", "会过去的", "别想太多")
RATIO_MARKS = ("陪伴占七成", "倾听两成", "技巧一成")
# 「技巧是末位，人才是前提」在定位页（guides/00）的落点：她信不认我，决定技巧有没有用
TRUST_FIRST_MARKS = ("技巧排最后", "她认不认我")
FOLLOWUP_HEAD = "## 事后那一次（回访）"
# 同意那一轮问完就止：存取回执不进收口那条（真实宿主 2026-10-02 22:49 截图照出）
CONSENT_ONCE_MARKS = ("问完就止", "只说这一轮一次", "收口那句话只说她的")
# 五条作品标题落地的口径（2026-10-03 00:25）：各配一对同句绑定，拆开写等于没写
TITLE_FIVE_MARKS = (
    # 2026-10-03 取到正文后核对，那三条视频讲的不是这件事（「情绪垃圾桶」＝择友五类；
    # 「每一次」＝性教育与避孕；「反复咀嚼痛苦」＝爱而不得），曾整条撤下。
    # 「情绪垃圾桶」这一条其后经产品判断**加回**，但落点与性质都变了：不再引那支视频，
    # 而是本 Skill 自己的定位判断，写在 `guides/00`「我们是什么」段。
    ("情绪垃圾桶", "不是她朋友的替代品"),        # 我不是她的替代品，也不当那个桶
    ("不是她朋友的替代品", "有限的"),           # 有限的、她愿意开口时才在
    ("可信度是攒出来的", "不是承诺出来的"),    # T2 有正文：不承诺主动联系
    ("不用力", "该在的时候要在"),              # T4 有正文：真诚、别分析别人
)
FOLLOWUP_MARKS = ("不带目的的轻触", "上次留下的锚", "不空问「最近怎么样」",
                  "只递一次", "她不来，我发不出去")


def check_comfort_stance() -> None:
    """安慰的立场与回访：内核写了，运行时也得在；同句绑定不许拆成两行。

    四处空白各配一道绑定：没要方案不许端方案、她哭那一轮不许提问、站她这边不许加码、
    隔天那一次落在跨会话那一页。禁句词表与第 7 条必须同改——只写规范不进 BANNED_COMFORT，
    examples/ 里的比惨句就没人抓。
    """
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return
    stext = read(skill)
    slines = stext.splitlines()
    if STANCE_HEAD not in stext:
        err(f"SKILL.md 缺「{STANCE_HEAD}」一节——站队口径没有落点，第 3 条就只剩禁令")
    broken = ["「%s」＋「%s」" % (a, b) for a, b in STANCE_PAIRS
              if not any(a in ln and b in ln for ln in slines)]
    if broken:
        err("SKILL.md 立场同句绑定断裂：" + "、".join(broken) + "——拆开写就等于这条没写")
    if NO_SOLUTION_MARK not in stext:
        err("SKILL.md 第 2 条未扩到第一轮之后：缺「%s」＝她讲事情经过会被当成征求主意" % NO_SOLUTION_MARK)
    absent = [m for m in SILENCE_MARKS if m not in stext]
    if absent:
        err("SKILL.md 缺她哭到说不下去那一轮的禁问口径：%s" % absent)
    absent = [w for w in SELF_PITY_BANNED if w not in stext]
    if absent:
        err("SKILL.md 第 7 条未列自我贬低与比惨：%s" % absent)
    notab = [w for w in SELF_PITY_BANNED if w not in BANNED_COMFORT]
    if notab:
        err("BANNED_COMFORT 与第 7 条脱节：%s 未进词表——examples/ 里的比惨句没人抓" % notab)
    # 空洞安慰：第 7 条须写出禁令，且词表须跟上（正文 3xf5j84ek8bvbqe）
    absent = [m for m in EMPTY_COMFORT_MARKS if m not in stext]
    if absent:
        err("SKILL.md 第 7 条缺空洞安慰禁令：%s——只说「没事的」这种通用句，"
            "接不上她说过的任何一件事，是把人往外推" % absent)
    notab = [w for w in EMPTY_COMFORT_WORDS if w not in BANNED_COMFORT]
    if notab:
        err("BANNED_COMFORT 与第 7 条脱节：%s 未进词表——examples/ 里的空洞安慰没人抓" % notab)

    # 15 条逐字稿（2026-10-03 凌晨）：五条新口径 ＋ 三条「不吸」的禁令
    ASR_FIVE = (
        ("SKILL.md", "细节要有颗粒度", "换成一个动作或一个瞬间"),   # C 具体到动作/感官
        ("SKILL.md", "被质问时不自证", "在场要给足"),      # A 不自证但在场
        # A 的第三种情形：她转述别人对她施压式的质问（创伤知情最高频入口，原视频主场景）
        ("SKILL.md", "她转述别人", "答了就是替她答"),
        # 第 10 条：她先给自己降格时顶回去（认她此刻的分量，不认她自封的位次）
        ("SKILL.md", "她先给自己降格时，要把它顶回去", "别人心里那把尺子就歪了"),
        ("SKILL.md", "我认的是她此刻的分量", "不是她替自己定的位次"),
        ("SKILL.md", "峰值过去，换挡要有信号", "不追着问细节"),    # D 换挡信号
        ("SKILL.md", "减法多于加法", "不追问、不劝、不升级"),
        # 「不追问」的现成手法：把她话里那个词接住、往下问半步
        ("SKILL.md", "把她话里的那个词接住", "不劝、不出谋"),
        # 关系淡了先认当初那半句是真的，先接住再松动
        ("SKILL.md", "先认当初那半句是真的", "先接住，再松动"),
        ("guides/22-中圈关系.md", "找交集，不打探", "她没提家里的事，我不挖"),
    )
    ASR_REFUSE = (
        ("倾诉＝心智不成熟", "绝不拿来对她说"),                      # 只作自检
        ("课题分离／你得先顾好自己", "自己已经说出想抽身"),         # 有条件才接
        ("不涉及利益就不反驳", "和稀泥不算中立"),                    # 与第 10 条相撞
    )
    g24 = ROOT / "guides" / "24-人物档案与判断.md"
    if not g24.is_file():
        err("缺 guides/24——三条「不吸」的口径没有归档处")
    else:
        t24 = read(g24)
        if "看着有用、其实不能吸" not in t24:
            err("guides/24 缺「三条外部材料里看着有用、其实不能吸」一节"
                "——下次看见同类主张会误吸")
        for a, b in ASR_REFUSE:
            if not any(a in ln and b in ln for ln in t24.splitlines()):
                err("guides/24 禁令拆散了：「%s」＋「%s」须在同一句" % (a, b))
    for rel_, a, b in ASR_FIVE:
        fp = ROOT / rel_
        if not fp.is_file():
            err("缺 %s——15 条逐字稿落地的口径无处可查" % rel_)
            continue
        if not any(a in ln and b in ln for ln in read(fp).splitlines()):
            err("%s 缺同句绑定「%s」＋「%s」——拆开写就等于这条没写" % (rel_, a, b))

    # 五条作品标题落地的口径：取到正文后核对，T1／T3／T5 依据不成立已撤（见 TITLE_FIVE_MARKS 注释），
    # 只剩两条有正文支撑的仍在守
    five = {
        "guides/00-欢迎与定位.md": (("情绪垃圾桶", "不是她朋友的替代品"),
                              ("不是她朋友的替代品", "有限的"),
                              ("可信度是攒出来的", "不是承诺出来的")),
        "guides/22-中圈关系.md": (("不用力", "该在的时候要在"),),
    }
    for rel, pairs in five.items():
        fp = ROOT / rel
        if not fp.is_file():
            err("缺 %s——作品标题落地的口径无处可查" % rel)
            continue
        flines = read(fp).splitlines()
        for a, b in pairs:
            if not any(a in ln and b in ln for ln in flines):
                err("%s 缺同句绑定「%s」＋「%s」——拆开写就等于这条没写" % (rel, a, b))

    ypath = ROOT / "agents" / "openai.yaml"
    ytext = read(ypath) if ypath.is_file() else ""
    # 与 check_runtime_mirror 同口径：夹具与旧版没有口吻小节时跳过，不虚报也不漏报成 error
    if ytext and RUNTIME_TONE_HEAD in ytext:
        ylines = ytext.splitlines()
        ybroken = ["「%s」＋「%s」" % (a, b) for a, b in STANCE_RUNTIME_PAIRS
                   if not any(a in ln and b in ln for ln in ylines)]
        if ybroken:
            err("agents/openai.yaml 立场条款未落地：" + "、".join(ybroken)
                + "（运行时读不到＝日常陪伴里只剩禁令）")
        for m in (NO_SOLUTION_MARK, "一个问题都别问", "我嘴笨"):
            if m not in ytext:
                err("agents/openai.yaml 缺「%s」——内核写了，运行时侧没跟" % m)

    g00 = ROOT / "guides" / "00-欢迎与定位.md"
    if g00.is_file():
        if not any(all(m in ln for m in RATIO_MARKS) for ln in read(g00).splitlines()):
            err("guides/00 缺同句定锚 %s——三七一没写在一句里，定位就还是按流程排" % list(RATIO_MARKS))
        g00lines = read(g00).splitlines()
        if not any(all(m in ln for m in TRUST_FIRST_MARKS) for ln in g00lines):
            err("guides/00 缺同句绑定 %s——三七一只写了次序，没写「技巧是给已经信我的人用的」，"
                "读起来仍像一份可以照着练的安慰技术清单" % list(TRUST_FIRST_MARKS))

    g02 = ROOT / MEMORY_GUIDE
    if g02.is_file():
        t = read(g02)
        absent = [m for m in CONSENT_ONCE_MARKS if m not in t]
        if absent:
            err("guides/02 缺「问完就止」：%s——真实宿主把同意与「记好了，就落在"
                "这台电脑上…」合进同一条回复，收口那一轮变成了存取回执" % absent)
        if FOLLOWUP_HEAD not in t:
            err("guides/02 缺「%s」一节——当场接住之外没有隔天那一下" % FOLLOWUP_HEAD)
        else:
            absent = [m for m in FOLLOWUP_MARKS if m not in t]
            if absent:
                err("guides/02 回访口径不全：%s（缺「她不来，我发不出去」＝把回访写成主动联系，"
                    "是兜不住的承诺）" % absent)
            # 改设计后的不变式（2026-10-02 真实宿主实测：收口轮只落了告别与同意，零个锚）：
            # 锚在**写档**那一轮顺手挑，不许再退回「收口那一轮留一个轻触」——那一轮归记忆同意。
            sec = t.split(FOLLOWUP_HEAD, 1)[1].split("\n## ", 1)[0]
            if "写档那一轮" not in sec:
                err("guides/02 回访锚没钉在写档那一轮——实测收口那一轮已被记忆同意占满，"
                    "锚落在那里必然落空（须写明「写档那一轮」顺手挑一句当锚）")
            if "收口那一轮留一个" in sec or "收口留一个" in sec:
                err("guides/02 又把回访锚派回收口那一轮——那一轮在提记忆同意，一轮一问塞不下第二个")
            # profile.md 模板须真的有这一行字段，否则「记进档案」无处可记（K5）
            if "上次留下的锚" not in t.split("## 先取得同意", 1)[0]:
                err("guides/02 的 profile.md 模板没有「上次留下的锚」这一行——"
                    "正文说记进档案、模板里没有，落点就悬空")


# 注册顺序＝`references/验证脚本说明.md`「检查项清单」的行序，类数也由这张表数出来
# （文档侧由 test_doc_rows_match_registration_order 逐条比对）。此前那个数是手抄的：
# `check_dimensions` 一直漏在表外，「15 类」错了三轮没有机器发现。
CHECKS = (
    check_skill_frontmatter,
    check_skill_budget,
    check_skill_structure,
    check_inventory,
    check_links,
    check_placeholders,
    check_forbidden_terms,
    check_bold_pollution,
    check_hotlines,
    check_tone_in_examples,
    check_memory_spec,
    check_person_judgment,
    check_decision_balance,
    check_runtime_mirror,
    check_books,
    check_dimensions,
    check_versions,
    check_manifest,
    check_card_schema,
    check_index_plane,
    check_comfort_stance,
    check_tag_namespace,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="仅输出失败项")
    args = ap.parse_args()

    for check in CHECKS:
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
