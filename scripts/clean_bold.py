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
# 中文输出须可被 CI / 调用方按 UTF-8 解析：Windows 控制台默认 cp936 会破坏重定向内容
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
# 污染特征：连续 >=2 组「**单字符**」
SIGNATURE = re.compile(rf"\*\*(?:[^\s*]\*\*){{2,}}")
# 第二种形态：被双字词隔开的单字加粗（**不**替来访者**做**决定），SIGNATURE 看不见。
# 与 validate_skill.bold_polluted 同口径，改动须两处同步——否则校验判错而修正器不动。
SPAN = re.compile(r"\*\*(.+?)\*\*")
CJK_ONE = re.compile(rf"[{CJK}]")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`[^`]*`")


def polluted(line: str) -> bool:
    """两种污染形态取并集；只加粗单个拉丁字母（**P**sychoticism）属正常排版。"""
    if SIGNATURE.search(line):
        return True
    return sum(1 for m in SPAN.finditer(line)
               if len(m.group(1)) == 1 and CJK_ONE.fullmatch(m.group(1))) >= 2


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


def clean_line(line: str) -> tuple[str, bool, bool]:
    """返回 (新行, 是否命中污染, 是否仍有残留)。"""
    spans = code_spans(line)
    masked = line
    for a, b in reversed(spans):        # 代码段用中性字符遮住，避免与 ** 拼出假阳性
        masked = masked[:a] + "q" * (b - a) + masked[b:]
    if not polluted(masked):
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
