"""
workflow_best_practices.py — AI 开发工作流最佳实践
演示 AI 辅助开发的标准流程：需求分析、架构设计、编码实现、测试验证、代码审查、部署上线。
"""
import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowStage:
    """工作流阶段"""
    name: str
    description: str
    ai_tools: List[str] = field(default_factory=list)
    human_tasks: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)


WORKFLOW_STAGES = [
    WorkflowStage(
        name="需求分析",
        description="明确功能需求和验收标准",
        ai_tools=["需求文档生成", "用户故事转换"],
        human_tasks=["需求确认", "优先级排序"],
        deliverables=["PRD", "用户故事", "验收标准"]
    ),
    WorkflowStage(
        name="架构设计",
        description="设计系统架构和技术选型",
        ai_tools=["架构图生成", "技术栈推荐"],
        human_tasks=["架构评审", "技术决策"],
        deliverables=["架构文档", "技术选型报告"]
    ),
    WorkflowStage(
        name="编码实现",
        description="使用 AI 辅助编写代码",
        ai_tools=["代码补全", "代码生成", "重构建议"],
        human_tasks=["代码审查", "逻辑确认"],
        deliverables=["源代码", "代码注释"]
    ),
    WorkflowStage(
        name="测试验证",
        description="编写和运行测试用例",
        ai_tools=["测试用例生成", "Bug 定位"],
        human_tasks=["测试场景设计", "验收测试"],
        deliverables=["测试报告", "覆盖率报告"]
    ),
    WorkflowStage(
        name="代码审查",
        description="AI + 人工双重审查",
        ai_tools=["静态分析", "代码规范检查"],
        human_tasks=["逻辑审查", "安全审查"],
        deliverables=["审查报告", "修复记录"]
    ),
    WorkflowStage(
        name="部署上线",
        description="CI/CD 自动化部署",
        ai_tools=["部署脚本生成", "监控配置"],
        human_tasks=["上线审批", "灰度发布"],
        deliverables=["部署记录", "监控告警"]
    ),
]


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self):
        self.stages = WORKFLOW_STAGES.copy()
        self.current_stage = 0
    
    def advance(self) -> Optional[WorkflowStage]:
        """进入下一阶段"""
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            return self.stages[self.current_stage]
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        return {
            "current_stage": self.stages[self.current_stage].name if self.stages else "N/A",
            "stage_index": self.current_stage,
            "total_stages": len(self.stages),
            "progress_pct": f"{(self.current_stage + 1) / len(self.stages) * 100:.0f}%" if self.stages else "0%"
        }


class CodeQualityChecker:
    """代码质量检查"""
    
    RULES = {
        "naming": "遵循 PEP 8 命名规范",
        "typing": "函数签名包含类型注解",
        "docstring": "所有公开函数有文档字符串",
        "complexity": "圈复杂度 <= 10",
        "coverage": "测试覆盖率 >= 80%",
    }
    
    def check(self, code: str) -> Dict[str, Any]:
        """检查代码质量"""
        results = {}
        
        has_snake = bool(re.search(r'def [a-z_]+\(', code))
        results["naming"] = {"passed": has_snake, "rule": self.RULES["naming"]}
        
        has_type_hints = bool(re.search(r'def \w+\([^)]*:\s*\w+', code))
        results["typing"] = {"passed": has_type_hints, "rule": self.RULES["typing"]}
        
        has_docstring = bool(re.search(r'""".*?"""', code, re.DOTALL))
        results["docstring"] = {"passed": has_docstring, "rule": self.RULES["docstring"]}
        
        return results


if __name__ == "__main__":
    print("=" * 60)
    print("  AI 开发工作流最佳实践演示")
    print("=" * 60)
    
    engine = WorkflowEngine()
    
    print("\n 1. 工作流阶段")
    for i, stage in enumerate(engine.stages):
        print(f"    {i+1}. {stage.name}: {stage.description}")
        print(f"       AI 工具: {', '.join(stage.ai_tools)}")
        print(f"       交付物: {', '.join(stage.deliverables)}")
    
    print("\n 2. 进度跟踪")
    print(f"    初始: {engine.get_progress()}")
    for _ in range(3):
        engine.advance()
    print(f"    推进 3 阶段后: {engine.get_progress()}")
    
    print("\n⭐ 3. 代码质量检查")
    checker = CodeQualityChecker()
    sample_code = '''
def calculate_average(numbers: list[float]) -> float:
    """计算列表平均值"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
'''
    results = checker.check(sample_code)
    for rule, result in results.items():
        icon = "✅" if result["passed"] else "❌"
        print(f"    {icon} {rule}: {result['rule']}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
