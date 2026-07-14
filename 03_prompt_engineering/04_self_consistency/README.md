# 3.4 自洽性（Self-Consistency）与多数投票

## 学习目标
掌握 Self-Consistency 的核心原理、多数投票策略和生产级实现。

## 文件说明

| 文件 | 说明 |
|------|------|
| `self_consistency.py` | 核心模块：SelfConsistencyEngine、SamplingConfig、AnswerNormalizer |
| `example_usage.py` | 5 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### Self-Consistency
通过对同一问题多次采样（高 temperature），利用多数投票选出最一致的答案。

### 早期终止
当某个答案的票数占比达到共识阈值时，提前结束采样，节省成本。

### 答案规范化
提取答案后去除前缀/后缀、标点符号，提高精确匹配率。

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/04_self_consistency
python example_usage.py
```
