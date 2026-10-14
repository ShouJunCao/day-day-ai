"""
ai_coding_tools.py — AI 编码工具对比与演示
对比主流 AI 编码助手：Copilot、Cursor、Windsurf、Cline。
演示工具调用和代码生成模拟。
"""
import os
import re
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CodingTool:
    """编码工具定义"""
    name: str
    vendor: str
    tool_type: str
    features: List[str] = field(default_factory=list)
    price: str = ""
    best_for: str = ""
    is_free: bool = False


TOOLS_DB = [
    CodingTool(
        name="GitHub Copilot",
        vendor="GitHub / Microsoft",
        tool_type="inline",
        features=["代码补全", "对话", "CLI", "PR 描述"],
        price="$10/月",
        best_for="日常编码补全"
    ),
    CodingTool(
        name="Cursor",
        vendor="Anysphere",
        tool_type="ide",
        features=["代码补全", "Agent 模式", "代码库索引"],
        price="$20/月",
        best_for="IDE 深度集成"
    ),
    CodingTool(
        name="Windsurf (Codeium)",
        vendor="Exafunction",
        tool_type="ide",
        features=["Cascade 对话", "代码库感知", "多模型"],
        price="$15/月",
        best_for="代码库感知"
    ),
    CodingTool(
        name="Cline (Claude Dev)",
        vendor="开源社区",
        tool_type="agent",
        features=["自主执行", "终端操作", "文件读写", "免费"],
        price="免费（自带 API Key）",
        best_for="自主 Agent 编码",
        is_free=True
    ),
    CodingTool(
        name="GitHub Copilot Agent Mode",
        vendor="GitHub",
        tool_type="agent",
        features=["终端访问", "代码库理解", "VS Code 集成"],
        price="$39/月（Enterprise）",
        best_for="企业级 Agent 编码"
    ),
]


class CodeGenerator:
    """模拟 AI 代码生成"""
    
    TEMPLATES = {
        "fastapi": '''from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str

@app.get("/users")
async def get_users():
    return {"users": []}

@app.post("/users")
async def create_user(user: User):
    return {"message": "User created", "user": user.model_dump()}''',

        "dataclass": '''from dataclasses import dataclass, field
from typing import List

@dataclass
class Project:
    name: str
    tasks: List[str] = field(default_factory=list)
    completed: int = 0
    
    @property
    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        return self.completed / len(self.tasks) * 100
    
    def add_task(self, task: str):
        self.tasks.append(task)''',

        "decorator": '''import time
import functools
from typing import Callable, Any

def timer(func: Callable) -> Callable:
    """计算函数执行时间的装饰器"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  {func.__name__} 耗时: {elapsed:.4f}s")
        return result
    return wrapper''',

        "async": '''import asyncio
from typing import List, Dict

async def fetch_data(url: str) -> Dict:
    """模拟异步数据获取"""
    await asyncio.sleep(0.1)
    return {"url": url, "status": "ok"}

async def fetch_all(urls: List[str]) -> List[Dict]:
    """并发获取多个 URL"""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)''',

        "class_hierarchy": '''from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """Agent 基类"""
    
    @abstractmethod
    def run(self, task: str) -> Any:
        pass
    
    @abstractmethod
    def get_tools(self) -> list:
        pass

class DataAgent(BaseAgent):
    """数据分析 Agent"""
    
    def get_tools(self):
        return ["query", "analyze", "report"]
    
    def run(self, task: str) -> dict:
        return {"status": "done", "task": task}''',
    }


class ToolComparator:
    """工具对比引擎"""
    
    def has_feature(self, tool: CodingTool, feature: str) -> bool:
        """检查工具是否具有某功能"""
        if feature == "免费":
            return tool.is_free or "免费" in tool.price
        if feature == "代码补全":
            return any("补全" in f for f in tool.features)
        if feature == "对话":
            return any("对话" in f or "Cascade" in f for f in tool.features)
        if feature == "Agent 模式":
            return any("Agent" in f or "自主" in f for f in tool.features)
        if feature == "CLI":
            return any("CLI" in f or "终端" in f for f in tool.features)
        if feature == "代码库索引":
            return any("索引" in f or "感知" in f or "理解" in f for f in tool.features)
        return any(feature.lower() in f.lower() for f in tool.features)
    
    def compare_by_feature(self, feature: str) -> List[Dict[str, Any]]:
        """按功能对比工具"""
        results = []
        for tool in TOOLS_DB:
            has = self.has_feature(tool, feature)
            results.append({
                "name": tool.name,
                "has_feature": has,
                "type": tool.tool_type,
                "price": tool.price
            })
        return results
    
    def recommend(self, use_case: str) -> Dict[str, Any]:
        """根据用例推荐工具"""
        recommendations = {
            "补全": "GitHub Copilot",
            "IDE 集成": "Cursor",
            "代码库理解": "Windsurf",
            "自主编码": "Cline",
            "企业级": "GitHub Copilot Agent Mode",
            "免费": "Cline",
            "多模型": "Windsurf",
        }
        
        best = recommendations.get(use_case, "Cursor")
        tool = next((t for t in TOOLS_DB if t.name == best), None)
        
        return {
            "use_case": use_case,
            "recommended": best,
            "reason": tool.best_for if tool else "",
            "price": tool.price if tool else ""
        }
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有工具信息"""
        return [
            {
                "name": t.name,
                "vendor": t.vendor,
                "type": t.tool_type,
                "features": t.features,
                "price": t.price,
                "best_for": t.best_for,
                "is_free": t.is_free
            }
            for t in TOOLS_DB
        ]


if __name__ == "__main__":
    print("=" * 60)
    print("  AI 编码工具对比演示")
    print("=" * 60)

    comparator = ToolComparator()
    
    print("\n 1. 工具概览")
    for tool in comparator.get_all():
        print(f"    {tool['name']} ({tool['vendor']})")
        print(f"      类型: {tool['type']} | 价格: {tool['price']}")
        print(f"      最佳: {tool['best_for']}")
    
    print("\n 2. 功能对比: Agent 模式")
    results = comparator.compare_by_feature("Agent 模式")
    for r in results:
        icon = "✅" if r["has_feature"] else "❌"
        print(f"    {icon} {r['name']} ({r['type']})")
    
    print("\n⭐ 3. 推荐")
    cases = ["补全", "IDE 集成", "自主编码", "免费"]
    for case in cases:
        rec = comparator.recommend(case)
        print(f"    {case} → {rec['recommended']} ({rec['price']})")
    
    print("\n 4. 代码生成示例")
    gen = CodeGenerator()
    print(f"    可用模板: {list(gen.TEMPLATES.keys())}")
    sample = gen.TEMPLATES["fastapi"]
    print(f"    FastAPI 模板 (前 100 字符):")
    print(f"    {sample[:100]}...")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
