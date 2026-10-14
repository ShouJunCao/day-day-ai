"""
example_usage.py — Kiro IDE Specs 驱动开发演示
演示 Spec 定义、任务生成、代码生成。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kiro_specs import (
    SpecManager,
    KiroCodeGenerator,
    SpecRequirement,
    Spec,
)


def demo_specs():
    print("=" * 60)
    print("  Spec 管理")
    print("=" * 60)
    
    sm = SpecManager()
    
    print("\n  已有 Specs:")
    for spec in sm.list_specs():
        print(f"    • {spec['name']} v{spec['version']} - {spec['status']}")
        print(f"      {spec['description']}")
        print(f"      架构: {spec['architecture']}")
        print(f"      需求数: {spec['requirements_count']}")
    
    # 创建新 Spec
    print("\n  创建新 Spec:")
    new_spec = sm.create_spec(
        name="数据分析服务",
        description="提供数据分析和可视化 API",
        requirements=[
            SpecRequirement("REQ-001", "数据查询接口", "must", "GET /api/data 返回数据集"),
            SpecRequirement("REQ-002", "统计分析接口", "should", "POST /api/analyze 返回统计结果"),
        ],
        architecture="FastAPI + Pandas + ECharts"
    )
    print(f"    创建: {new_spec.name} v{new_spec.version}")


def demo_tasks():
    print("\n" + "=" * 60)
    print("  任务生成与进度")
    print("=" * 60)
    
    sm = SpecManager()
    tasks = sm.generate_tasks("user_api")
    
    print(f"\n  为用户管理 API 生成 {len(tasks)} 个任务:")
    for i, task in enumerate(tasks):
        print(f"    {i+1}. [{task.requirement_id}] {task.description[:60]}...")
    
    print(f"\n  初始进度: {sm.get_progress('user_api')}")
    
    # 模拟完成
    sm.complete_task(0, ["models.py", "routes/register.py"])
    sm.complete_task(1, ["auth.py", "routes/login.py"])
    sm.complete_task(2, ["routes/users.py"])
    
    print(f"  完成 3 个任务后: {sm.get_progress('user_api')}")


def demo_code_generation():
    print("\n" + "=" * 60)
    print("  代码生成")
    print("=" * 60)
    
    gen = KiroCodeGenerator()
    
    # 生成模型
    model = gen.generate_model(
        "UserRegister", "用户注册请求",
        {
            "username": "str = Field(min_length=3, max_length=50)",
            "email": "EmailStr",
            "password": "str = Field(min_length=8)"
        }
    )
    print("\n  生成的 Pydantic 模型:")
    print("  " + "-" * 40)
    for line in model.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 40)
    
    # 生成路由
    route = gen.generate_route(
        "post", "/api/register", "register_user",
        "用户注册接口", "request: UserRegister"
    )
    print("\n  生成的 FastAPI 路由:")
    print("  " + "-" * 40)
    for line in route.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 40)
    
    # 生成测试
    test = gen.generate_test("register_success", "用户注册成功")
    print("\n  生成的测试用例:")
    print("  " + "-" * 40)
    for line in test.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 40)


def demo_spec_workflow():
    print("\n" + "=" * 60)
    print("  Specs 驱动完整工作流")
    print("=" * 60)
    
    print("""
    Kiro IDE 的 Specs 驱动工作流:
    
    1. 定义 Spec
       → 描述需求、验收标准、技术架构
    
    2. 生成任务
       → 每个需求自动转换为开发任务
    
    3. Agent 执行
       → Agent 读取 Spec，规划实现方案
       → 自动生成代码、测试、文档
    
    4. 进度跟踪
       → 实时更新任务状态
       → 验收标准自动验证
    
    5. 完成交付
       → 所有任务完成后，Spec 标记为 done
       → 生成完整的项目代码
    """)


if __name__ == "__main__":
    demo_specs()
    demo_tasks()
    demo_code_generation()
    demo_spec_workflow()
