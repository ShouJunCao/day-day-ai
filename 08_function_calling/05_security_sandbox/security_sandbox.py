"""
security_sandbox.py — 工具权限控制与安全沙箱实现
"""
import os
import re
import json
import hashlib
from typing import Optional, List, Dict, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 模块：数据结构
# ============================================================

class PermissionLevel(Enum):
    """权限级别"""
    READ = "read"              # 只读
    WRITE = "write"            # 读写
    EXECUTE = "execute"        # 执行
    NETWORK = "network"        # 网络访问
    ADMIN = "admin"            # 管理员


class SandboxType(Enum):
    """沙箱类型"""
    NONE = "none"              # 无沙箱
    SUBPROCESS = "subprocess"  # 子进程隔离
    DOCKER = "docker"          # Docker 容器
    E2B = "e2b"               # E2B 云端沙箱


@dataclass
class ToolPermission:
    """工具权限定义"""
    tool_name: str
    allowed_permissions: Set[PermissionLevel]
    max_execution_time: float = 10.0
    rate_limit: int = 100  # 每分钟最大调用次数


@dataclass
class SecurityContext:
    """安全上下文"""
    user_id: str
    role: str
    permissions: Set[PermissionLevel] = field(default_factory=set)
    sandbox_type: SandboxType = SandboxType.SUBPROCESS


# ============================================================
# 模块：权限管理器
# ============================================================

