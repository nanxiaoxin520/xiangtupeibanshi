#!/usr/bin/env python3
"""乡土陪伴师白盒测试套件。

覆盖范围：
  A. validate_skill.py 的全部检查项——每类均验证「通过」与「失败」分支
     （项数不写在这里：由 `CHECKS` 与 `references/验证脚本说明.md` 逐条比对）
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

本文件是行为内核。新对话开口前，先静默读本机档案。

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
| 5 行动 | 摊开两头的代价（见 `guides/12-CBT核心技能.md`），再一个小行动 |

### 10 先站在她这边

附和她骂那个人只用她自己用过的那几个字，不加码。和稀泥不算中立。站她这边是站她的处境，不是替她定罪别人。
她没开口要办法，往后的轮次同样不许端方案。那一个问题都别问，我不催你。
我嘴笨、我比你更糟、谁不是这么过来的，一律禁用。

## 细节与颗粒度

**细节要有颗粒度**：能换成一个动作或一个瞬间的，就不要留成形容词。

## 峰值与换挡

**峰值过去，换挡要有信号**：不追着问细节。
**被质问时不自证**：在场要给足。
**她转述别人**对她施压式的质问时，**答了就是替她答**。
**她先给自己降格时，要把它顶回去**——别人心里那把尺子就歪了；我认的是她此刻的分量，不是她替自己定的位次。
**把她话里的那个词接住**、往下问半步，不劝、不出谋。
关系淡了**先认当初那半句是真的**：**先接住，再松动**。
**减法多于加法**：不追问、不劝、不升级。
她没问「他为什么这样」，**不劝她去把原因想明白**——**你不是那种人，所以你不需要懂他**；和稀泥不算中立。
**技巧是末位，人才是前提**：**没有「我应该更会安慰」这回事**，只有她认不认我。
禁**空洞安慰**：只说通用句接不上她说过的任何一件事，那是**把人往外推**。

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
| 跨会话记忆 | `guides/02-长期记忆.md` |
| 人物判断 | `guides/24-人物档案与判断.md` |

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
    "00-欢迎与定位.md", "01-第一次对话.md", "02-长期记忆.md",
    "10-情绪识别与命名.md",
    "11-认知重构.md", "12-CBT核心技能.md", "13-正念与接纳.md",
    "20-内圈关系.md", "21-差序格局与家庭.md", "22-中圈关系.md",
    "23-工作议题.md", "24-人物档案与判断.md",
    "30-自我探索.md", "31-意义议题.md",
    "40-危机识别.md", "41-资源连接.md", "50-自我照护.md",
    "60-中国心理学会7大原则.md", "70-关系伤害分析.md",
    "71-关系冲突5场景.md", "99-测试模式.md",
)

# 合规的长期记忆指南：三条硬账 + 两层同意默认不开 + 云端降档 + 四条口令齐
MEMORY_GUIDE_OK = (
    "# 长期记忆\n\n"
    "- **只写本地**\n- **不上传**\n- **不进 git**\n\n"
    "落点：`<HOME>/.xiangtupeibanshi/memory/profile.md`\n\n"
    "危机要点须**单独同意**，**默认不建**。\n\n"
    "## 一台电脑不止一个人\n\n档案头部一行**代号**，取她自己的称呼；"
    "换人对原档**不念、不引用、不改**，另建一份；改代号时文件名跟着改。\n\n"
    "## 别人来要呢\n\n第三人来要，我不念给任何人，也不确认有没有这份档案。\n\n"
    "她问对话会不会被留存、被拿去训练：那由宿主定，我不替它打保票。\n\n"
    "撤回后她又说记着我，算重新同意，从不追补已删的条目。\n\n"
    "## 记什么\n\n那个人那一行：关系词／她的说法／她的评分／她的类型标签／现实事件。\n\n"
    "我给谁的定性都不落档，只照她的话记她自己下的判断。我推出来的类型倾向同样不落档。她说以后都别给她推类型，这类长期停照原话记进忌讳。\n\n"
    "云端宿主降档：只记零隐私骨架。\n\n"
    "### 查看\n\n原样念给她\n\n### 暂停\n\n停写停召回\n\n"
    "### 撤销\n\n删她指的那条\n\n### 清空\n\n确认后删档\n"
)

# 合规的人物判断指南：五路进料 + 三层 + 判断句三要求 + 分级 + 拒判 + 不诊断 + 时机 + 危机让路
JUDGMENT_GUIDE_OK = (
    "# 人物档案与判断\n\n"
    "护栏：第一轮只做接住，判断排在其后；命中危险信号先走 `guides/40-危机识别.md`。\n"
    "护栏：出口只准**你／我二人称**，不许用旁观者口吻评述她的生活；且**只说她说过的事**，她没讲的不补。\n\n"
    "## 五路进料\n\n人物信息／类型标签／她的评分／现实事件／她自己的行为。\n\n"
    "## 三层\n\n事实层、解释层（给互相竞争的解释）、判断层。\n\n"
    "判断句须带把握度，并说什么情况下要改口；改口条件写不出来就不算判断。\n\n"
    "## 判到哪一层\n\n第 1 层判行为与处境；第 2 层给人定性，"
    "只在她自己明确要这一句时，且标成推测。\n\n"
    "## 证据不足\n\n只剩标签和分数时，直说不足以下判断；"
    "不许用 MBTI 补事实的空缺。\n\n"
    "不用诊断词——本 Skill 不诊断。\n\n"
    "## 推类型：默认在推，不主动说\n\n推，默认开着；说，要她先开口——她没问，话里不出现「型」这类字样；也不主动询问她或那个人是什么型，不把话头往「你们什么 MBTI」上引。\n\n"
    "给她本人推时落点只有她还能挪哪一步：只从她说出的现实事件推，不拿推断替她做决定；不替她贴四字标签，不替她总结品格。\n\n"
    "新事撞上改口条件就当场改口；没有新事不重复——重复不是跟进。\n\n"
    "说出口那轮**过程不出口**：依据几件、把握高低、什么情况改口齐在后台就算清过，念出来就成了**报流程**；"
    "她逼要字母时**连「我不给」都不出口，也不给替代的检索词**——那两样都是把类型再摆一遍；"
    "出口**至多两句、整条不超 60 字**，一句给结论，一句把话头交回给她，先接她那句也算在内。\n\n"
    "但**短是省字，不是削薄**她的处境，也别轮轮拿同一句反问交差。\n\n"
    "定稿四条：他哪件事落在你眼里了，让你觉得他像那样？"
    "这例我判断不了，我硬凑不了一个人格给你。要不你把关于他的事说给我听听，让我猜猜他的人格。"
    "我只能推测他像是看不见你的难受，不是存心晾你。还有哪回你也这样一个人扛着？"
    "你想从哪件跟他开口？\n\n"
    "停嘴这场之后本场不再自行重启；她说明白以后都别推，那是**停推**，记进忌讳、跨会话生效。\n\n"
    "命中危险信号那一轮既不说也不推，先做安全评估。\n"
    "## 三条外部材料里看着有用、其实不能吸\n\n"
    "- **倾诉＝心智不成熟**：只作陪伴者自检，**绝不拿来对她说**。\n"
    "- **课题分离／你得先顾好自己**：只在她**自己已经说出想抽身**时才可接。\n"
    "- **不涉及利益就不反驳**：与第 10 条**和稀泥不算中立**正面相撞。\n"
)

MEMORY_T99_OK = "# 测试模式\n\n测试模式不写不读长期记忆档案。\n"

# 合规的权衡资料段：内核第 5 步路由过来，两道护栏与危机例外齐
DECISION_GUIDE_OK = (
    "# CBT 核心技能\n\n## 摊开两头的代价（行动前的权衡）\n\n"
    "两道护栏：**不进第一轮**（第一轮只做接住）；摊完**不替她选**，也不暗示哪头更体面，"
    "落点只问一句。"
    "她逼要结论时**先摊账，再说不替她选**。\n\n"
    "命中家暴、控制、自伤时不摊利弊，先按 `guides/40-危机识别.md` 做**安全评估**。\n"
)


def _card_ok() -> str:
    """合规档案卡：13 个骨架节（顺序取自 `VS.CARD_SKELETON`）+ 自由带一节 + 目录逐条对齐。

    骨架从校验器常量派生，避免夹具与口径各改各的。
    """
    heads: list[str] = []
    for h in VS.CARD_SKELETON:
        if h == "目录":
            continue
        if h == "核心问题":
            heads.append("核心内容")          # 自由带：位于「真实学术信息」与「核心问题」之间
        heads.append(h)
    toc = "\n".join("- [[#%s]]" % h for h in heads)
    body = "\n\n".join("## %s\n\n内容" % h for h in heads)
    return (
        "---\ntitle: 《乡土中国》\nauthor: 费孝通\ntype: sociology\n"
        "domain: 文化与社会\naudience: 进阶\napproach: 本土整合\n"
        "culture: 中国本土\nevidence: C\n"
        "tags: [板块/文化与社会, 读者/进阶, 取向/本土整合, 文化圈/中国本土, 主题/关系]\n---\n\n"
        "# 《乡土中国》\n\n## 目录\n\n" + toc + "\n\n" + body + "\n"
    )


CARD_OK = _card_ok()


def make_fixture(base: Path) -> Path:
    """构造一个可通过全部 21 类检查的最小仓库。"""
    def w(rel: str, text: str = "内容\n") -> None:
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    w("SKILL.md", SKILL_OK)
    w("VERSION", "0.1.1")
    w("CHANGELOG.md", "# 更新日志\n\n## [0.1.1] - 2026-09-18\n\n- 初版\n")
    w("LICENSE", "MIT License\n\nCopyright (c) 2026 xiangtupeibanshi contributors\n")
    w("NOTICE.md", "# 内容引用与版权说明\n\n代码适用 MIT；书籍整理与二手诠释不在授权范围内。\n")
    w("README.md",
      "# 乡土陪伴师\n\n"
      "```\n"
      "├── guides/                     # %d 篇操作指南\n"
      "└── scripts/\n"
      "    └── validate_skill.py       # %d 类内容校验\n"
      "```\n\n"
      "# Hometown Companion\n\n"
      "```\n"
      "├── guides/                     # %d operational guides\n"
      "└── scripts/\n"
      "    └── validate_skill.py       # %d categories of content validation\n"
      "```\n"
      % (len(REQUIRED_GUIDE_NAMES), len(VS.CHECKS),
         len(REQUIRED_GUIDE_NAMES), len(VS.CHECKS)))
    w("SECURITY.md", "# 安全\n")
    w("CONTRIBUTING.md", "# 贡献\n")
    w("agents/openai.yaml", "interface:\n  display_name: 乡土陪伴师\n")
    w("guides/README.md",
      "# Guides 导航\n\n" + "\n".join("- %s" % n for n in REQUIRED_GUIDE_NAMES) + "\n")
    for name in REQUIRED_GUIDE_NAMES:
        w(f"guides/{name}")
    w("guides/00-欢迎与定位.md",
      "# 欢迎与定位\n\n**我不是她朋友的替代品，也不是那个「情绪垃圾桶」**：我是**有限的**、"
      "她愿意开口的那几次。\n\n"
      "**可信度是攒出来的，不是承诺出来的。**\n\n"
      "**陪伴占七成，倾听两成，技巧一成。**\n\n"
      "**技巧排最后**：技巧是给已经信我的人用的，只有**她认不认我**。\n\n"
           "## 能做什么\n\n清单。\n")
    w("guides/22-中圈关系.md",
      "# 中圈关系（朋友同事）\n\n## 一条定调：别太用力\n\n"
      "不用力不是冷漠——该在的时候要在。\n\n"
      "## 共同交集\n\n"
      "**找交集，不打探**：她没提家里的事，我不挖。\n")
    # 回访一节只在基线里追加，不动 MEMORY_GUIDE_OK 本体（A16 那批用例按它断言）
    w("guides/02-长期记忆.md", MEMORY_GUIDE_OK + (
        "\n## 事后那一次（回访）\n\n留一个**不带目的的轻触**；档案记「上次留下的锚」；"
        "第一句从锚接，不空问「最近怎么样」；只递一次；她不来，我发不出去。"
        "锚在写档那一轮顺手挑一句当锚，不落在收口那一轮（那一轮归记忆同意）。\n"
        "**问完就止**：存储位置和控制权只说这一轮一次，收口那句话只说她的。\n"
        "上次留下的锚（写档时顺手挑一句，没有就留空）\n"))
    # profile.md 模板里要有这一行字段，否则「记进档案」无处可记
    _g02 = (base / "guides/02-长期记忆.md").read_text(encoding="utf-8")
    if "上次留下的锚（写档时顺手挑一句" not in _g02.split("## 先取得同意", 1)[0]:
        _g02 = _g02.replace("# 我们走到哪儿\n",
                            "# 我们走到哪儿\n# 上次留下的锚（写档时顺手挑一句，没有就留空）\n", 1)
    w("guides/02-长期记忆.md", _g02)
    w("guides/24-人物档案与判断.md", JUDGMENT_GUIDE_OK)
    w("guides/99-测试模式.md", MEMORY_T99_OK)
    w("guides/12-CBT核心技能.md", DECISION_GUIDE_OK)
    w("references/README.md", "# References 索引\n\n热线与资源速查.md\n")
    w("references/热线与资源速查.md", CANONICAL_HOTLINE)
    w("documentation/README.md")
    # 权衡的落点问句放这儿：README 不计入 manifest 的 examples 数，免得动计数夹具
    w("examples/README.md", "# 示例导航\n\n> 这两笔账，你更付不起哪一笔？\n")
    w("scripts/validate_skill.py", "#!/usr/bin/env python3\n")
    w("docs/manifest.yaml",
      "version: 0.1.1\nskill_name: xiangtupeibanshi\n"
      "guides: 21\nexamples: 0\nreferences: 1\ndocumentation: 0\nbooks: 1\n")
    # 仓内词表事实源（check_tag_namespace 要求在场，且 §2 须与 DIM_VOCAB 逐字同口径）
    w("docs/tag-vocabulary.md",
      "# 标签命名空间事实源\n\n"
      "| 命名空间 | frontmatter 字段 | 取值数 | 受控词表 |\n|---|---|---|---|\n"
      + "".join(
          "| `%s/` | `%s` | %d | %s |\n" % (ns, key, len(VS.DIM_VOCAB[key]),
                                           " · ".join(sorted(VS.DIM_VOCAB[key])))
          for ns, key in VS.DIM_NS.items())
      + "\n| 自由标注 |\n"
      + "".join("| `%s/` |\n" % ns for ns in sorted(VS.FREE_NS)))
    w("_books/README.md")
    w("_books/《乡土中国》.md", CARD_OK)
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

    def test_split_single_char_bold_detected(self):
        """被双字词隔开的单字加粗（**不**替来访者**做**决定）：BOLD_SIGNATURE 看不见。"""
        self.write("guides/40-危机识别.md", "2. **不**替来访者**做**决定\n")
        self.assertErrors(VS.check_bold_pollution, "非相邻单字加粗", "加粗格式污染")

    def test_latin_initial_bold_exempt(self):
        """首字母强调（**P**sychoticism／**E**xtraversion）是正常排版，不判污染。"""
        self.write("_books/《人格心理学》.md",
                   "> （**P**sychoticism 精神质／**E**xtraversion 外向性／**N**euroticism 神经质）\n")
        self.assertClean(VS.check_bold_pollution, "拉丁首字母加粗")

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

    def test_heading_scoped_24h_detected(self):
        """小节标题声称 24h、号码写在下面的条目里：同行窗口看不到，须按小节判定。"""
        self.write("guides/70-关系伤害分析.md",
                   "### 立即危机热线（24h）\n- **010-82951332** 北京心理危机研究与干预中心\n"
                   "- **400-821-1215** Lifeline Shanghai\n")
        self.assertErrors(VS.check_hotlines, "小节标题 24h 下的限时号码", "列在小节")

    def test_heading_scoped_clean_when_in_limited_section(self):
        """号码挂在「时段受限」小节下，且本行写明服务时间与否定语。"""
        self.write("guides/71-关系冲突5场景.md",
                   "### 立即危机热线（24h）\n- **12356** 全国心理援助热线\n\n"
                   "### 时段受限\n- **400-821-1215** Lifeline Shanghai：10:00–22:00，非 24 小时\n")
        self.assertClean(VS.check_hotlines, "限时小节")

    def test_heading_scoped_skips_fenced_block(self):
        """围栏代码块内的示例目录树/清单不参与小节判定。"""
        self.write("guides/40-危机识别.md",
                   "### 立即危机热线（24h）\n\n```\n400-821-1215\n```\n")
        self.assertClean(VS.check_hotlines, "围栏内不参与小节判定")

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


class TestA14ToneRules(FixtureCase):
    """口吻门禁：一轮一问、不外泄内部路径、不端有毒鸡汤；反例引用须放行。"""

    def test_baseline_clean(self):
        self.assertClean(VS.check_tone_in_examples, "口吻基线")

    def test_multi_question_reply_detected(self):
        self.write("examples/9-测.md", "### 第 1 轮\n> 你吃饭了吗？今天过得怎么样？\n")
        self.assertErrors(VS.check_tone_in_examples, "一条回复两问", "一轮最多一问")

    def test_questions_split_across_turns_allowed(self):
        """拆成两轮各一问，正是第 4 条要求的形态。"""
        self.write("examples/9-测.md",
                   "### 第 1 轮\n> 你吃饭了吗？\n\n### 第 2 轮\n> 今天过得怎么样？\n")
        self.assertClean(VS.check_tone_in_examples, "逐轮单问")

    def test_internal_path_in_reply_detected(self):
        self.write("examples/9-测.md",
                   "### 第 1 轮\n> 根据 `_books/《非暴力沟通》.md` 的研究，这样表达更有效。\n")
        self.assertErrors(VS.check_tone_in_examples, "内部路径外泄", "内部路径")

    def test_banned_comfort_detected(self):
        self.write("examples/9-测.md", "### 第 1 轮\n> 别难过了，你已经很棒了。\n")
        self.assertErrors(VS.check_tone_in_examples, "有毒鸡汤", "端出有毒鸡汤")

    def test_banned_comfort_as_negative_example_allowed(self):
        """作为反例提及（不说「想开点」）不得判错，否则文档里写不了禁用清单。"""
        self.write("examples/9-测.md", "### 第 1 轮\n> 那先不说「想开点」这类话，你先喝半杯水。\n")
        self.assertClean(VS.check_tone_in_examples, "就近否定语境的禁句")

    def test_counter_example_heading_allowed(self):
        """「反面示范」小节的旧式整块回复是给模型看的错样，不参与门禁。"""
        self.write("examples/9-测.md",
                   "## 反面示范（不要模仿）\n> 别难过了。你吃饭了吗？今天过得怎么样？\n")
        self.assertClean(VS.check_tone_in_examples, "反面示范豁免")

    def test_leading_blockquote_metadata_allowed(self):
        """篇首「相关指南」导读块引用 guides 路径是文档元信息，不是发给用户的句子。"""
        self.write("examples/9-测.md",
                   "# 示例\n> **相关指南**：`guides/40-危机识别.md`（危机流程）。\n")
        self.assertClean(VS.check_tone_in_examples, "篇首导读豁免")

    def test_fenced_block_exempt(self):
        self.write("examples/9-测.md", "# 示例\n\n```\n你吃饭了吗？今天怎么样？\n```\n")
        self.assertClean(VS.check_tone_in_examples, "围栏代码块豁免")


class TestA15RuntimeMirror(FixtureCase):
    """运行时 system_prompt 与内核「说话方式」的镜像一致性（CLAUDE.md 已有约定，此处给门禁）。"""

    # 运行时侧的口吻段（含五批的人称／非编造条款），删段与开场白两处用例共用同一串，
    # 免得改了夹具文本就让「删段」用例的匹配目标落空（本次第一次跑就是这样假绿的）。
    TONE_BLOCK = ("  【说话方式（硬约束）】\n"
                  "  说明行。出口只准你／我二人称，不用旁观者口吻；只说她说过的事，她没讲的不补。\n"
                  "  - 1 首轮只做接住\n  - 2 一轮最多一个问题\n\n")
    KERNEL = ("---\nname: xiangtupeibanshi\ndescription: d\n---\n\n# 内核\n\n"
              "## 说话方式（硬约束）\n\n开篇声明。出口只准你／我二人称，不用旁观者口吻；"
              "只说她说过的事，她没讲的不补。\n\n"
              "### 1 首轮只接住\n\n内容。\n\n### 2 一轮最多一问\n\n内容。\n\n## 限制\n\n非医疗。\n")
    RUNTIME_OK = ("interface:\n  display_name: 乡土陪伴师\n\nsystem_prompt: |\n"
                  "  你是乡伴。\n\n" + TONE_BLOCK +
                  "  【安全边界（硬约束）】\n  - 不诊断\n")

    def test_baseline_fixture_warns(self):
        """夹具里没有口吻小节时只给 WARN，不虚报也不漏报成 error。"""
        self.assertClean(VS.check_runtime_mirror, "无口吻小节的夹具")
        self.assertTrue(any("跳过运行时镜像比对" in w for w in VS.WARNINGS),
                        f"应给出跳过比对的 WARN，实际: {VS.WARNINGS}")

    def test_aligned_mirror_clean(self):
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK)
        self.assertClean(VS.check_runtime_mirror, "内核与运行时同数")

    def test_voice_pair_split_detected(self):
        """五批：把「旁观者」那半挪到另一行（两词都还在）——称了「你」却没禁旁白，照样报红。"""
        self.write("SKILL.md", self.KERNEL.replace(
            "不用旁观者口吻", "\n\n不用旁观者口吻", 1))
        self.write("agents/openai.yaml", self.RUNTIME_OK)
        self.assertErrors(VS.check_runtime_mirror, "内核人称绑定断裂", "人称与非编造条款未落地")

    def test_voice_missing_in_runtime_detected(self):
        """五批：内核写了「只说她说过的事」、运行时镜像没跟上——真实宿主读的是镜像。"""
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK.replace("她没讲的不补", "随意补充", 1))
        self.assertErrors(VS.check_runtime_mirror, "运行时缺非编造条款", "agents/openai.yaml 人称与非编造条款未落地")

    def test_voice_clean_both_sides(self):
        """阴性对照：两处都在场时不报这条（防判据写松成永远报红）。"""
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK)
        errs = [e for e in self.run_check(VS.check_runtime_mirror) if "人称与非编造" in e]
        self.assertEqual([], errs, f"两处条款俱在却误报：{errs}")

    def test_kernel_gains_rule_detected(self):
        """内核加一条、运行时没跟上——正是 0.1.4 踩过的「9 条 vs 10 条」。"""
        self.write("SKILL.md", self.KERNEL.replace(
            "## 限制", "### 3 不端鸡汤\n\n内容。\n\n## 限制"))
        self.write("agents/openai.yaml", self.RUNTIME_OK)
        self.assertErrors(VS.check_runtime_mirror, "内核多出一条", "脱节")

    def test_runtime_missing_block_detected(self):
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK.replace(self.TONE_BLOCK, ""))
        self.assertErrors(VS.check_runtime_mirror, "运行时缺段", "缺少【说话方式")

    def test_duplicate_top_level_key_detected(self):
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK + "\nsystem_prompt: 又一份\n")
        self.assertErrors(VS.check_runtime_mirror, "顶层键重复", "顶层键重复")

    def test_nested_key_not_mistaken_for_top_level(self):
        """interface 下的缩进键不参与顶层键查重。"""
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml",
                   self.RUNTIME_OK.replace("  display_name: 乡土陪伴师",
                                           "  display_name: 乡土陪伴师\n  system_prompt: 缩进同名词"))
        self.assertClean(VS.check_runtime_mirror, "缩进键不应判重")

    OPENER_KERNEL = KERNEL.replace(
        "## 说话方式（硬约束）",
        "## 开场白（固定）\n\n新对话的第一句固定为：**乖乖，有什么事想和我分享的吗？**"
        "——原样发出，不介绍自己，也不加过程话。\n\n## 说话方式（硬约束）")
    OPENER_RUNTIME = ("interface:\n  display_name: 乡土陪伴师\n\nsystem_prompt: |\n"
                      "  【开场白（固定）】\n  新对话的第一句固定为：「乖乖，有什么事想和我分享的吗？」"
                      "——原样发出，此后不介绍自己，也不加过程话。\n\n" + TONE_BLOCK +
                      "  【安全边界（硬约束）】\n  - 不诊断\n")

    def test_opener_aligned_clean(self):
        self.write("SKILL.md", self.OPENER_KERNEL)
        self.write("agents/openai.yaml", self.OPENER_RUNTIME)
        self.assertClean(VS.check_runtime_mirror, "开场句两处一致")

    def test_opener_wording_drift_detected(self):
        """开场句是要一字不改说出口的，运行时改个字就得报。"""
        self.write("SKILL.md", self.OPENER_KERNEL)
        self.write("agents/openai.yaml",
                   self.OPENER_RUNTIME.replace("乖乖，有什么事想和我分享的吗？",
                                               "乖乖，今天想聊点什么？"))
        self.assertErrors(VS.check_runtime_mirror, "开场句被改写", "两处不一致")

    def test_opener_missing_in_runtime_detected(self):
        self.write("SKILL.md", self.OPENER_KERNEL)
        self.write("agents/openai.yaml",
                   self.OPENER_RUNTIME.replace(
                       "  【开场白（固定）】\n  新对话的第一句固定为：「乖乖，有什么事想和我分享的吗？」"
                       "——原样发出，此后不介绍自己，也不加过程话。\n\n", ""))
        self.assertErrors(VS.check_runtime_mirror, "运行时缺开场句", "未写固定开场句")

    def test_no_self_intro_rule_required_in_runtime(self):
        self.write("SKILL.md", self.OPENER_KERNEL)
        self.write("agents/openai.yaml",
                   self.OPENER_RUNTIME.replace("——原样发出，此后不介绍自己，也不加过程话。", "——原样发出。"))
        self.assertErrors(VS.check_runtime_mirror, "缺不自介约定", "不介绍自己")

    def test_no_opener_section_skips_check(self):
        """夹具/旧版没有「开场白（固定）」一节时整条跳过，不虚报。"""
        self.write("SKILL.md", self.KERNEL)
        self.write("agents/openai.yaml", self.RUNTIME_OK)
        self.assertClean(VS.check_runtime_mirror, "无开场白一节")


class TestA16MemorySpec(FixtureCase):
    """长期记忆门禁：只落本机、先同意再写、两层默认不开、四条口令齐、云端降档。"""

    def test_baseline_clean(self):
        self.assertClean(VS.check_memory_spec, "长期记忆基线")

    def test_guide_missing_detected(self):
        (self.root / "guides" / "02-长期记忆.md").unlink()
        self.assertErrors(VS.check_memory_spec, "记忆指南缺失", "missing memory guide")

    def test_kernel_route_missing_detected(self):
        """指南在、内核没路由——等于功能对模型不存在。"""
        self.write("SKILL.md", SKILL_OK.replace(
            "| 跨会话记忆 | `guides/02-长期记忆.md` |\n", ""))
        self.assertErrors(VS.check_memory_spec, "内核未路由", "未把跨会话记忆路由")

    def test_command_heading_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("### 撤销\n\n删她指的那条\n\n", ""))
        self.assertErrors(VS.check_memory_spec, "缺撤销口令", "口令小节不全")

    def test_hard_rule_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("- **不上传**\n", "- **可外传**\n"))
        self.assertErrors(VS.check_memory_spec, "缺不外传硬账", "存储硬账缺失")

    def test_consent_layer_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("**单独同意**，**默认不建**", "一并同意"))
        self.assertErrors(VS.check_memory_spec, "危机项未单独同意", "同意层级缺失")

    def test_downgrade_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("云端宿主降档", "其他宿主"))
        self.assertErrors(VS.check_memory_spec, "缺云端降档", "宿主降档口径缺失")

    def test_store_path_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace(".xiangtupeibanshi", "某处"))
        self.assertErrors(VS.check_memory_spec, "未声明落点", "未声明档案落点")

    def test_multiuser_section_missing_detected(self):
        """D-1：没有分档办法，换一个人来就用上一位的档案接话——串档。"""
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("## 一台电脑不止一个人", "## 其他说明"))
        self.assertErrors(VS.check_memory_spec, "缺分档办法", "一台电脑不止一个人")

    def test_multiuser_marks_missing_detected(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("换人对原档**不念、不引用、不改**，另建一份", "先问一句"))
        self.assertErrors(VS.check_memory_spec, "分档办法不完整", "分档办法不全")

    def test_rename_code_mark_missing_detected(self):
        """D-14：改代号不留文件名跟着走的说法，旧名还在就会读不到档。"""
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("；改代号时文件名跟着改", ""))
        self.assertErrors(VS.check_memory_spec, "缺改代号口径", "分档办法不全")

    def test_honesty_marks_missing_detected(self):
        """D-12：她问「会不会被留存／拿去训练」时没话可说，就会过度承诺。"""
        self.write("guides/02-长期记忆.md", MEMORY_GUIDE_OK.replace(
            "她问对话会不会被留存、被拿去训练：那由宿主定，我不替它打保票。\n\n", ""))
        self.assertErrors(VS.check_memory_spec, "缺对话留存口径", "诚实口径")

    def test_third_party_section_missing_detected(self):
        """D-13：第三人来要、她问别人的档，两种旁人在场都得有依据。"""
        self.write("guides/02-长期记忆.md", MEMORY_GUIDE_OK.replace(
            "## 别人来要呢\n\n第三人来要，我不念给任何人，也不确认有没有这份档案。\n\n", ""))
        self.assertErrors(VS.check_memory_spec, "缺旁人在场一节", "别人来要呢")

    def test_reopen_marks_missing_detected(self):
        """D-15：撤回后重开若追补已删条目，清空就成了假的。"""
        self.write("guides/02-长期记忆.md", MEMORY_GUIDE_OK.replace(
            "撤回后她又说记着我，算重新同意，从不追补已删的条目。\n\n", ""))
        self.assertErrors(VS.check_memory_spec, "缺撤回后重开口径", "重新同意")

    def test_cold_start_trigger_missing_detected(self):
        """D-5：冷启动读档得在内核里有触发点，只写在 guide 里模型未必走到。"""
        self.write("SKILL.md", SKILL_OK.replace("新对话开口前，先静默读本机档案。", ""))
        self.assertErrors(VS.check_memory_spec, "内核无冷启动触发点", "冷启动读档")

    def test_cold_start_must_be_in_entry_section(self):
        """字样埋在「限制」一节里等于没有——触发点必须在入口那一节。"""
        moved = SKILL_OK.replace("新对话开口前，先静默读本机档案。", "").replace(
            "本 Skill 不是专业心理治疗。",
            "本 Skill 不是专业心理治疗。新对话开口前，先静默读本机档案。")
        self.write("SKILL.md", moved)
        self.assertErrors(VS.check_memory_spec, "触发点埋错节", "缺冷启动读档触发点")

    def test_repo_trace_detected(self):
        """档案一旦落进仓库就是隐私外泄，比漏写一条口令严重得多。"""
        self.write("profile.md", "她的称呼：当家的\n")
        self.assertErrors(VS.check_memory_spec, "仓库内有档案", "仓库内出现记忆档案")

    def test_repo_trace_detected_for_second_person(self):
        """换人分档会写出 profile-<代号>.md，带后缀的档同样不许进仓库。"""
        self.write("profile-阿梅.md", "她的称呼：阿梅\n")
        self.assertErrors(VS.check_memory_spec, "分档档案进仓", "profile-阿梅.md")

    def test_gitignore_without_marker_detected(self):
        self.write(".gitignore", "tmp/\n")
        self.assertErrors(VS.check_memory_spec, "gitignore 未挡档案", "未忽略记忆档案目录")

    def test_gitignore_absent_is_silent(self):
        """夹具本就没有 .gitignore，不应凭空报错（独立成仓场景）。"""
        self.assertFalse((self.root / ".gitignore").exists())
        self.assertClean(VS.check_memory_spec, "无 .gitignore")

    def test_legacy_term_detected(self):
        self.write("guides/99-测试模式.md", "# 测试模式\n\n用户画像不更新。\n")
        self.assertErrors(VS.check_memory_spec, "旧称未同步", "旧称")


class TestA17PersonJudgment(FixtureCase):
    """人物判断门禁：五路进料齐、三层齐、判断句带把握度与改口条件、定性须她索要。

    每条判据都有独立破坏用例——门禁判据只要有一条无从触发，它就等于没写。
    """

    def test_baseline_clean(self):
        self.assertClean(VS.check_person_judgment, "人物判断基线")

    def test_guide_missing_detected(self):
        (self.root / "guides" / "24-人物档案与判断.md").unlink()
        self.assertErrors(VS.check_person_judgment, "指南缺失",
                          "missing person-judgment guide")

    def test_kernel_route_missing_detected(self):
        self.write("SKILL.md", SKILL_OK.replace(
            "| 人物判断 | `guides/24-人物档案与判断.md` |\n", ""))
        self.assertErrors(VS.check_person_judgment, "内核未路由", "未把人物判断路由")

    def test_each_input_required(self):
        """五路进料逐条破坏：少任何一路，判断就退化成凭一句话定罪。

        必须抹掉**全部**出现次数——夹具里「现实事件」在两处出现，只抹一处仍算齐料，
        那样这条用例就成了假绿（本仓第一批夹具只抹一处，正是因为加了推类型一节才暴露）。
        """
        for mark in VS.PERSON_INPUT_MARKS:
            self.write("guides/24-人物档案与判断.md",
                       JUDGMENT_GUIDE_OK.replace(mark, ""))
            self.assertErrors(VS.check_person_judgment, f"缺进料「{mark}」", "进料不全")

    def test_layer_missing_detected(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("判断层", "", 1))
        self.assertErrors(VS.check_person_judgment, "缺判断层", "三层口径不全")

    def test_rival_explanation_required(self):
        """解释层只走个形式（没有竞争解释）也要报红。"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("互相竞争的解释", "她的解释", 1))
        self.assertErrors(VS.check_person_judgment, "解释层不竞争", "三层口径不全")

    def test_confidence_required(self):
        """抹掉**全部**「把握度」：本篇在判断句要求与长度档两处都写它，只抹第一处仍算齐字。
        （2026-10-02 加「砍的是排比」那句时正是这样假绿了一次——与 T20 五路进料、T22 改口条件同一教训。）"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("把握度", "感觉"))
        self.assertErrors(VS.check_person_judgment, "判断无把握度", "判断句要求缺失")

    def test_falsifier_required(self):
        """抹掉**全部**「改口条件」：夹具里它出现两次（判断句要求与推类型的逐轮跟进），
        只改第一处仍算齐字——同 T20 那次五路进料的假绿同一个道理。"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("改口条件", "底气"))
        self.assertErrors(VS.check_person_judgment, "判断无改口条件", "判断句要求缺失")

    def test_tier_gate_required(self):
        """她没索要就给人定性，是最容易滑过去的一步。"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("只在她自己明确要这一句时，且", "随时可以，并", 1))
        self.assertErrors(VS.check_person_judgment, "定性无索要门槛", "分级落点不全")

    def test_speculation_label_required(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("标成推测", "说得更狠", 1))
        self.assertErrors(VS.check_person_judgment, "定性未标推测", "分级落点不全")

    def test_refusal_rule_required(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("直说不足以下判断；", "照样给个说法；", 1))
        self.assertErrors(VS.check_person_judgment, "缺拒判口径", "拒判口径")

    def test_no_label_fill_in_gap(self):
        self.write("guides/24-人物档案与判断.md", JUDGMENT_GUIDE_OK.replace(
            "不许用 MBTI 补事实的空缺。", "可以用 MBTI 先顶着。", 1))
        self.assertErrors(VS.check_person_judgment, "拿标签补证据", "拒判口径")

    def test_no_diagnosis_words(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("不用诊断词", "可以用诊断词", 1))
        self.assertErrors(VS.check_person_judgment, "缺诊断边界", "诊断边界")

    def test_timing_required(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("第一轮只做接住，判断排在其后；", "", 1))
        self.assertErrors(VS.check_person_judgment, "未钉时机", "未钉住时机")

    def test_crisis_yield_required(self):
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("先走 `guides/40-危机识别.md`", "先按本篇判", 1))
        self.assertErrors(VS.check_person_judgment, "危机不让路", "未让路给危机流程")

    def test_memory_archive_sync(self):
        """本篇改了档案字段、guides/02 没跟上——两处一脱钩，落盘就记错东西。"""
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("她的评分／她的类型标签", "她的说法", 1))
        self.assertErrors(VS.check_person_judgment, "档案字段未同步", "人物档案字段未与本篇同步")

    def test_infer_section_missing_detected(self):
        """没有「她要我推类型」这一节＝她索要类型时没有口径，模型会自己发明测评话术。"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace(VS.PERSON_INFER_HEADING, "## 其他", 1))
        self.assertErrors(VS.check_person_judgment, "缺推类型一节", "缺「推类型：默认在推，不主动说」一节")

    def test_each_infer_rule_required(self):
        """推类型六条判据逐条破坏：「不主动询问」少一个字，就成逢人就问 MBTI。"""
        for mark in VS.PERSON_INFER_MARKS:
            self.write("guides/24-人物档案与判断.md",
                       JUDGMENT_GUIDE_OK.replace(mark, ""))
            self.assertErrors(VS.check_person_judgment, f"缺推类型判据「{mark}」", "推类型口径不全")

    def test_infer_rules_survive_rewording(self):
        """反义改写三处必须照样报红：判据认语义位置，不能被同义词悄悄换掉。"""
        for old, new in (("不主动询问", "可以主动询问"),
                         ("说，要她先开口", "说，不必等她开口"),
                         ("本场不再自行重启", "本场之后照常重启"),
                         ("至多两句", "长短不论"),
                         ("**过程不出口**", "过程也可以讲给她听"),
                         ("**连「我不给」都不出口，也不给替代的检索词**", "直接说不给，再给几个替代检索词"),
                         ("**只说她说过的事**，她没讲的不补", "可以按常理推测她没说的事")):
            self.write("guides/24-人物档案与判断.md",
                       JUDGMENT_GUIDE_OK.replace(old, new, 1))
            self.assertErrors(VS.check_person_judgment, f"反义改写「{old}」", "推类型口径不全")

    def test_memory_inference_clause_sync(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("我推出来的类型倾向同样不落档。", "", 1))
        self.assertErrors(VS.check_person_judgment, "推断落档口径缺失", "人物档案字段未与本篇同步")

    def test_infer_same_line_pairs_required(self):
        """六对同句绑定：把右侧那半挪到另一行（两词都还在）必须照样报红。

        只查「全文有没有这个词」会被别处同词顶包——这六对管的是位置。
        """
        for left, right in VS.PERSON_INFER_SAME_LINE_PAIRS:
            self.write("guides/24-人物档案与判断.md",
                       JUDGMENT_GUIDE_OK.replace(right, chr(10) + chr(10) + right, 1))
            self.assertErrors(VS.check_person_judgment,
                              f"同句绑定断裂「{left}｜{right}」", "推类型同句绑定断裂")

    def test_infer_pair_split_not_reported_as_absence(self):
        """拆行只该触发位置判据，不该被「词缺失」误报——两条判据各管一头。"""
        left, right = VS.PERSON_INFER_SAME_LINE_PAIRS[0]
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace(right, chr(10) + chr(10) + right, 1))
        errs = self.run_check(VS.check_person_judgment)
        self.assertTrue(any("同句绑定断裂" in e for e in errs), f"未报位置错：{errs}")
        self.assertFalse(any("推类型口径不全" in e for e in errs),
                         f"两词俱在却报词缺失，两条判据串了：{errs}")

    def test_memory_longterm_stop_sync(self):
        """她说明白「以后都别推」＝长期停，得有个跨会话的落点；档案侧没这句，停就只活一场。"""
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("长期停", "", 1))
        self.assertErrors(VS.check_person_judgment, "长期停未入档", "人物档案字段未与本篇同步")

    def test_infer_reply_locks_required(self):
        """她逐字定的两条回复（一句问完就停／硬凑不了一个人格）被改写＝口径变了，必须报红。"""
        for lock in VS.PERSON_INFER_REPLY_LOCKS:
            self.write("guides/24-人物档案与判断.md",
                       JUDGMENT_GUIDE_OK.replace(lock, "你再说说是哪件事。", 1))
            self.assertErrors(VS.check_person_judgment,
                              f"定稿句改写「{lock[:6]}…」", "定稿句被改写")

    def test_infer_lock_kept_while_rule_broken(self):
        """定稿句还在、但把长度上限拆成另一行：词面俱在、约束已断——位置判据得独立抓到。"""
        left, right = VS.PERSON_INFER_SAME_LINE_PAIRS[6]
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace(right, chr(10) + chr(10) + right, 1))
        errs = self.run_check(VS.check_person_judgment)
        self.assertTrue(any("同句绑定断裂" in e and left in e for e in errs), f"未报长度上限断线：{errs}")
        self.assertFalse(any("定稿句被改写" in e for e in errs), f"定稿句未动却误报：{errs}")

    def test_anti_rigid_clause_required(self):
        """只留长度上限、删掉防死板的反向条款——简洁会被执行成轮轮同一句反问。"""
        self.write("guides/24-人物档案与判断.md",
                   JUDGMENT_GUIDE_OK.replace("短是省字，不是削薄", "回复就是要短", 1))
        self.assertErrors(VS.check_person_judgment, "反向条款被反义改写", "推类型同句绑定断裂")

    def test_runtime_mirror_short_mark_required(self):
        """镜像开了【人物档案与判断】这一节却没写长度上限：运行时提示里没有，guides 的约束就落不到真实宿主。"""
        self.write("agents/openai.yaml",
                   "【人物档案与判断】\n- 说出口那轮末了把话头交回给她一句，也别轮轮拿同一句反问交差\n")
        self.assertErrors(VS.check_person_judgment, "镜像缺「过程不出口」", "未落地简洁上限")

    def test_runtime_mirror_marks_all_required(self):
        """六判据逐条破坏，缺哪条报哪条（两档的句数与字数都在内）。"""
        base = ("【人物档案与判断】\n"
                "- 出口至多两句、整条不超 60 字，过程不出口，连「我不给」都不出口、不给替代的检索词；"
                "末了把话头交回给她一句，也别轮轮拿同一句反问交差\n")
        for mark in VS.PERSON_RUNTIME_MARKS:
            self.write("agents/openai.yaml", base.replace(mark, ""))
            self.assertErrors(VS.check_person_judgment, f"镜像缺「{mark}」", "未落地简洁上限")

    def test_runtime_mirror_clean_when_all_present(self):
        """六判据俱在 → 不该报「未落地简洁上限」（阴性对照，防判据写松成永远报红）。"""
        base = ("【人物档案与判断】\n"
                "- 出口至多两句、整条不超 60 字，过程不出口，连「我不给」都不出口、不给替代的检索词；"
                "末了把话头交回给她一句，也别轮轮拿同一句反问交差\n")
        self.write("agents/openai.yaml", base)
        errs = [e for e in self.run_check(VS.check_person_judgment) if "未落地简洁上限" in e]
        self.assertEqual(errs, [], f"六判据齐却报错：{errs}")

    def test_runtime_mirror_no_block_not_reported(self):
        """夹具的 openai.yaml 没有这一节，不该被这条判据误伤——判据只在块存在时生效。"""
        self.write("agents/openai.yaml", "interface:\n  display_name: 乡土陪伴师\n")
        errs = [e for e in self.run_check(VS.check_person_judgment) if "未落地简洁上限" in e]
        self.assertEqual(errs, [], f"没有该节却报错：{errs}")

    def test_memory_qualifier_sync(self):
        self.write("guides/02-长期记忆.md",
                   MEMORY_GUIDE_OK.replace("我给谁的定性都不落档，", "我的定性也一并落档，", 1))
        self.assertErrors(VS.check_person_judgment, "定性落档口径相反", "人物档案字段未与本篇同步")


