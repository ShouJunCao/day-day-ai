"""
framework_comparison.py — Agent 框架对比与实现演示
对比 LangGraph、AutoGen、CrewAI、OpenAI Agents SDK、Dify 五大主流 Agent 框架。
包含基于 LLM 的框架推荐助手。
"""
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from openai import OpenAI

# 阿里云 DashScope 配置
DASHSCOPE_API_KEY = os.getenv("API_KEY", "sk-492...81ff")
DASHSCOPE_BASE_URL = os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DASHSCOPE_MODEL = os.getenv("MODEL_NAME", "qwen3.7-max")

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
)

# ============================================================
# 模块：框架特性定义
# ============================================================

@dataclass
class FrameworkFeature:
    """框架特性评分"""
    name: str
    agent_loop: str  # Agent 循环类型
    multi_agent: bool  # 是否支持多 Agent
    graph_support: bool  # 是否支持图编排
    code_complexity: str  # 代码复杂度（低/中/高）
    learning_curve: str  # 学习曲线（低/中/高）
    best_for: str  # 适用场景


# ============================================================
# 模块：五大框架对比数据
# ============================================================

FRAMEWORKS: List[FrameworkFeature] = [
    FrameworkFeature(
        name="LangGraph",
        agent_loop="自定义状态机",
        multi_agent=True,
        graph_support=True,
        code_complexity="高",
        learning_curve="高",
        best_for="复杂多步工作流、需要精细控制的应用"
    ),
    FrameworkFeature(
        name="AutoGen",
        agent_loop="对话驱动",
        multi_agent=True,
        graph_support=False,
        code_complexity="中",
        learning_curve="中",
        best_for="多 Agent 协作、代码生成、对话场景"
    ),
    FrameworkFeature(
        name="CrewAI",
        agent_loop="任务驱动",
        multi_agent=True,
        graph_support=False,
        code_complexity="低",
        learning_curve="低",
        best_for="团队协作、角色扮演、快速原型"
    ),
    FrameworkFeature(
        name="OpenAI Agents SDK",
        agent_loop="函数调用驱动",
        multi_agent=False,
        graph_support=False,
        code_complexity="低",
        learning_curve="低",
        best_for="轻量级 Agent、OpenAI 生态集成"
    ),
    FrameworkFeature(
        name="Dify",
        agent_loop="可视化编排",
        multi_agent=True,
        graph_support=True,
        code_complexity="低",
        learning_curve="低",
        best_for="非技术用户、可视化工作流、生产部署"
    ),
]

# ============================================================
# 模块：框架推荐助手（使用真实模型调用）
# ============================================================