class PermissionManager:
    """
    权限管理器：管理工具的访问权限。
    """

    def __init__(self):
        self.tool_permissions: Dict[str, ToolPermission] = {}
        self.user_roles: Dict[str, Set[PermissionLevel]] = {}
        self.call_counts: Dict[str, int] = {}  # 用于限速

    def register_tool(self, tool_name: str, permissions: Set[PermissionLevel],
                      max_execution_time: float = 10.0, rate_limit: int = 100):
        """注册工具权限"""
        self.tool_permissions[tool_name] = ToolPermission(
            tool_name=tool_name,
            allowed_permissions=permissions,
            max_execution_time=max_execution_time,
            rate_limit=rate_limit,
        )

    def set_user_role(self, user_id: str, permissions: Set[PermissionLevel]):
        """设置用户角色权限"""
        self.user_roles[user_id] = permissions

    def check_permission(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """检查用户是否有权限调用某个工具"""
        result = {"allowed": False, "reason": ""}

        # 1. 检查工具是否存在
        if tool_name not in self.tool_permissions:
            result["reason"] = f"工具 '{tool_name}' 未注册"
            return result

        # 2. 检查用户权限
        user_perms = self.user_roles.get(user_id, set())
        tool_perms = self.tool_permissions[tool_name].allowed_permissions

        # 用户必须拥有工具所需的所有权限
        if not tool_perms.issubset(user_perms):
            missing = tool_perms - user_perms
            result["reason"] = f"缺少权限: {', '.join(p.value for p in missing)}"
            return result

        # 3. 检查速率限制
        count = self.call_counts.get(tool_name, 0)
        if count >= self.tool_permissions[tool_name].rate_limit:
            result["reason"] = f"工具 '{tool_name}' 调用频率超限"
            return result

        result["allowed"] = True
        return result

    def record_call(self, tool_name: str):
        """记录调用（用于限速）"""
        self.call_counts[tool_name] = self.call_counts.get(tool_name, 0) + 1


# ============================================================
# 模块：安全沙箱
# ============================================================

class SecuritySandbox:
    """
    安全沙箱：在隔离环境中执行工具调用。
    """

    def __init__(self, sandbox_type: SandboxType = SandboxType.SUBPROCESS):
        self.sandbox_type = sandbox_type
        self.allowed_commands: Set[str] = set()

    def add_allowed_command(self, command: str):
        """添加允许执行的命令"""
        self.allowed_commands.add(command)

    def execute_in_sandbox(self, command: str, timeout: float = 10.0) -> str:
        """在沙箱中执行命令"""
        # 1. 检查命令是否在白名单中
        base_cmd = command.split()[0] if command.split() else ""
        if self.allowed_commands and base_cmd not in self.allowed_commands:
            return f"错误: 命令 '{base_cmd}' 不在白名单中"

        # 2. 根据沙箱类型执行
        if self.sandbox_type == SandboxType.NONE:
            return self._execute_direct(command)
        elif self.sandbox_type == SandboxType.SUBPROCESS:
            return self._execute_subprocess(command, timeout)
        elif self.sandbox_type == SandboxType.DOCKER:
            return self._execute_docker(command, timeout)
        elif self.sandbox_type == SandboxType.E2B:
            return self._execute_e2b(command, timeout)

        return f"错误: 未知沙箱类型 '{self.sandbox_type}'"

    def _execute_direct(self, command: str) -> str:
        """直接执行（无隔离，仅用于测试）"""
        return f"[直接执行] {command}"

    def _execute_subprocess(self, command: str, timeout: float) -> str:
        """子进程隔离执行"""
        # 实际实现会使用 subprocess.run
        return f"[子进程隔离] 执行: {command}, 超时: {timeout}s"

    def _execute_docker(self, command: str, timeout: float) -> str:
        """Docker 容器隔离执行"""
        return f"[Docker 容器] 执行: {command}, 超时: {timeout}s"

    def _execute_e2b(self, command: str, timeout: float) -> str:
        """E2B 云端沙箱执行"""
        return f"[E2B 云端] 执行: {command}, 超时: {timeout}s"


# ============================================================
# 模块：安全工具执行器
# ============================================================

class SecureToolExecutor:
    """
    安全工具执行器：结合权限控制和沙箱执行。
    """

    def __init__(self, permission_manager: PermissionManager,
                 sandbox: SecuritySandbox):
        self.permission_manager = permission_manager
        self.sandbox = sandbox

    def execute(self, user_id: str, tool_name: str,
                arguments: Dict[str, Any]) -> Dict[str, Any]:
        """安全执行工具"""
        # 1. 权限检查
        perm_result = self.permission_manager.check_permission(user_id, tool_name)
        if not perm_result["allowed"]:
            return {
                "success": False,
                "error": f"权限拒绝: {perm_result['reason']}",
            }

        # 2. 记录调用
        self.permission_manager.record_call(tool_name)

        # 3. 构建命令
        command = self._build_command(tool_name, arguments)

        # 4. 在沙箱中执行
        max_time = self.permission_manager.tool_permissions[tool_name].max_execution_time
        result = self.sandbox.execute_in_sandbox(command, timeout=max_time)

        return {
            "success": not result.startswith("错误:"),
            "result": result,
            "user_id": user_id,
            "tool_name": tool_name,
        }

    def _build_command(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """构建执行命令"""
        args_str = " ".join(f"--{k} {v}" for k, v in arguments.items())
        return f"{tool_name} {args_str}".strip()


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  工具权限控制与安全沙箱演示")
    print("=" * 60)

    # 1. 权限管理
    print("\n📋 权限管理:")
    pm = PermissionManager()
    pm.register_tool("weather", {PermissionLevel.READ, PermissionLevel.NETWORK})
    pm.register_tool("database", {PermissionLevel.READ, PermissionLevel.WRITE})
    pm.register_tool("shell", {PermissionLevel.EXECUTE})

    pm.set_user_role("user_1", {PermissionLevel.READ, PermissionLevel.NETWORK})
    pm.set_user_role("user_2", {PermissionLevel.READ, PermissionLevel.WRITE,
                                 PermissionLevel.EXECUTE, PermissionLevel.NETWORK})

    # 检查权限
    for uid in ["user_1", "user_2"]:
        for tool in ["weather", "database", "shell"]:
            result = pm.check_permission(uid, tool)
            status = "✅ 允许" if result["allowed"] else f"❌ {result['reason']}"
            print(f"  {uid} 调用 {tool}: {status}")

    # 2. 沙箱执行
    print("\n🔒 沙箱执行:")
    sandbox = SecuritySandbox(SandboxType.DOCKER)
    sandbox.add_allowed_command("weather")
    sandbox.add_allowed_command("query")

    for cmd in ["weather --city 北京", "rm -rf /", "query --db main"]:
        result = sandbox.execute_in_sandbox(cmd, timeout=5.0)
        print(f"  执行 '{cmd}' → {result}")

    # 3. 安全执行器
    print("\n🛡️ 安全工具执行器:")
    executor = SecureToolExecutor(pm, sandbox)

    result = executor.execute("user_1", "weather", {"city": "上海"})
    print(f"  user_1 调用 weather(上海): {result['success']}, 结果={result.get('result', '')[:50]}")

    result = executor.execute("user_1", "database", {"query": "SELECT *"})
    print(f"  user_1 调用 database: {result['success']}, 错误={result.get('error', '')}")

    # 4. 对比表
    print("\n" + "=" * 60)
    print("  沙箱类型对比")
    print("=" * 60)
    print(f"{'类型':<15s} {'隔离级别':<20s} {'适用场景':<20s}")
    print("-" * 55)
    print(f"{'无沙箱':<15s} {'无隔离':<20s} {'开发测试':<20s}")
    print(f"{'子进程':<15s} {'进程级隔离':<20s} {'轻量级任务':<20s}")
    print(f"{'Docker':<15s} {'容器级隔离':<20s} {'生产环境':<20s}")
    print(f"{'E2B':<15s} {'云端沙箱':<20s} {'多租户环境':<20s}")
