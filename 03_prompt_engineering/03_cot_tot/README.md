# 3.3 思维链（CoT）与思维树（Tree-of-Thought）

## 学习目标
掌握 CoT 和 ToT 两种推理引导技术的原理、实现和工程化应用。

## 文件说明

| 文件 | 说明 |
|------|------|
| `cot_tot.py` | 核心模块：ZeroShotCoT、FewShotCoT、TreeOfThought、ReasoningEngine |
| `example_usage.py` | 5 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### Chain-of-Thought（CoT）
- 引导模型逐步展示推理过程
- Zero-shot CoT：添加 "Let's think step by step"
- Few-shot CoT：在示例中展示推理步骤

### Tree-of-Thought（ToT）
- 同时探索多条推理路径
- BFS/DFS + beam search 找最优路径
- 每步生成候选 → LLM 评估 → 保留最优

### ReasoningEngine
- 统一推理引擎，自动选择策略
- auto 模式：评估复杂度 → 选择 CoT 或 ToT

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/03_cot_tot
python example_usage.py
```
