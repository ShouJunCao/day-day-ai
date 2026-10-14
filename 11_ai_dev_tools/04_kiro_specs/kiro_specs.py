"""
kiro_specs.py — Kiro IDE Specs 驱动开发演示
演示 Specs 定义、Agent 模式、架构理解和代码生成。
"""
import os
import re
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================
# 模块：Spec 定义
# ============================================================

@dataclass
class SpecRequirement:
    """Spec 需求项"""
    id: str
    description: str
    priority: str  # must / should / could
    acceptance_criteria: str = ""


@dataclass
class Spec:
    """Spec 定义"""
    name: str
    version: str
    description: str
    requirements: List[SpecRequirement] = field(default_factory=list)
    architecture: str = ""
    created_at: str = ""
    status: str = "draft"


@dataclass
class SpecTask:
    """Spec 任务"""
    spec_name: str
    requirement_id: str
    description: str
    status: str = "pending"  # pending / in_progress / done
    files_created: List[str] = field(default_factory=list)
    tests_passed: bool = False


# ============================================================
# 模块：Spec 示例
# ============================================================

EXAMPLE_SPECS = {
    "user_api": Spec(
        name="用户管理 API",
        version="1.0",
        description="实现用户注册、登录、查询、更新的 REST API",
        requirements=[
            SpecRequirement(
                id="REQ-001",
                description="用户注册接口",
                priority="must",
                acceptance_criteria="POST /api/register 接受用户名、邮箱、密码，返回用户 ID"
            ),
            SpecRequirement(
                id="REQ-002",
                description="用户登录接口",
                priority="must",
                acceptance_criteria="POST /api/login 接受邮箱和密码，返回 JWT Token"
            ),
            SpecRequirement(
                id="REQ-003",
                description="用户信息查询",
                priority="should",
                acceptance_criteria="GET /api/users/:id 返回用户详细信息"
            ),
            SpecRequirement(
                id="REQ-004",
                description="密码加密存储",
                priority="must",
                acceptance_criteria="密码使用 bcrypt 加密后存储"
            ),
        ],
        architecture="FastAPI + SQLAlchemy + PostgreSQL",
        status="active"
    ),
    
    "data_pipeline": Spec(
        name="数据处理流水线",
        version="1.0",
        description="构建 ETL 数据处理流水线",
        requirements=[
            SpecRequirement(
                id="REQ-001",
                description="数据提取模块",
                priority="must",
                acceptance_criteria="从 CSV/JSON/API 提取数据"
            ),
            SpecRequirement(
                id="REQ-002",
                description="数据转换模块",
                priority="must",
                acceptance_criteria="清洗、标准化、聚合数据"
            ),
            SpecRequirement(
                id="REQ-003",
                description="数据加载模块",
                priority="should",
                acceptance_criteria="将处理后的数据写入数据库或文件"
            ),
        ],
        architecture="Python + Pandas + Apache Airflow",
        status="active"
    ),
}


# ============================================================
# 模块：Spec 管理器
# ============================================================

class SpecManager:
    """Spec 管理器"""
    
    def __init__(self):
        self.specs: Dict[str, Spec] = EXAMPLE_SPECS.copy()
        self.tasks: List[SpecTask] = []
    
    def create_spec(self, name: str, description: str,
                    requirements: List[SpecRequirement],
                    architecture: str = "") -> Spec:
        """创建新 Spec"""
        spec = Spec(
            name=name,
            version="1.0",
            description=description,
            requirements=requirements,
            architecture=architecture,
            created_at=datetime.now().isoformat(),
            status="draft"
        )
        self.specs[name] = spec
        return spec
    
    def get_spec(self, name: str) -> Optional[Spec]:
        return self.specs.get(name)
    
    def list_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": s.name,
                "version": s.version,
                "description": s.description,
                "requirements_count": len(s.requirements),
                "architecture": s.architecture,
                "status": s.status
            }
            for s in self.specs.values()
        ]
    
    def generate_tasks(self, spec_name: str) -> List[SpecTask]:
        """根据 Spec 生成任务"""
        spec = self.specs.get(spec_name)
        if not spec:
            return []
        
        tasks = []
        for req in spec.requirements:
            task = SpecTask(
                spec_name=spec_name,
                requirement_id=req.id,
                description=f"实现: {req.description}\n验收: {req.acceptance_criteria}"
            )
            tasks.append(task)
            self.tasks.append(task)
        
        return tasks
    
    def complete_task(self, task_index: int, files: List[str]):
        """完成任务"""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].status = "done"
            self.tasks[task_index].files_created = files
            self.tasks[task_index].tests_passed = True
    
    def get_progress(self, spec_name: str) -> Dict[str, Any]:
        """获取 Spec 进度"""
        spec_tasks = [t for t in self.tasks if t.spec_name == spec_name]
        total = len(spec_tasks)
        done = sum(1 for t in spec_tasks if t.status == "done")
        
        return {
            "spec": spec_name,
            "total": total,
            "done": done,
            "pending": total - done,
            "progress": f"{done}/{total} ({done/total*100:.0f}%)" if total > 0 else "0%"
        }