class TestA18DecisionBalance(FixtureCase):
    """「接住情绪 → 分析利弊 → 给下一步」中间那一环：内核、资料段、示例三处都得在位。"""

    ROW = ("| 5 行动 | 摊开两头的代价（见 `guides/12-CBT核心技能.md`），再一个小行动 |")

    def test_baseline_clean(self):
        self.assertClean(VS.check_decision_balance, "权衡基线")

    def test_kernel_step5_without_the_mark(self):
        self.write("SKILL.md", SKILL_OK.replace(self.ROW, "| 5 行动 | 一个小行动 |"))
        self.assertErrors(VS.check_decision_balance, "第 5 步不摊代价", "第 5 步缺")

    def test_mark_buried_outside_step_section(self):
        """判据按位置取：写在「限制」那一节里照样等于没有这一环。"""
        self.write("SKILL.md", SKILL_OK.replace(
            self.ROW, "| 5 行动 | 一个小行动 |").replace(
            "本 Skill 不是专业心理治疗。",
            "本 Skill 不替她做决定，也不摊开两头的代价。"))
        self.assertErrors(VS.check_decision_balance, "位置判定", "第 5 步缺")

    def test_kernel_not_routed(self):
        self.write("SKILL.md", SKILL_OK.replace("（见 `guides/12-CBT核心技能.md`）", ""))
        self.assertErrors(VS.check_decision_balance, "第 5 步未路由到资料段", "未把权衡做法路由到")

    def test_guide_section_absent(self):
        self.write("guides/12-CBT核心技能.md", "# CBT 核心技能\n\n只有三技术。\n")
        self.assertErrors(VS.check_decision_balance, "资料段缺这一节", "缺「## 摊开两头的代价」一节")

    def test_guide_missing_the_prohibition(self):
        self.write("guides/12-CBT核心技能.md",
                   "# CBT 核心技能\n\n## 摊开两头的代价（行动前的权衡）\n\n"
                   "把两头说清楚就行。命中家暴、控制、自伤时不摊利弊，先按 `guides/40-危机识别.md` 做安全评估。\n")
        self.assertErrors(VS.check_decision_balance, "缺「不替她选」", "缺护栏")

    def test_landing_question_pair_not_proxyable(self):
        """反证第三次假绿：抹掉「落点只问一句」后，别处的「不替她选」不许替这条 bullet 顶包。"""
        self.write("guides/12-CBT核心技能.md",
                   DECISION_GUIDE_OK.replace("落点只问一句", "最后问一句"))
        errs = self.run_check(VS.check_decision_balance)
        self.assertTrue(any("没把「不替她选」与「落点只问一句」写成一句" in e for e in errs),
                        f"落点问句分家应报红，实际 {errs}")

    def test_guide_missing_the_first_round_guard(self):
        """S2 场景实测出的那条：没有「不进第一轮」，内核第 5 步会把模型拽着抢跑。"""
        self.write("guides/12-CBT核心技能.md",
                   DECISION_GUIDE_OK.replace("**不进第一轮**（第一轮只做接住）；", ""))
        errs = self.run_check(VS.check_decision_balance)
        self.assertTrue(any("不进第一轮" in e for e in errs), f"应报缺第一轮护栏，实际 {errs}")

    def test_exception_split_across_lines(self):
        """反证收紧的那条：例外拆成两句、或只在资料出处留个「安全评估」，都不算写了禁则。"""
        self.write("guides/12-CBT核心技能.md",
                   "# CBT 核心技能\n\n## 摊开两头的代价（行动前的权衡）\n\n"
                   "摊完不替她选。先摊账，再说不替她选。\n\n命中家暴、控制、自伤时不摊利弊。\n\n"
                   "安全评估的做法见 `guides/40-危机识别.md`。\n")
        errs = self.run_check(VS.check_decision_balance)
        self.assertTrue(any("没把「不摊利弊」与「安全评估」写成一句" in e for e in errs),
                        f"危机例外拆句应报红，实际 {errs}")

    def test_ordering_rule_split_across_lines(self):
        """D-H4（真实宿主跑出来的那条）：「先摊账」与「不替她选」分家，机器就该红。"""
        self.write("guides/12-CBT核心技能.md",
                   "# CBT 核心技能\n\n## 摊开两头的代价（行动前的权衡）\n\n"
                   "两道护栏：**不进第一轮**；摊完**不替她选**。\n\n"
                   "命中家暴、控制、自伤时不摊利弊，先做安全评估。\n\n"
                   "她逼要结论时先把账摊开。\n")
        errs = self.run_check(VS.check_decision_balance)
        self.assertTrue(any("没把「先摊账」与「不替她选」写成一句" in e for e in errs),
                        f"次序判据应报红，实际 {errs}")

    def test_no_example_shows_the_move(self):
        self.write("examples/README.md", "# 示例导航\n")
        self.assertErrors(VS.check_decision_balance, "示例没给样", "没有一处摊代价的落点问句")


