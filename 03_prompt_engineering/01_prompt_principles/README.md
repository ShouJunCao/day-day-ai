# 3.1 Prompt 设计基本原则

## 学习目标
掌握 Prompt 设计的四大核心原则：清晰、具体、结构化、分步骤。

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompt_principles.py` | 核心模块：PromptBuilder、PromptTemplate、PromptRegistry |
| `example_usage.py` | 5 个使用示例，演示四大原则的实际应用 |
| `README.md` | 本文件 |

## 核心概念

### 四大原则

1. **清晰（Clear）**：消除歧义，明确任务类型和意图
2. **具体（Specific）**：给出约束条件和细节信息
3. **结构化（Structured）**：使用模板组织 Prompt 内容
4. **分步骤（Step-by-step）**：将复杂任务拆解为有序步骤

### 三大工具类

- **PromptBuilder**：数据类，快速构建结构化 Prompt
- **PromptTemplate**：基于 $variable 的可复用模板系统
- **PromptRegistry**：模板注册中心，支持版本管理和标签筛选

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/01_prompt_principles
python example_usage.py
```
