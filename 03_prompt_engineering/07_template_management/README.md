# 3.7 Prompt 模板管理与版本控制

## 学习目标
掌握 Prompt 模板化、基于 YAML 的管理方案及灰度发布机制。

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompt_manager.py` | 核心模块：PromptManager, PromptVersionController |
| `example_usage.py` | 4 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### 为什么需要管理？
- 硬编码导致修改困难、无版本追溯。
- 模板化实现配置与代码分离。

### 方案对比
- **本地 YAML + Git**：轻量，灵活，适合小团队。
- **Promptflow**：可视化编排，适合复杂流程。
- **LangSmith**：强大的评估与监控，适合大规模生产。

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/07_template_management
python example_usage.py
```