class TestA19ComfortStance(FixtureCase):
    """第 21 类：安慰的立场·不端方案·禁问·回访——四处空白各自的绑定与镜像。"""

    SKILL = ("---\nname: xiangtupeibanshi\ndescription: d\n---\n\n# 内核\n\n"
             "## 说话方式（硬约束）\n\n开篇。\n\n### 10 先站在她这边\n\n"
             "附和她骂那个人时只用她自己用过的那几个字，不加码、不扩展。\n"
             "和稀泥不算中立。站她这边是站她的处境，不是替她定罪别人。\n"
             "她没开口要办法，往后的轮次同样不许端方案。\n"
             "那一个问题都别问，我不催你。我嘴笨、我比你更糟、谁不是这么过来的，一律禁用。\n\n"
             "## 细节与颗粒度\n\n"
             "**细节要有颗粒度**：**换成一个动作或一个瞬间的，就不要留成形容词**。\n\n"
             "## 峰值与换挡\n\n"
             "**峰值过去，换挡要有信号**：**不追着问细节**。\n"
             "**被质问时不自证**：**在场要给足**；**她转述别人**对她施压式的质问时，"
             "**答了就是替她答**。\n"
             "**她先给自己降格时，要把它顶回去**——别人心里那把尺子就歪了；"
             "我认的是她此刻的分量，不是她替自己定的位次。\n"
             "**减法多于加法**：不追问、不劝、不升级；**把她话里的那个词接住**、往下问半步，"
             "不劝、不出谋；关系淡了**先认当初那半句是真的**：**先接住，再松动**。\n"
             "她没问「他为什么这样」，**不劝她去把原因想明白**——"
             "**你不是那种人，所以你不需要懂他**；和稀泥不算中立。\n"
             "**技巧是末位，人才是前提**：**没有「我应该更会安慰」这回事**，只有她认不认我。\n"
             "禁**空洞安慰**：接不上她说过的任何一件事，那是**把人往外推**。\n\n"
             "## 限制\n\n非医疗。\n")
    YAML = ("interface:\n  display_name: 乡土陪伴师\n\nsystem_prompt: |\n"
            "  【说话方式（硬约束）】\n  你是乡伴。只用她自己用过的字，不加码。和稀泥不算中立。\n"
            "  她没开口要办法就不许端方案。那一个问题都别问。我嘴笨属禁用。\n"
            "  你不是那种人，所以你不需要懂他。和稀泥不算中立。\n")
    G00 = ("# 欢迎\n\n**我不是她朋友的替代品，也不是那个「情绪垃圾桶」**：我是**有限的**、"
           "她愿意开口的那几次。\n\n"
           "**可信度是攒出来的，不是承诺出来的。**\n\n"
           "**陪伴占七成，倾听两成，技巧一成。**\n\n"
      "**技巧排最后**：技巧是给已经信我的人用的，只有**她认不认我**。\n\n"
           "## 能做什么\n\n清单。\n")
    G02 = ("# 长期记忆\n\n# 我们走到哪儿\n# 上次留下的锚（写档时顺手挑一句，没有就留空）\n"
           "\n## 先取得同意（两层，默认都不开）\n\n"
           "**怎么说**：一轮一问。\n\n"
           "**问完就止**：存储位置和控制权只说这一轮一次，收口那句话只说她的。\n"
           "略。\n"
           "\n## 事后那一次（回访）\n\n留一个**不带目的的轻触**；"
           "锚在写档那一轮顺手挑一句当锚；档案记「上次留下的锚」；第一句从锚接，"
           "不空问「最近怎么样」；只递一次；她不来，我发不出去。\n")
    G22 = ("# 中圈关系（朋友同事）\n\n## 一条定调：别太用力\n\n"
           "不用力不是冷漠——**该在的时候要在**（她真出事，我不缺席）。\n\n"
           "## 共同交集\n\n"
           "**找交集，不打探**：**她没提家里的事，我不挖**。\n")

    def base(self):
        self.write("SKILL.md", self.SKILL)
        self.write("agents/openai.yaml", self.YAML)
        self.write("guides/00-欢迎与定位.md", self.G00)
        self.write("guides/02-长期记忆.md", self.G02)
        self.write("guides/22-中圈关系.md", self.G22)

    def test_baseline_clean(self):
        self.base()
        self.assertClean(VS.check_comfort_stance, "四处齐备的夹具")

    def test_stance_pair_split_detected(self):
        """把「不加码」挪到另一行：两个词都还在，绑定断了——拆开写等于这条没写。"""
        self.base()
        self.write("SKILL.md", self.SKILL.replace("那几个字，不加码", "那几个字。\n\n不加码", 1))
        self.assertErrors(VS.check_comfort_stance, "立场同句绑定断裂", "立场同句绑定断裂")

    def test_wordlist_drift_detected(self):
        """第 7 条写了比惨禁句、词表没跟上：examples/ 里的比惨句就没人抓。"""
        self.base()
        saved = VS.BANNED_COMFORT
        VS.BANNED_COMFORT = tuple(w for w in saved if w != "我嘴笨")
        try:
            self.assertErrors(VS.check_comfort_stance, "词表与规范脱节", "BANNED_COMFORT 与第 7 条脱节")
        finally:
            VS.BANNED_COMFORT = saved

    def test_empty_comfort_rule_missing_detected(self):
        """抹掉第 7 条的空洞安慰禁令：接不上事实的通用句又没人管了（正文 3xf5j84ek8bvbqe）。"""
        self.base()
        self.write("SKILL.md", self.SKILL.replace("禁**空洞安慰**：接不上她说过的任何一件事，那是**把人往外推**。", "", 1))
        self.assertErrors(VS.check_comfort_stance, "空洞安慰禁令缺失", "第 7 条缺空洞安慰禁令")

    def test_empty_comfort_wordlist_drift_detected(self):
        """第 7 条写了空洞安慰、词表没跟上：examples/ 里的「没事的」就没人抓。"""
        self.base()
        saved = VS.BANNED_COMFORT
        VS.BANNED_COMFORT = tuple(w for w in saved if w != "没事的")
        try:
            self.assertErrors(VS.check_comfort_stance, "空洞安慰词表脱节", "未进词表")
        finally:
            VS.BANNED_COMFORT = saved

    def test_trust_first_missing_detected(self):
        """guides/00 只剩三七一、没有「技巧是给已经信我的人用的」：定位又变回技术清单。"""
        self.base()
        self.write("guides/00-欢迎与定位.md",
                   "# 欢迎\n\n**陪伴占七成，倾听两成，技巧一成。**\n\n## 能做什么\n\n清单。\n")
        self.assertErrors(VS.check_comfort_stance, "技巧前置缺失", "技巧排最后")

    def test_runtime_mirror_missing_detected(self):
        """内核写了、运行时镜像没跟：真实宿主读的是镜像。"""
        self.base()
        # 口吻小节在场、立场条款被抹——这才是要抓的情形；整节没有时按 check_runtime_mirror 口径跳过
        self.write("agents/openai.yaml",
                   "interface:\n  display_name: 乡土陪伴师\n\nsystem_prompt: |\n"
                   "  【说话方式（硬约束）】\n  你是乡伴。\n")
        self.assertErrors(VS.check_comfort_stance, "运行时缺立场条款", "立场条款未落地")

    def test_no_solution_rule_missing_detected(self):
        self.base()
        self.write("SKILL.md", self.SKILL.replace("她没开口要办法，往后的轮次同样不许端方案。", "", 1))
        self.assertErrors(VS.check_comfort_stance, "第 2 条未扩到整场", "她没开口要办法")

    def test_followup_section_missing_detected(self):
        self.base()
        self.write("guides/02-长期记忆.md", "# 长期记忆\n\n## 与危机流程的接缝\n\n让路。\n")
        self.assertErrors(VS.check_comfort_stance, "缺回访节", "事后那一次（回访）")

    def test_followup_overpromise_detected(self):
        """删掉「她不来，我发不出去」：回访会被写成主动联系——兜不住的承诺。"""
        self.base()
        self.write("guides/02-长期记忆.md", self.G02.replace("她不来，我发不出去。", "", 1))
        self.assertErrors(VS.check_comfort_stance, "回访缺诚实边界", "她不来，我发不出去")

    def test_followup_anchor_not_pinned_to_close_detected(self):
        """真实宿主实测：收口那一轮被记忆同意占满，锚落在那里必然落空。"""
        self.base()
        self.write("guides/02-长期记忆.md",
                   self.G02.replace("锚在写档那一轮顺手挑一句当锚；",
                                     "收口那一轮留一个轻触；", 1))
        self.assertErrors(VS.check_comfort_stance, "锚又落回收口", "没钉在写档那一轮")

    def test_template_field_missing_detected(self):
        """正文说记进档案、模板里没有这一行，落点悬空（K5）。"""
        self.base()
        self.write("guides/02-长期记忆.md",
                   self.G02.replace("# 上次留下的锚（写档时顺手挑一句，没有就留空）\n", "", 1))
        self.assertErrors(VS.check_comfort_stance, "模板缺锚字段", "模板没有「上次留下的锚」")

    def test_consent_receipt_rule_missing_detected(self):
        """真实宿主 22:49：同意与「记好了，就落在这台电脑上…」被合进同一条回复，
        收口那一轮变成了存取回执。判据须在场。"""
        self.base()
        self.write("guides/02-长期记忆.md",
                   self.G02.replace("**问完就止**：存储位置和控制权只说这一轮一次，收口那句话只说她的。\n", "", 1))
        self.assertErrors(VS.check_comfort_stance, "缺问完就止", "缺「问完就止」")

    def test_ratio_anchor_split_detected(self):
        self.base()
        self.write("guides/00-欢迎与定位.md", "# 欢迎\n\n陪伴占七成。\n倾听两成。\n技巧一成。\n")
        self.assertErrors(VS.check_comfort_stance, "三七一未同句", "缺同句定锚")


