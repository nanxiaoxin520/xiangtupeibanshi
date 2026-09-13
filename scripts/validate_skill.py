#!/usr/bin/env python3
"""Validate the xiangtupeibanshi skill."""

from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
SKILL_MAX_LINES = 200
SKILL_MAX_CHARACTERS = 8_000
SKILL_MAX_APPROX_TOKENS = 7_000

REQUIRED_GUIDES = (
    "00-欢迎与定位.md",
    "01-第一次对话.md",
    "10-情绪识别与命名.md",
    "11-认知重构.md",
    "12-CBT核心技能.md",
    "13-正念与接纳.md",
    "20-内圈关系.md",
    "21-差序格局与家庭.md",
    "40-危机识别.md",
    "60-中国心理学会7大原则.md",
    "70-关系伤害分析.md",
    "71-关系冲突5场景.md",
)


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        ERRORS.append(f"missing required path: {path}")
    return target


def validate_frontmatter() -> None:
    skill = require("SKILL.md")
    if not skill.is_file():
        return
    content = skill.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        ERRORS.append("SKILL.md has invalid YAML frontmatter")
        return
    frontmatter = match.group(1)
    keys = re.findall(r"^([A-Za-z0-9_-]+):", frontmatter, re.MULTILINE)
    if keys != ["name", "description"]:
        ERRORS.append(f"frontmatter keys must be name, description; got {keys}")
    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else ""
    if name not in ("xinli-zhushou", "xiangtupeibanshi") or not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        ERRORS.append(f"invalid skill name: {name!r}")


def approximate_token_count(content: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    latin_words = len(re.findall(r"[A-Za-z0-9_]+", content))
    other = len(re.findall(r"[^\sA-Za-z0-9_\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    return cjk + int(latin_words * 1.3) + int(other / 4)


def validate_skill_budget() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return
    content = skill.read_text(encoding="utf-8")
    lines = content.splitlines()
    if len(lines) > SKILL_MAX_LINES:
        ERRORS.append(f"SKILL.md exceeds {SKILL_MAX_LINES} lines: {len(lines)}")
    if len(content) > SKILL_MAX_CHARACTERS:
        ERRORS.append(f"SKILL.md exceeds {SKILL_MAX_CHARACTERS} chars: {len(content)}")
    if approximate_token_count(content) > SKILL_MAX_APPROX_TOKENS:
        ERRORS.append(f"SKILL.md token budget exceeded")


def validate_inventory() -> None:
    require("agents/openai.yaml")
    for filename in REQUIRED_GUIDES:
        require(f"guides/{filename}")


def validate_broken_links() -> None:
    link_pattern = re.compile(r"\]\(([^)]+)\)")
    for markdown in ROOT.rglob("*.md"):
        if ".git" in str(markdown):
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:)", target):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                ERRORS.append(
                    f"broken local link in {markdown.relative_to(ROOT)}: {raw_target}"
                )


def validate_placeholders() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "[" + "TODO" in text:
            ERRORS.append(f"template placeholder in {path.relative_to(ROOT)}")


def validate_no_goutoujunshi_residue() -> None:
    """Ensure no goutoujunshi-related terms remain (except in historical context)."""
    forbidden = ["goutoujunshi", "狗头军师", "shengjidaguai", "中国语境心理治疗师"]
    # Allow historical mentions in CHANGELOG, README history, CONTRIBUTING
    allow_list = ["CHANGELOG.md", "CONTRIBUTING.md", "README.md"]
    for path in ROOT.rglob("*.md"):
        if ".git" in str(path):
            continue
        rel = str(path.relative_to(ROOT))
        if any(a in rel for a in allow_list):
            continue
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                ERRORS.append(f"goutoujunshi residue in {path.relative_to(ROOT)}: {term}")


def main() -> int:
    validate_frontmatter()
    validate_skill_budget()
    validate_inventory()
    validate_broken_links()
    validate_placeholders()
    validate_no_goutoujunshi_residue()
    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}")
        return 1
    print("xiangtupeibanshi validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
