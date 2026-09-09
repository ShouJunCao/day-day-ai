"""
example_usage.py — 工具权限控制与安全沙箱演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_sandbox import (
    PermissionManager,
    SecuritySandbox,
    SecureToolExecutor,
    PermissionLevel,
    SandboxType,
)


def demo_permission_check():
    """演示权限检查"""
    print("=" * 60)
    print("  权限管理演示")
    print("=" * 60)

    pm = PermissionManager()
    pm.register_tool("weather", {PermissionLevel.READ, PermissionLevel.NETWORK})
    pm.register_tool("database", {PermissionLevel.READ, PermissionLevel.WRITE})
    pm.register_tool("shell", {PermissionLevel.EXECUTE})
    pm.register_tool("admin_panel", {PermissionLevel.ADMIN})

    # 不同角色
    pm.set_user_role("viewer", {PermissionLevel.READ})
    pm.set_user_role("editor", {PermissionLevel.READ, PermissionLevel.WRITE})
    pm.set_user_role("operator", {PermissionLevel.READ, PermissionLevel.WRITE,
                                   PermissionLevel.EXECUTE, PermissionLevel.NETWORK})
    pm.set_user_role("admin", {PermissionLevel.READ, PermissionLevel.WRITE,
                               PermissionLevel.EXECUTE, PermissionLevel.NETWORK,
                               PermissionLevel.ADMIN})

    roles = ["viewer", "editor", "operator", "admin"]
    tools = ["weather", "database", "shell", "admin_panel"]

    print(f"\n{'角色':<12s}", end="")
    for t in tools:
        print(f"{t:<15s}", end="")
    print()
    print("-" * 70)

    for role in roles:
        print(f"{role:<12s}", end="")
        for tool in tools:
            result = pm.check_permission(role, tool)
            print(f"{'✅' if result['allowed'] else '❌':<15s}", end="")
        print()


def demo_sandbox():
    """演示沙箱执行"""
    print("\n" + "=" * 60)
    print("  沙箱类型演示")
    print("=" * 60)

    sandbox_types = [
        (SandboxType.NONE, "无沙箱"),
        (SandboxType.SUBPROCESS, "子进程"),
        (SandboxType.DOCKER, "Docker"),
        (SandboxType.E2B, "E2B"),
    ]

    for stype, label in sandbox_types:
        sandbox = SecuritySandbox(stype)
        sandbox.add_allowed_command("weather")
        sandbox.add_allowed_command("query")

        print(f"\n  📦 {label}:")
        for cmd in ["weather --city 北京", "rm -rf /", "query --db main"]:
            result = sandbox.execute_in_sandbox(cmd, timeout=5.0)
            print(f"    '{cmd}' → {result}")


def demo_secure_executor():
    """演示安全执行器"""
    print("\n" + "=" * 60)
    print("  安全工具执行器")
    print("=" * 60)

    pm = PermissionManager()
    pm.register_tool("weather", {PermissionLevel.READ, PermissionLevel.NETWORK})
    pm.register_tool("database", {PermissionLevel.READ, PermissionLevel.WRITE})
    pm.set_user_role("user_1", {PermissionLevel.READ, PermissionLevel.NETWORK})
    pm.set_user_role("user_2", {PermissionLevel.READ, PermissionLevel.WRITE})

    sandbox = SecuritySandbox(SandboxType.DOCKER)
    sandbox.add_allowed_command("weather")
    sandbox.add_allowed_command("query")

    executor = SecureToolExecutor(pm, sandbox)

    # user_1: 有 weather 权限
    result = executor.execute("user_1", "weather", {"city": "上海"})
    print(f"\n  user_1 调用 weather(上海):")
    print(f"    成功: {result['success']}")
    if result.get("result"):
        print(f"    结果: {result['result'][:60]}...")

    # user_1: 无 database 权限
    result = executor.execute("user_1", "database", {"query": "SELECT *"})
    print(f"\n  user_1 调用 database:")
    print(f"    成功: {result['success']}")
    if result.get("error"):
        print(f"    错误: {result['error']}")

    # user_2: 有 database 权限
    result = executor.execute("user_2", "database", {"query": "SELECT *"})
    print(f"\n  user_2 调用 database:")
    print(f"    成功: {result['success']}")
    if result.get("result"):
        print(f"    结果: {result['result'][:60]}...")


def demo_comparison():
    """对比表"""
    print("\n" + "=" * 60)
    print("  沙箱类型对比")
    print("=" * 60)
    print(f"{'类型':<15s} {'隔离级别':<20s} {'适用场景':<20s}")
    print("-" * 55)
    print(f"{'无沙箱':<15s} {'无隔离':<20s} {'开发测试':<20s}")
    print(f"{'子进程':<15s} {'进程级隔离':<20s} {'轻量级任务':<20s}")
    print(f"{'Docker':<15s} {'容器级隔离':<20s} {'生产环境':<20s}")
    print(f"{'E2B':<15s} {'云端沙箱':<20s} {'多租户环境':<20s}")


if __name__ == "__main__":
    demo_permission_check()
    demo_sandbox()
    demo_secure_executor()
    demo_comparison()