class TestA18RealRepoDecisionBalance(unittest.TestCase):
    """真实仓库得有这一环——夹具只证明判据会红，不证明仓库是绿的。"""

    def setUp(self):
        self._saved_root, self._saved_errs = VS.ROOT, list(VS.ERRORS)
        VS.ROOT = ROOT
        VS.ERRORS.clear()

    def tearDown(self):
        VS.ERRORS.clear()
        VS.ERRORS.extend(self._saved_errs)
        VS.ROOT = self._saved_root

    def test_real_repo_has_decision_balance(self):
        VS.check_decision_balance()
        self.assertEqual(list(VS.ERRORS), [], f"真实仓库缺「分析利弊」这一环：{list(VS.ERRORS)}")

    def test_kernel_still_within_line_budget(self):
        """内核这一行是就地改写的：加行会撞 200 行硬闸门。"""
        lines = len((ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(lines, VS.SKILL_MAX_LINES, f"SKILL.md 行数超预算：{lines}")


class TestA19DocCheckRegistry(unittest.TestCase):
    """「检查项清单」的行序、函数名单、类数，一律从 `CHECKS` 数出来，不再手抄。"""

    DOC = "references/验证脚本说明.md"
    ROW = re.compile(r"^\|\s*\d+\s*\|[^|]*\|\s*`(check_[a-z_]+)`\s*\|", re.MULTILINE)

    def test_doc_rows_match_registration_order(self):
        names = [f.__name__ for f in VS.CHECKS]
        listed = self.ROW.findall((ROOT / self.DOC).read_text(encoding="utf-8"))
        self.assertEqual(listed, names,
                         "文档表与 CHECKS 不同序或有漏登记——新增检查项须同步这一张表")

    def test_doc_category_count_is_derived(self):
        text = (ROOT / self.DOC).read_text(encoding="utf-8")
        m = re.search(r"## 3\. 检查项清单（(\d+) 类）", text)
        self.assertTrue(m, "「检查项清单」标题应写明类数")
        self.assertEqual(int(m.group(1)), len(VS.CHECKS),
                         f"标题类数 {m.group(1)} 与 CHECKS 实际 {len(VS.CHECKS)} 不符")

    def test_removal_of_a_registered_check_is_detected(self):
        """反证：把一项从 CHECKS 摘掉，文档比对必须立刻变红，而不是继续「抄来的数正好」。"""
        saved = VS.CHECKS
        VS.CHECKS = saved[:-1]
        try:
            with self.assertRaises(AssertionError):
                self.test_doc_rows_match_registration_order()
        finally:
            VS.CHECKS = saved


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

    def test_split_single_char_bold_cleaned(self):
        """被双字词隔开的单字加粗：SIGNATURE 看不见，clean_line 须与校验器同口径接住。"""
        out, hit, _ = CB.clean_line("2. **不**替来访者**做**决定")
        self.assertTrue(hit, "非相邻形态应判为污染")
        self.assertEqual(out, "2. 不替来访者做决定")

    def test_latin_initial_bold_preserved(self):
        """只加粗单个拉丁字母是首字母强调，不得误伤。"""
        line = "> （**P**sychoticism 精神质／**E**xtraversion 外向性／**N**euroticism 神经质）"
        out, hit, _ = CB.clean_line(line)
        self.assertFalse(hit, f"拉丁首字母加粗不应判错: {line}")
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
                if not flags[i] and VS.bold_polluted(VS.strip_inline_code(line)):
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
        m = re.search(r"^version:\s*(\S+)", manifest, re.MULTILINE)
        self.assertIsNotNone(m, "docs/manifest.yaml 缺少 version 字段")
        self.assertEqual(m.group(1), version, "manifest 版本与 VERSION 不一致")

    def test_dimension_vocab_matches_data_source(self):
        """受控词表须三处一致：校验器 / 仓内事实源 / 生成侧 TSV。

        2026-10-03 改判：`_plan/` 不可见时**报红而非 skip**。此前是 skipTest，
        于是 CI 上这条比对永不执行，「170 用例全绿」实际并不覆盖 122 张卡的
        受控词表——本地全绿被误读成「线上有守护」。受控词表已搬进
        docs/tag-vocabulary.md（仓内 SSOT），即便 `_plan/` 缺失也仍可校验前两处。
        """
        doc = ROOT / "docs" / "tag-vocabulary.md"
        self.assertTrue(doc.is_file(), "缺仓内词表事实源 docs/tag-vocabulary.md")
        vocab_doc = doc.read_text(encoding="utf-8")
        keys = ["domain", "audience", "approach", "culture"]

        # 仓内事实源 §2 的表格：`| `板块/` | `domain` | 12 | 取值1 · 取值2 … |`
        for ns, key in VS.DIM_NS.items():
            m = re.search(r"^\|\s*`" + re.escape(ns) + r"/`\s*\|\s*`" + key +
                          r"`\s*\|[^|]*\|([^|]*)\|\s*$", vocab_doc, re.MULTILINE)
            self.assertIsNotNone(m, f"docs/tag-vocabulary.md §2 缺 `{ns}/` → `{key}` 行")
            doc_vals = {v.strip() for v in m.group(1).split("·") if v.strip()}
            self.assertEqual(doc_vals, VS.DIM_VOCAB[key],
                             f"{key} 词表漂移：仓内事实源 {sorted(doc_vals)} vs "
                             f"校验器 {sorted(VS.DIM_VOCAB[key])}")
        # 自由标注命名空间也须在仓内事实源 §3 有登记（校验器 check_tag_namespace 逐卡再查一遍）
        for ns in VS.FREE_NS:
            self.assertIn(f"`{ns}/`", vocab_doc,
                          f"docs/tag-vocabulary.md §3 未登记自由命名空间 `{ns}/`")

        # 生成侧：仓库外的 TSV 仍须与前两处一致
        src = ROOT.parent / "_plan" / "_taxonomy_dimensions.tsv"
        self.assertTrue(src.is_file(),
                        "_plan/_taxonomy_dimensions.tsv 不可见：词表生成侧无法核对。"
                        "本仓已把它降为生成侧、受控词表以 docs/tag-vocabulary.md 为准，"
                        "但 TSV 消失意味着流水线入口丢失，须查明后再放行。")
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
        n = len(list((self.root / "guides").glob("*.md"))) - 1   # 扣除 README.md
        self.write("docs/manifest.yaml", f"guides: {n}\nexamples: 0\nreferences: 1\n")
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

    def test_bold_pollution_criteria_agree(self):
        """校验器判错的行，修正器必须认同一处并能动它——两侧口径不得各说各话。

        比对在不含行内代码的单行上做：校验器先 strip_inline_code 再判，
        clean_line 则自行遮罩代码段，两侧的差异只在代码段处理方式。
        """
        samples = (
            "> **本**文**档** = **整**个** s**k**i**l**l** 框**架**",   # 相邻形态
            "2. **不**替来访者**做**决定",                              # 被双字词隔开
            '- "你**有**没有**想**过**伤害**自己**？"',                  # 危机话术污染
            "- **自伤**想法、行为",                                      # 合法整词
            "- **不**追问创伤细节",                                      # 单处单字强调
            "> （**P**sychoticism／**E**xtraversion）",                  # 拉丁首字母
            "- **1**月**2**日开会",                                      # 已知限制：仍判污染
        )
        for line in samples:
            with self.subTest(line=line):
                self.assertEqual(VS.bold_polluted(line), CB.polluted(line),
                                 "两侧污染判定不一致")
                if VS.bold_polluted(line):
                    self.assertNotEqual(CB.clean_line(line)[0], line,
                                        "校验判污染但修正器不动它 → 死结")


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


# ============================================================ A2x. 骨架与索引面
class TestA20CardSchema(FixtureCase):
    """档案卡骨架（check_card_schema）：13 节齐备且有序、自由带非空、目录逐条对齐、括注受控。

    反证的意义：`check_books` 只查 frontmatter 与「未读边界」子串，
    `check_dimensions` 只查多维标注——骨架此前无门禁，于是 7 种「真实学术信息」标题、
    2 种「未读边界」标题、122/122 张卡目录缺后注入三节，长期无人发现。
    """

    CARD = "_books/《乡土中国》.md"

    def _card(self) -> str:
        return (self.root / self.CARD).read_text(encoding="utf-8")

    def _put(self, text: str) -> None:
        self.write(self.CARD, text)

    def test_baseline_clean(self):
        self.assertClean(VS.check_card_schema, "骨架")

    def test_missing_skeleton_heading(self):
        self._put(self._card().replace("## 根本矛盾点\n\n内容\n\n", ""))
        self.assertErrors(VS.check_card_schema, "缺骨架节", "骨架节缺失")

    def test_skeleton_out_of_order(self):
        """把「安慰和治疗」整段挪到「基本矛盾点」之前——节都在，但顺序错。"""
        text = self._card()
        block = "## 安慰和治疗\n\n内容\n\n"
        text = text.replace(block, "")
        text = text.replace("## 基本矛盾点", block + "## 基本矛盾点", 1)
        self._put(text)
        self.assertErrors(VS.check_card_schema, "骨架乱序", "顺序错误")

    def test_free_band_emptied(self):
        """抹掉自由带那一节：骨架节仍齐，但卡片实质内容无处安放。"""
        text = self._card().replace("## 核心内容\n\n内容\n\n", "")
        text = text.replace("- [[#核心内容]]\n", "")
        self._put(text)
        self.assertErrors(VS.check_card_schema, "自由带空", "没有自由带")

    def test_toc_drift_detected(self):
        self._put(self._card().replace("- [[#相关阅读]]\n", ""))
        self.assertErrors(VS.check_card_schema, "目录漂移", "卡内目录与正文不一致")

    def test_source_qualifier_out_of_vocab(self):
        text = self._card().replace("## 真实学术信息", "## 真实学术信息（据说）")
        text = text.replace("[[#真实学术信息]]", "[[#真实学术信息（据说）]]")
        self._put(text)
        self.assertErrors(VS.check_card_schema, "括注越界", "不在受控词表")

    def test_qualifier_in_vocab_allowed(self):
        text = self._card().replace("## 真实学术信息", "## 真实学术信息（原文核验）")
        text = text.replace("[[#真实学术信息]]", "[[#真实学术信息（原文核验）]]")
        self._put(text)
        self.assertClean(VS.check_card_schema, "受控括注")


class TestA21IndexPlane(FixtureCase):
    """索引面（check_index_plane）：导航表覆盖、索引书名用卡名、README 计数等于现算值。"""

    def test_baseline_clean(self):
        self.assertClean(VS.check_index_plane, "索引面")

    def test_guide_missing_from_nav(self):
        self.write("guides/README.md", "# Guides 导航\n\n- 00-欢迎与定位.md\n")
        self.assertErrors(VS.check_index_plane, "导航漏收", "未收录")

    def test_readme_count_drift(self):
        n = len(REQUIRED_GUIDE_NAMES)
        self.write("README.md",
                   "guides/   # %d 篇操作指南\n"
                   "guides/   # %d operational guides\n"
                   "validate_skill.py   # %d 类内容校验\n"
                   "validate_skill.py   # %d categories\n"
                   % (n - 1, n, len(VS.CHECKS), len(VS.CHECKS)))
        self.assertErrors(VS.check_index_plane, "计数漂移", "实测")

    def test_book_index_name_not_a_card(self):
        self.write("references/书籍档案索引.md",
                   "# 书籍档案索引\n\n| # | 书名 | 作者 | 议题 |\n|---|---|---|---|\n"
                   "| 1 | 《并不存在的书》 | 某人 | 议题 |\n")
        self.assertErrors(VS.check_index_plane, "索引书名不存在", "不对应任何档案卡")

    def test_book_index_qualifier_detected(self):
        """反证：`《乡土中国》（费孝通）` 这种「书名 + 限定语」写法，按卡名检索会落空。"""
        self.write("references/书籍档案索引.md",
                   "# 书籍档案索引\n\n| # | 书名 | 作者 | 议题 |\n|---|---|---|---|\n"
                   "| 1 | 《乡土中国》（费孝通） | 费孝通 | 差序格局 |\n")
        self.assertErrors(VS.check_index_plane, "索引限定语", "带了限定语")

    def test_card_absent_from_book_index(self):
        self.write("references/书籍档案索引.md",
                   "# 书籍档案索引\n\n| # | 书名 | 作者 | 议题 |\n|---|---|---|---|\n"
                   "| 1 | 《别的书》 | 某人 | 议题 |\n")
        self.assertErrors(VS.check_index_plane, "卡片未收录", "未收录")


class TestA22TagNamespace(FixtureCase):
    """标签命名空间（check_tag_namespace）：归属、形态、仓内事实源在场。"""

    def _card(self) -> str:
        return (self.root / "_books" / "《乡土中国》.md").read_text(encoding="utf-8")

    def _put(self, text: str) -> None:
        self.write("_books/《乡土中国》.md", text)

    def test_baseline_clean(self):
        self.assertClean(VS.check_tag_namespace, "标签命名空间")

    def test_unknown_namespace_detected(self):
        """拼错的命名空间此前无任何一道闸能发现（8 个自由命名空间全无覆盖）。"""
        text = self._card().replace("主题/关系", "方法论/CBT")
        self._put(text)
        self.assertErrors(VS.check_tag_namespace, "命名空间越界", "既不在受控维度")

    def test_controlled_tag_out_of_sync(self):
        text = self._card().replace("板块/文化与社会", "板块/循证疗法")
        self._put(text)
        self.assertErrors(VS.check_tag_namespace, "受控标签不同步", "不同步")

    def test_controlled_ns_two_values(self):
        text = self._card().replace("板块/文化与社会", "板块/文化与社会, 板块/循证疗法")
        self._put(text)
        self.assertErrors(VS.check_tag_namespace, "受控维度多值", "每卡只准一个")

    def test_vocab_doc_missing(self):
        (self.root / "docs" / "tag-vocabulary.md").unlink()
        self.assertErrors(VS.check_tag_namespace, "缺事实源", "缺仓内词表事实源")

    def test_vocab_doc_missing_free_ns(self):
        """自由命名空间没在仓内事实源 §3 表里登记 = 事实存在但机器看不见。

        破坏只删 §3 那一行：`主题/` 在 §1 总表与 §2 正文里还会出现，
        判据若用全文子串会被顶包（2026-10-03 活树反证 G5 实测未抓到）。
        """
        p = self.root / "docs" / "tag-vocabulary.md"
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines(keepends=True)
                 if not ln.startswith("| `主题/`")]
        p.write_text("".join(lines), encoding="utf-8")
        self.assertErrors(VS.check_tag_namespace, "未登记自由命名空间", "未登记命名空间")

    def test_nested_free_tag_allowed(self):
        """阴性对照：自由标注本就允许嵌套（`主题/人格/自恋型人格`），不得误报。"""
        text = self._card().replace("主题/关系", "主题/人格/自恋型人格, 方法/DBT/痛苦耐受")
        self._put(text)
        self.assertClean(VS.check_tag_namespace, "自由标注可嵌套")


if __name__ == "__main__":
    unittest.main(verbosity=2)
