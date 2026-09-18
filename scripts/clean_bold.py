#!/usr/bin/env python3
"""清理「隔字加粗」格式污染（**本**文**档** 形态）。

策略：
  1. 逐行检测「污染特征」——连续 >=2 组 `**单字符**`。
  2. 命中特征的行，剥离该行全部 `**`（行内代码段、frontmatter、代码块受保护）。
  3. 输出残留报告：清洗后仍存在奇数个 `**` 的行，需人工复核。

用法：
    python scripts/clean_bold.py --dry-run   # 只报告
    python scripts/clean_bold.py --write     # 就地修复
    python scripts/clean_bold.py --check     # CI：存在污染即退出码 1
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
# 污染特征：连续 >=2 组「**单字符**」
SIGNATURE = re.compile(rf"\*\*(?:[^\s*]\*\*){{2,}}")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`[^`]*`")


def protected_flags(text: str) -> list[bool]:
    """标记受保护行：YAML frontmatter、围栏代码块。"""
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


def code_spans(line: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in INLINE.finditer(line)]


def inside(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in spans)


def clean_line(line: str) -> tuple[str, bool, bool]:
    """返回 (新行, 是否命中污染, 是否仍有残留)。"""
    spans = code_spans(line)
    hits = [m for m in SIGNATURE.finditer(line) if not inside(m.start(), spans)]
    if not hits:
        return line, False, False
    pieces, last = [], 0
    for a, b in spans:
        pieces.append(line[last:a].replace("**", ""))
        pieces.append(line[a:b])
        last = b
    pieces.append(line[last:].replace("**", ""))
    new = "".join(pieces)
    residual = new.count("**") % 2 == 1
    return new, True, residual


def iter_markdown() -> list[Path]:
    return [
        p for p in sorted(ROOT.rglob("*.md"))
        if not SKIP_DIRS & set(p.relative_to(ROOT).parts)
    ]


def scan(path: Path) -> tuple[str, str, int, list[tuple[int, str]]]:
    original = path.read_text(encoding="utf-8")
    flags = protected_flags(original)
    lines = original.split("\n")
    out, changed_lines, residual = [], 0, []
    for i, line in enumerate(lines):
        if flags[i]:
            out.append(line)
            continue
        new, hit, res = clean_line(line)
        if hit:
            changed_lines += 1
        if res:
            residual.append((i + 1, new))
        out.append(new)
    return original, "\n".join(out), changed_lines, residual


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    dirty, residual_total, residual_lines = [], 0, []
    for path in iter_markdown():
        original, new, n, residual = scan(path)
        if n == 0:
            continue
        rel = path.relative_to(ROOT)
        dirty.append(rel)
        residual_total += len(residual)
        for lineno, text in residual:
            residual_lines.append(f"{rel}:{lineno}: {text.strip()[:70]}")
        if args.check:
            print(f"POLLUTED: {rel}")
        elif args.write:
            path.write_text(new, encoding="utf-8")
            print(f"FIXED: {rel}  ({n} 行)")
        else:
            print(f"WOULD FIX: {rel}  ({n} 行)")

    print(f"\n[汇总] 污染文件 {len(dirty)} 个；需人工复核的残留行 {residual_total} 行。",
          file=sys.stderr)
    if residual_lines and not args.write:
        print("\n[残留行样例（前 15 条）]", file=sys.stderr)
        for r in residual_lines[:15]:
            print("  " + r, file=sys.stderr)
    if args.check and dirty:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
