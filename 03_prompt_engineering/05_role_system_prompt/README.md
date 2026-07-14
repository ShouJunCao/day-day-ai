# 3.5 角色设定与 System Prompt 设计模式

## 学习目标
掌握 System Prompt 的核心要素、常见角色模式和生产级构建器实现。

## 文件说明

| 文件 | 说明 |
|------|------|
| `role_system.py` | 核心模块：SystemPromptBuilder、DynamicSystemPrompt |
| `example_usage.py` | 5 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### System Prompt
- 具有最高优先级的全局指令
- 定义模型的人格、行为边界和输出风格
- 隐式附加到每一轮对话上下文中

### 常见角色模式
- **专家模式**：激发深层推理能力，减少浅显错误
- **审查者模式**：用于 Self-Refinement，专门找茬
- **导师模式**：引导式教学，不直接给答案

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/05_role_system_prompt
python example_usage.py
```
