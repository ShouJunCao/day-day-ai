# 3.6 结构化输出（JSON Mode、XML）

## 学习目标
掌握结构化输出的核心原理、JSON/XML/Pydantic 三种主流方案及容错机制。

## 文件说明

| 文件 | 说明 |
|------|------|
| `structured_output.py` | 核心模块：解析器、提取器、校验器 |
| `example_usage.py` | 5 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### JSON Mode
- API 级强制输出 JSON
- 需配合 Prompt 中的 Schema 说明
- 稳定性高，但依赖模型支持

### XML 标签
- 适用于混合内容（自然语言 + 数据）
- 通用性强，所有模型可用
- 通过正则提取标签内容

### Pydantic 校验
- 强类型验证
- 支持自动重试修复
- 工业级数据质量保障

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/06_structured_output
python example_usage.py
```
