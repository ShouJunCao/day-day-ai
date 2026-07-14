"""
role_system.py — 角色设定与 System Prompt 管理系统
包含多种角色模板、结构化构建器与验证机制

学习重点:
1. 常见角色模式（专家、审查者、导师等）
2. SystemPromptBuilder 结构化构建
3. 动态上下文注入与变量替换
4. Prompt 校验与 Token 估算
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import re


# ============================================================
# 第一部分：角色模板定义
# ============================================================

EXPERT_CODE_REVIEWER = """
# 角色
你是一位拥有 10 年经验的 Python 架构师，精通设计模式、并发编程和性能优化。

# 任务
审查用户提交的代码，指出潜在问题并提供改进建议。

# 审查维度
1. **正确性**：逻辑漏洞、边界条件、异常处理
2. **性能**：时间/空间复杂度、内存泄漏风险
3. **可维护性**：命名规范、代码结构、注释完整性
4. **安全性**：注入风险、敏感信息泄露、权限校验

# 输出要求
- 使用 Markdown 格式
- 严重问题标记为 🔴，建议标记为 🟡
- 必须提供修改后的代码示例
- 保持语气专业、客观、建设性
"""

CRITIC_PATTERN = """
# 角色
你是一个严苛的逻辑审查员。你的唯一目的是找出用户论点或代码中的漏洞。

# 行为准则
- 不要温和地指出问题，直接命中核心逻辑缺陷。
- 如果论证存在跳跃，请追问“为什么”。
- 如果代码有安全隐患，请指出具体利用场景。
- 只有在方案完美时才给出肯定（极少情况）。

# 输出格式
1. **主要漏洞**：[列出 1-3 个致命问题]
2. **次要风险**：[列出潜在风险]
3. **最终判定**：[通过 / 需修改 / 拒绝]
"""

MENTOR_PATTERN = """
# 角色
你是一位耐心的编程导师，擅长使用类比和苏格拉底式提问引导学生。

# 任务
帮助用户理解编程概念，但永远不要直接给出完整答案。

# 行为准则
1. 将复杂问题拆解为小步骤
2. 使用生活化的类比解释抽象概念
3. 如果用户卡住，给出提示而非答案
4. 鼓励用户尝试写代码，即使不完美

# 约束条件
- ❌ 除非用户明确要求，否则不要直接给代码
- ❌ 不要使用过于专业的术语，除非先解释它们
"""


# ============================================================
# 第二部分：System Prompt 构建器
# ============================================================

class SystemPromptBuilder:
    """
    System Prompt 结构化构建器。
    
    支持链式调用，自动处理空字段，
    并提供基础校验逻辑。
    """
    
    def __init__(self):
        self._role = ""
        self._context = []
        self._rules = []
        self._format = ""
        self._constraints = []
    
    def set_role(self, role: str) -> 'SystemPromptBuilder':
        """
        设定角色身份。
        
        参数:
            role: 角色描述字符串
        返回:
            self 用于链式调用
        """
        self._role = role
        return self
    
    def add_context(self, context: str) -> 'SystemPromptBuilder':
        """添加背景信息"""
        self._context.append(context)
        return self
    
    def add_rule(self, rule: str) -> 'SystemPromptBuilder':
        """添加行为准则"""
        self._rules.append(rule)
        return self
    
    def set_format(self, fmt: str) -> 'SystemPromptBuilder':
        """设定输出格式"""
        self._format = fmt
        return self
    
    def add_constraint(self, constraint: str) -> 'SystemPromptBuilder':
        """添加硬性约束（绝对不能做的事）"""
        self._constraints.append(constraint)
        return self
    
    def estimate_tokens(self) -> int:
        """
        估算当前 Prompt 的 Token 数量（粗略估算）。
        
        返回:
            预估 Token 数
        """
        text = self._assemble()
        # 英文/数字约 4 字符 1 token，中文约 1-1.5 字符 1 token
        # 这里使用简单的启发式估算
        return len(text) // 2
    
    def validate(self) -> list[str]:
        """
        校验 Prompt 的有效性。
        
        返回:
            错误信息列表，为空则有效
        """
        errors = []
        if not self._role:
            errors.append("未设定角色")
        if len(self._rules) == 0 and not self._context:
            errors.append("缺少行为准则或背景信息，模型可能缺乏指引")
        
        try:
            prompt_text = self._assemble()
        except ValueError:
            # 内容为空时无法组装，前面的规则已记录相应错误
            prompt_text = ""
        if len(prompt_text) > 4000:
            errors.append("Prompt 过长（>4000字符），可能占用过多 Context Window")
        
        return errors
    
    def _assemble(self) -> str:
        """
        组装 Prompt 文本（不触发校验）。
        
        此方法为 build()/validate()/estimate_tokens() 共用的核心逻辑，
        单独抽出以避免 build() 与 validate() 相互递归调用。
        
        返回:
            格式化后的 Prompt 字符串
        异常:
            ValueError: 如果未设定任何内容
        """
        parts = []
        
        if self._role:
            parts.append(f"# 角色\n{self._role}")
        
        if self._context:
            ctx_text = "\n".join(f"- {c}" for c in self._context)
            parts.append(f"# 背景信息\n{ctx_text}")
        
        if self._rules:
            rules_text = "\n".join(f"{i+1}. {r}" for i, r in enumerate(self._rules))
            parts.append(f"# 行为准则\n{rules_text}")
        
        if self._constraints:
            cons_text = "\n".join(f"- ❌ {c}" for c in self._constraints)
            parts.append(f"# 限制条件\n{cons_text}")
        
        if self._format:
            parts.append(f"# 输出格式\n{self._format}")
        
        if not parts:
            raise ValueError("System Prompt 不能为空，请至少设定角色")
        
        return "\n\n".join(parts)
    
    def build(self) -> str:
        """
        组装最终的 System Prompt（先校验后组装）。
        
        返回:
            格式化后的 Prompt 字符串
        异常:
            ValueError: 如果未设定角色
        """
        errors = self.validate()
        if errors:
            # 注意：这里选择 warning 而不是 fail，
            # 但在严格模式下可以改为 raise
            pass
        
        return self._assemble()


# ============================================================
# 第三部分：动态 System Prompt
# ============================================================

class DynamicSystemPrompt(SystemPromptBuilder):
    """
    支持动态变量注入的 System Prompt 构建器。
    """
    
    def __init__(self, user_locale: str = "zh"):
        super().__init__()
        self.locale = user_locale
    
    def set_role(self, role: str) -> 'DynamicSystemPrompt':
        locale_prefix = {
            "zh": "你是一个",
            "en": "You are a",
            "ja": "あなたは",
        }.get(self.locale, "你是一个")
        self._role = f"{locale_prefix} {role}"
        return self
    
    def inject_context(self, user_profile: dict) -> 'DynamicSystemPrompt':
        """根据用户画像注入个性化上下文"""
        self.add_context(f"用户等级：{user_profile.get('tier', 'Free')}")
        self.add_context(f"偏好语言：{user_profile.get('language', 'zh')}")
        
        if user_profile.get('tier') == 'Enterprise':
            self.add_constraint("允许调用高级 API")
        else:
            self.add_constraint("禁止调用付费 API")
        
        return self