class FrameworkAdvisor:
    """
    基于 LLM 的框架选择建议助手
    
    分析用户需求，结合框架特性数据，
    通过大模型推理给出最适合的框架推荐。
    """
    
    PROMPT_TEMPLATE = """你是一个 AI 开发专家，擅长选择合适的 Agent 开发框架。
请根据用户的需求和项目特点，从以下框架中选择最合适的一个，并给出推荐理由。

可选框架：
{frameworks_data}

用户需求：
{requirements}

请按以下格式输出：
推荐框架: <框架名称>
推荐理由: <详细理由，说明为什么该框架最适合此需求>
替代方案: <如果不选推荐框架，次优的选择是什么>
注意事项: <使用该框架时需要注意的问题>
"""

    def __init__(self):
        self.frameworks_data = self._format_frameworks_data()

    def _format_frameworks_data(self) -> str:
        """格式化框架数据为文本"""
        lines = []
        for fw in FRAMEWORKS:
            lines.append(
                f"- {fw.name}: {fw.best_for} "
                f"(多Agent:{'是' if fw.multi_agent else '否'}, "
                f"图编排:{'支持' if fw.graph_support else '不支持'}, "
                f"复杂度:{fw.code_complexity})"
            )
        return "\n".join(lines)

    def recommend(self, requirements: str) -> Dict[str, Any]:
        """调用 LLM 进行框架推荐"""
        prompt = self.PROMPT_TEMPLATE.format(
            frameworks_data=self.frameworks_data,
            requirements=requirements
        )
        
        try:
            response = client.chat.completions.create(
                model=DASHSCOPE_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个专业的 AI 框架选择顾问。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if content is None:
                return {"error": "Empty response from LLM"}
            result_text = content.strip()
            
            # 解析结果（简单解析）
            lines = result_text.split("\n")
            recommendation = {
                "raw_output": result_text,
                "framework": "",
                "reason": "",
                "alternative": "",
                "notes": ""
            }
            
            for line in lines:
                if "推荐框架" in line:
                    recommendation["framework"] = line.split(":", 1)[-1].strip()
                elif "推荐理由" in line:
                    recommendation["reason"] = line.split(":", 1)[-1].strip()
                elif "替代方案" in line:
                    recommendation["alternative"] = line.split(":", 1)[-1].strip()
                elif "注意事项" in line:
                    recommendation["notes"] = line.split(":", 1)[-1].strip()
            
            return recommendation
            
        except Exception as e:
            return {"error": str(e)}


# ============================================================
# 模块：代码复杂度分析器
# ============================================================

class CodeComplexityAnalyzer:
    """
    代码复杂度分析器
    
    评估不同框架实现相同功能所需的代码量。
    """
    
    @staticmethod
    def estimate_lines(framework: str, task: str) -> int:
        """估算实现特定任务所需的代码行数"""
        # 基于经验的估算值
        base_lines = {
            "LangGraph": 80,
            "AutoGen": 50,
            "CrewAI": 30,
            "OpenAI Agents SDK": 25,
            "Dify": 10  # 可视化配置，代码最少
        }
        
        # 任务复杂度系数
        complexity_multiplier = 1.0
        if "多步骤" in task or "复杂" in task:
            complexity_multiplier = 1.5
        if "多 Agent" in task:
            complexity_multiplier *= 1.3
        
        return int(base_lines.get(framework, 50) * complexity_multiplier)


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Agent 框架对比演示")
    print("=" * 60)

    # 1. 框架概览
    print("\n📊 1. 五大框架概览")
    print(f"{'=' * 50}")
    for fw in FRAMEWORKS:
        print(f"\n📦 {fw.name}")
        print(f"   Agent 循环: {fw.agent_loop}")
        print(f"   多 Agent: {'支持' if fw.multi_agent else '不支持'}")
        print(f"   图编排: {'支持' if fw.graph_support else '不支持'}")
        print(f"   代码复杂度: {fw.code_complexity}")
        print(f"   学习曲线: {fw.learning_curve}")
        print(f"   最佳场景: {fw.best_for}")

    # 2. 代码复杂度估算
    print("\n📏 2. 代码复杂度估算")
    analyzer = CodeComplexityAnalyzer()
    task = "构建一个多步骤数据分析 Agent"
    print(f"   任务: {task}")
    for fw in FRAMEWORKS:
        lines = analyzer.estimate_lines(fw.name, task)
        print(f"   {fw.name}: 约 {lines} 行代码")

    # 3. 框架推荐（真实模型调用）
    print("\n🤖 3. 基于 LLM 的框架推荐")
    advisor = FrameworkAdvisor()
    
    scenarios = [
        "我需要构建一个企业级的复杂工作流，需要精细控制每个步骤的状态转换。",
        "我想让多个 AI 角色互相讨论，共同解决一个编程问题。",
        "我们团队没有太多编程经验，希望用拖拽的方式构建 AI 应用。",
        "只需要一个简单的助手，能调用几个 API 工具就行。"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- 场景 {i} ---")
        print(f"需求: {scenario}")
        result = advisor.recommend(scenario)
        if "error" not in result:
            print(f"推荐: {result.get('framework', 'N/A')}")
            print(f"理由: {result.get('reason', 'N/A')[:50]}...")
        else:
            print(f"错误: {result['error']}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
