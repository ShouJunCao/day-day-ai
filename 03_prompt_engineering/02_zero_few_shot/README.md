# 3.2 零样本（Zero-shot）与少样本（Few-shot）提示

## 学习目标
理解 Zero-shot 和 Few-shot 提示的核心概念、适用场景和工程化实现。

## 文件说明

| 文件 | 说明 |
|------|------|
| `zero_few_shot.py` | 核心模块：ZeroShotPrompt、FewShotPrompt、ExampleLibrary |
| `example_usage.py` | 5 个使用示例，演示 Zero-shot 和 Few-shot 的实际应用 |
| `README.md` | 本文件 |

## 核心概念

### Zero-shot（零样本）
- 不提供任何示例，直接让模型完成任务
- 依赖模型预训练时学到的通用知识
- 适用于：通用任务、快速验证、Token 预算有限的场景

### Few-shot（少样本）
- 提供 1-N 个示例（通常 3-5 个），让模型学习模式后完成任务
- 通过示例补充领域知识，提高输出一致性
- 适用于：标准化任务、专业领域、需要高一致性的场景

### 决策框架
- 任务简单通用 → Zero-shot
- 输出格式固定 → Few-shot
- 领域专业性强 → Few-shot
- 快速原型验证 → Zero-shot
- Token 预算有限 → Zero-shot

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/02_zero_few_shot
python example_usage.py
```
