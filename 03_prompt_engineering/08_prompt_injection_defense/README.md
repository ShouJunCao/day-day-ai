# 3.8 Prompt 注入攻击类型与防御策略

## 学习目标
掌握 Prompt 注入的原理、常见攻击类型及多层防御体系。

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompt_defense.py` | 核心模块：PromptShield, ToolSandbox |
| `example_usage.py` | 3 个使用示例 |
| `README.md` | 本文件 |

## 核心概念

### 注入类型
- **直接注入**：用户输入中直接包含恶意指令。
- **间接注入**：恶意指令隐藏在外部数据源（网页、API 响应）中。
- **越狱 (Jailbreak)**：通过角色扮演等手段绕过安全限制。

### 防御策略
1. **输入过滤**：关键词匹配、正则检测、LLM 审查。
2. **指令隔离**：使用 XML 标签包裹用户数据。
3. **沙箱与权限**：限制模型可执行的工具范围。
4. **输出审计**：防止敏感信息泄露。

## 运行方式

```bash
cd ~/Desktop/天天AI/workspace/03_prompt_engineering/08_prompt_injection_defense
python example_usage.py
```
