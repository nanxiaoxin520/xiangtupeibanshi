#!/usr/bin/env python3
"""热线信息批量修正（安全关键）。

修正项：
  1. `12356-5`            → `12356`（国家卫健委 2024-12 设置的全国统一号码，无后缀）
  2. `（2022 新设）`       → 删除（实际为 2024-12 设置、2025-05-01 前开通）
  3. `生命热线`            → `Lifeline Shanghai`（并标注英语服务）
  4. `400-821-1215` 旁的 `24h` → `10:00–22:00`（该热线非 24 小时）

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
SKIP_PARTS = {".git", "node_modules", "__pycache__", "_plan", "backups"}
# 变更日志需保留历史错误写法作为修复记录，不予改写
SKIP_FILES = {"CHANGELOG.md"}

RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"12356-5"), "12356", "号码后缀错误"),
    (re.compile(r"（2022\s*新设）"), "", "年份错误"),
    (re.compile(r"\(2022\s*新设\)"), "", "年份错误"),
    (re.compile(r"生命热线"), "Lifeline Shanghai", "名称错误"),
)

# 400-821-1215：把**紧跟该号码**的 24h 表述改为真实服务时间
LIMITED = "400-821-1215"
H24 = re.compile(r"（?\s*24\s*h\s*）?", re.IGNORECASE)
NEAR = 40  # 号码与 24h 之间的最大字符距离


def fix_limited_line(line: str) -> tuple[str, bool]:
    """仅替换与该号码邻近的 24h，避免误改同行其他号码的服务时间。"""
    if LIMITED not in line:
        return line, False
    out, last, changed = [], 0, False
    for m in H24.finditer(line):
        if LIMITED not in line[max(0, m.start() - NEAR):m.start()]:
            continue
        out.append(line[last:m.start()])
        out.append("（10:00–22:00）")
        last = m.end()
        changed = True
    if not changed:
        return line, False
    out.append(line[last:])
    return "".join(out), True


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
    notes: list[str] = []
    for pattern, repl, label in RULES:
        new, n = pattern.subn(repl, text)
        if n:
            notes.append(f"{label} x{n}")
            text = new
    lines = text.split("\n")
    for i, line in enumerate(lines):
        new, changed = fix_limited_line(line)
        if changed:
            lines[i] = new
            notes.append(f"服务时间修正 @line {i + 1}")
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
