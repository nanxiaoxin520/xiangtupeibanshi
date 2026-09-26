#!/usr/bin/env python3
"""热线信息批量修正（安全关键）。

修正项（与 validate_skill.check_hotlines 保持同口径）：
  1. `12356-数字`          → `12356`（全国统一号码无后缀；整段吞掉后缀，不留新错号）
  2. `2022 新设`            → `2024-12 设置`（实际由国家卫健委 2024-12 设置）
  3. `生命热线`             → `Lifeline Shanghai`（仅当同一行提到 400-821-1215；
                            「…干预中心生命热线」属另一家机构名，不改）
  4. `400-821-1215` 邻近的 `24h` / `24 小时` → `10:00–22:00`（该线英语服务、非全天候）

frontmatter、围栏代码块、行内代码段均受保护——规则示例常以行内代码书写，
改写它们会把「禁止 `12356-5`」变成「禁止 `12356`」。

用法：
    python scripts/fix_hotlines.py --dry-run
    python scripts/fix_hotlines.py --write
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
SKIP_PARTS = {".git", "node_modules", "__pycache__", "_plan", "backups"}
# 变更日志需保留历史错误写法作为修复记录，不予改写
SKIP_FILES = {"CHANGELOG.md"}

RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    # 整段吃掉 -数字 后缀；只删 "-5" 会把 12356-55 变成 123565（新的错号且校验器不再报）
    (re.compile(r"12356-\d+"), "12356", "号码后缀错误"),
    # 更正年份而非删除：无括号的「2022 新设」也要能修，否则校验判错却无从修正
    (re.compile(r"2022\s*新设"), "2024-12 设置", "年份错误"),
)

# 400-821-1215：把与该号码邻近的 24h / 24 小时 表述改为真实服务时间，
# 并更正其误称。三处口径（H24 / NEGATION / NEAR / 误称豁免）必须与
# validate_skill.check_hotlines 一致，否则「校验判错」与「修正器改写」会脱节。
LIMITED = "400-821-1215"
H24 = re.compile(r"(?P<open>（)?\s*24\s*(?:h|小时)\s*(?P<close>）)?", re.IGNORECASE)
NEGATION = re.compile(r"(?:非|不是|不再|未|不)\s*(?:提供|含)?\s*$")
NEAR = 40  # 号码与 24 小时表述之间的最大字符距离
MISNOMER = re.compile(r"(?<!中心)生命热线")  # 「…干预中心生命热线」是另一家机构名
REAL_HOURS = "10:00–22:00"
REAL_NAME = "Lifeline Shanghai"
INLINE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(```|~~~)")


def protected_flags(text: str) -> list[bool]:
    """标记受保护行：YAML frontmatter、围栏代码块（与 clean_bold 同语义）。"""
    lines = text.split("\n")
    flags = [False] * len(lines)
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            flags[i] = True
            if lines[i].strip() == "---":
                break
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            flags[i] = True
            in_fence = not in_fence
            continue
        if in_fence:
            flags[i] = True
    return flags


def blank_code(line: str) -> str:
    """把行内代码段替换为等长空格。

    长度不变，故在「掩码」上算出的位置可直接用于原行：既复刻了校验器
    「先剥离行内代码再判定」的口径，又能把替换精确落回原位。
    """
    return INLINE.sub(lambda m: " " * (m.end() - m.start()), line)


def fix_line(line: str) -> tuple[str, list[str]]:
    """修正一行，返回 (新行, 说明列表)。

    行内代码段不参与：里面的 `12356-5` 常常就是规则示例本身，曾因此把
    「禁止 `12356-5`」改写成「禁止 `12356`」，语义反转且校验器不再报错。
    """
    mask = blank_code(line)
    notes: list[str] = []
    edits: list[tuple[int, int, str]] = []

    for pattern, repl, label in RULES:
        for m in pattern.finditer(line):
            if mask[m.start():m.end()] != m.group(0):
                continue  # 落在行内代码段内
            edits.append((m.start(), m.end(), repl))
            notes.append(label)

    if LIMITED in mask:
        for m in MISNOMER.finditer(mask):
            edits.append((m.start(), m.end(), REAL_NAME))
            notes.append("名称错误")
        for m in H24.finditer(mask):
            if LIMITED not in mask[max(0, m.start() - NEAR):m.end() + 10]:
                continue
            if NEGATION.search(mask[max(0, m.start() - 8):m.start()]):
                continue  # 「非 24 小时」是正确表述
            # 原文带括号才补括号，避免在散文里插出一对孤立括号；
            # 前导空白一并保留，否则「提供 24 小时」会被粘成「提供10:00–22:00」
            lead = m.group(0)[:len(m.group(0)) - len(m.group(0).lstrip())]
            has_paren = bool(m.group("open") and m.group("close"))
            repl = lead + (f"（{REAL_HOURS}）" if has_paren else REAL_HOURS)
            edits.append((m.start(), m.end(), repl))
            notes.append("服务时间修正")

    if not edits:
        return line, []
    out, pos = [], 0
    for start, end, repl in sorted(edits):
        if start < pos:
            continue  # 罕见重叠时保留先前编辑，避免错位
        out.append(line[pos:start])
        out.append(repl)
        pos = end
    out.append(line[pos:])
    return "".join(out), notes


def iter_files() -> list[Path]:
    out: list[Path] = []
    for pat in ("*.md", "*.yaml", "*.yml"):
        for p in ROOT.rglob(pat):
            if SKIP_PARTS & set(p.relative_to(ROOT).parts):
                continue
            if str(p.relative_to(ROOT)) in SKIP_FILES:
                continue
            out.append(p)
    return sorted(set(out))


def fix_text(text: str) -> tuple[str, list[str]]:
    """逐行修正；frontmatter 与围栏代码块整块受保护，行内代码段受保护。"""
    lines = text.split("\n")
    flags = protected_flags(text)
    notes: list[str] = []
    for i, line in enumerate(lines):
        if flags[i]:
            continue
        new, line_notes = fix_line(line)
        for label in line_notes:
            notes.append(f"{label} @line {i + 1}")
        lines[i] = new
    return "\n".join(lines), notes


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--write", action="store_true")
    args = ap.parse_args()

    touched = 0
    for path in iter_files():
        original = path.read_text(encoding="utf-8")
        new, notes = fix_text(original)
        if new == original:
            continue
        touched += 1
        rel = path.relative_to(ROOT)
        print(f"{'FIXED' if args.write else 'WOULD FIX'}: {rel}  [{'; '.join(notes)}]")
        if args.write:
            path.write_text(new, encoding="utf-8")

    print(f"\n合计 {touched} 个文件需要修正。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