# ============================================================
# 模块：代码生成器
# ============================================================

class KiroCodeGenerator:
    """Kiro 代码生成器"""
    
    PATTERNS = {
        "fastapi_model": '''from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class {class_name}(BaseModel):
    """{description}"""
{fields}''',

        "fastapi_route": '''from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

@{method}("{path}")
async def {func_name}({params}):
    """{description}"""
    # TODO: 实现业务逻辑
    return {{"message": "{func_name} executed"}}''',

        "test_case": '''import pytest
from fastapi.testclient import TestClient

def test_{test_name}():
    """测试 {description}"""
    # TODO: 编写测试用例
    assert True''',
    }
    
    def generate_model(self, class_name: str, description: str,
                       fields: Dict[str, str]) -> str:
        """生成 Pydantic 模型"""
        field_strs = []
        for name, type_hint in fields.items():
            field_strs.append(f"    {name}: {type_hint}")
        
        return self.PATTERNS["fastapi_model"].format(
            class_name=class_name,
            description=description,
            fields="\n".join(field_strs)
        )
    
    def generate_route(self, method: str, path: str, func_name: str,
                       description: str, params: str = "") -> str:
        """生成路由"""
        return self.PATTERNS["fastapi_route"].format(
            method=method, path=path, func_name=func_name,
            description=description, params=params
        )
    
    def generate_test(self, test_name: str, description: str) -> str:
        """生成测试用例"""
        return self.PATTERNS["test_case"].format(
            test_name=test_name, description=description
        )


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Kiro IDE Specs 驱动开发演示")
    print("=" * 60)

    # 1. Spec 管理
    print("\n 1. Spec 管理")
    sm = SpecManager()
    
    print(f"  已有 Specs:")
    for spec in sm.list_specs():
        print(f"    • {spec['name']} v{spec['version']} - {spec['status']}")
        print(f"      {spec['description']}")
        print(f"      架构: {spec['architecture']}")
        print(f"      需求数: {spec['requirements_count']}")
    
    # 2. 任务生成
    print("\n 2. 任务生成")
    tasks = sm.generate_tasks("user_api")
    print(f"  为用户管理 API 生成 {len(tasks)} 个任务:")
    for i, task in enumerate(tasks):
        print(f"    {i+1}. [{task.requirement_id}] {task.description[:50]}...")
    
    # 3. 进度跟踪
    print("\n 3. 进度跟踪")
    progress = sm.get_progress("user_api")
    print(f"  {progress}")
    
    # 模拟完成任务
    sm.complete_task(0, ["models.py", "routes.py"])
    sm.complete_task(1, ["auth.py", "routes.py"])
    progress = sm.get_progress("user_api")
    print(f"  完成后: {progress}")

    # 4. 代码生成
    print("\n⭐ 4. 代码生成")
    gen = KiroCodeGenerator()
    
    model = gen.generate_model(
        "UserRegister",
        "用户注册请求",
        {
            "username": "str = Field(min_length=3, max_length=50)",
            "email": "EmailStr",
            "password": "str = Field(min_length=8)"
        }
    )
    print(f"  生成的模型:")
    print(f"  {model}")
    
    route = gen.generate_route(
        "post", "/api/register", "register_user",
        "用户注册接口", "request: UserRegister"
    )
    print(f"\n  生成的路由:")
    print(f"  {route}")
    
    test = gen.generate_test("register_user", "用户注册")
    print(f"\n  生成的测试:")
    print(f"  {test}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
