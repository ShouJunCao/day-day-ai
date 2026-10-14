"""
ai_coding_agents.py — AI 编码 Agent 对比与演示
对比主流 AI 编码 Agent：Claude Code、Codex CLI、OpenCode、Kiro。
演示 Agent 任务规划和代码生成模拟。
"""
import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CodingAgent:
    """编码 Agent 定义"""
    name: str
    vendor: str
    agent_type: str  # cli / ide / cloud
    features: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    price: str = ""
    best_for: str = ""


AGENTS_DB = [
    CodingAgent(
        name="Claude Code",
        vendor="Anthropic",
        agent_type="cli",
        features=["终端交互", "文件读写", "Git 操作", "代码库理解", "多步执行"],
        models=["Claude Sonnet 4", "Claude Opus 4"],
        price="$20/月（Pro）",
        best_for="终端驱动编码"
    ),
    CodingAgent(
        name="Codex CLI",
        vendor="OpenAI",
        agent_type="cli",
        features=["终端交互", "文件读写", "安全沙箱", "代码审查"],
        models=["GPT-4o", "o1", "o3"],
        price="$200/月（Pro）",
        best_for="安全编码执行"
    ),
    CodingAgent(
        name="OpenCode",
        vendor="开源社区",
        agent_type="cli",
        features=["终端交互", "文件读写", "自定义规则", "多模型支持"],
        models=["Claude", "GPT-4", "本地模型"],
        price="免费（开源）",
        best_for="自定义编码流程"
    ),
    CodingAgent(
        name="Kiro Agent",
        vendor="AWS",
        agent_type="ide",
        features=["Specs 驱动", "Agent 模式", "代码生成", "架构理解"],
        models=["Claude Sonnet", "Nova"],
        price="免费（开发者版）",
        best_for="Specs 驱动开发"
    ),
]


class CodeAgentSimulator:
    """模拟编码 Agent 执行"""
    
    TASK_TEMPLATES = {
        "create_api": '''# 任务: 创建 REST API
# Agent 执行步骤:

# Step 1: 分析需求
# - 需要用户管理的 CRUD 接口
# - 使用 FastAPI 框架
# - 包含验证和错误处理

# Step 2: 创建模型
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None

# Step 3: 创建路由
@app.post("/users")
async def create_user(user: UserCreate):
    if not user.name.strip():
        raise HTTPException(400, "Name required")
    return {"id": 1, **user.model_dump()}''',

        "refactor": '''# 任务: 重构代码
# Agent 执行步骤:

# Step 1: 分析现有代码
# - 识别重复逻辑
# - 发现可提取的函数
# - 检查类型提示

# Step 2: 提取公共函数
def validate_input(data: dict, required_keys: list) -> bool:
    return all(k in data for k in required_keys)

# Step 3: 应用重构
# - 替换重复代码为函数调用
# - 添加类型注解
# - 更新文档字符串''',

        "debug": '''# 任务: 调试代码
# Agent 执行步骤:

# Step 1: 复现问题
# - 运行测试用例
# - 观察错误输出
# - 定位问题代码行

# Step 2: 分析根因
# - 检查变量状态
# - 追踪调用链
# - 识别边界条件

# Step 3: 修复并验证
# - 添加边界检查
# - 更新测试用例
# - 运行完整测试集''',
    }
    
    def simulate_task(self, task_type: str) -> str:
        """模拟执行任务"""
        return self.TASK_TEMPLATES.get(task_type, "未知任务类型")


class AgentComparator:
    """Agent 对比引擎"""
    
    def has_feature(self, agent: CodingAgent, feature: str) -> bool:
        """检查 Agent 是否具有某功能"""
        return any(feature.lower() in f.lower() for f in agent.features)
    
    def compare_by_feature(self, feature: str) -> List[Dict[str, Any]]:
        """按功能对比 Agent"""
        results = []
        for agent in AGENTS_DB:
            has = self.has_feature(agent, feature)
            results.append({
                "name": agent.name,
                "has_feature": has,
                "type": agent.agent_type,
                "price": agent.price
            })
        return results
    
    def recommend(self, use_case: str) -> Dict[str, Any]:
        """根据用例推荐 Agent"""
        recommendations = {
            "终端驱动": "Claude Code",
            "安全编码": "Codex CLI",
            "自定义流程": "OpenCode",
            "Specs 驱动": "Kiro Agent",
            "免费": "OpenCode",
            "多模型": "OpenCode",
        }
        
        best = recommendations.get(use_case, "Claude Code")
        agent = next((a for a in AGENTS_DB if a.name == best), None)
        
        return {
            "use_case": use_case,
            "recommended": best,
            "reason": agent.best_for if agent else "",
            "price": agent.price if agent else ""
        }
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有 Agent 信息"""
        return [
            {
                "name": a.name,
                "vendor": a.vendor,
                "type": a.agent_type,
                "features": a.features,
                "models": a.models,
                "price": a.price,
                "best_for": a.best_for
            }
            for a in AGENTS_DB
        ]


if __name__ == "__main__":
    print("=" * 60)
    print("  AI 编码 Agent 对比演示")
    print("=" * 60)

    comparator = AgentComparator()
    
    print("\n 1. Agent 概览")
    for agent in comparator.get_all():
        print(f"    {agent['name']} ({agent['vendor']})")
        print(f"      类型: {agent['type']} | 价格: {agent['price']}")
        print(f"      模型: {', '.join(agent['models'])}")
        print(f"      最佳: {agent['best_for']}")
    
    print("\n 2. 功能对比: 终端交互")
    results = comparator.compare_by_feature("终端交互")
    for r in results:
        icon = "✅" if r["has_feature"] else "❌"
        print(f"    {icon} {r['name']} ({r['type']})")
    
    print("\n⭐ 3. 推荐")
    cases = ["终端驱动", "安全编码", "自定义流程", "免费"]
    for case in cases:
        rec = comparator.recommend(case)
        print(f"    {case} → {rec['recommended']} ({rec['price']})")
    
    print("\n 4. 任务模拟")
    sim = CodeAgentSimulator()
    task = sim.simulate_task("create_api")
    print(f"    创建 API 任务模拟:")
    print(f"    {task[:100]}...")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
