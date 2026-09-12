# 架构

## 核心结构

```
xinli-zhushou/
├── SKILL.md              # 行为内核（134 行硬上限）
├── agents/openai.yaml    # 显示配置
├── guides/                # 陪伴指南（按议题）
├── _books/                # 37 本书档案卡
├── documentation/         # 开发者文档
├── examples/              # 实际使用示例
├── scripts/               # 验证脚本
└── .github/               # GitHub 模板
```

## 渐进式披露

模型**只**按议题加载相关 guides——**不**一次加载所有。

## 4 种陪伴模式

1. **倾听** — 安静地听
2. **探索** — 开放式问题
3. **支持** — 温暖 + 资源
4. **引导** — 理清价值观