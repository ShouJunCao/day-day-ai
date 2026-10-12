"""
mcp_security.py — MCP 安全最佳实践
涵盖身份验证、授权控制、输入验证、数据脱敏、速率限制、审计日志。
"""
import os
import re
import json
import hashlib
import time
import logging
from typing import Optional, List, Dict, Any, Set, Callable
from dataclasses import dataclass, field


# ============================================================
# 模块：安全数据结构
# ============================================================

@dataclass
class SecurityContext:
    """安全上下文，维护用户身份、权限和配置"""
    user_id: str = "anonymous"
    authorized_tools: Set[str] = field(default_factory=set)
    api_key: Optional[str] = None

    def authorize_tool(self, tool_name: str):
        self.authorized_tools.add(tool_name)

    def is_authorized(self, tool_name: str) -> bool:
        return tool_name in self.authorized_tools


# ============================================================
# 模块：身份验证
# ============================================================

class MCPAuthenticator:
    """
    MCP 身份验证器
    
    支持 API 密钥和令牌认证。
    API 密钥以哈希值存储，而非明文。
    令牌支持过期和撤销。
    """
    
    def __init__(self):
        self.api_keys: Dict[str, str] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def register_api_key(self, key: str, user_id: str):
        """注册 API 密钥（存储哈希值）"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.api_keys[key_hash] = user_id

    def authenticate_api_key(self, key: str) -> Optional[str]:
        """验证 API 密钥"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.api_keys.get(key_hash)

    def issue_token(self, user_id: str, roles: List[str],
                    expires_in: int = 3600) -> str:
        """颁发认证令牌"""
        token = hashlib.sha256(
            f"{user_id}:{time.time()}:{os.urandom(16).hex()}".encode()
        ).hexdigest()
        self.tokens[token] = {
            "user_id": user_id,
            "roles": roles,
            "expires_at": time.time() + expires_in,
            "is_valid": True,
        }
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        info = self.tokens.get(token)
        if not info or not info["is_valid"]:
            return None
        if time.time() > info["expires_at"]:
            info["is_valid"] = False
            return None
        return info

    def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        if token in self.tokens:
            self.tokens[token]["is_valid"] = False
            return True
        return False


# ============================================================
# 模块：授权控制
# ============================================================

class MCPAuthorizer:
    """
    MCP 授权控制器
    
    实现基于角色的访问控制（RBAC）：
    - 角色定义权限集合
    - 用户分配一个或多个角色
    - 工具定义所需权限
    """
    
    ROLE_PERMISSIONS = {
        "admin": {"read", "write", "delete", "admin", "configure"},
        "editor": {"read", "write"},
        "viewer": {"read"},
        "guest": set(),
    }

    def __init__(self):
        self.user_roles: Dict[str, List[str]] = {}
        self.tool_permissions: Dict[str, Set[str]] = {}

    def assign_role(self, user_id: str, role: str):
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)

    def set_tool_permission(self, tool_name: str, required_permission: str):
        self.tool_permissions[tool_name] = {required_permission}

    def check_access(self, user_id: str, tool_name: str) -> bool:
        user_permissions = set()
        for role in self.user_roles.get(user_id, []):
            user_permissions.update(
                self.ROLE_PERMISSIONS.get(role, set())
            )
        required = self.tool_permissions.get(tool_name, set())
        return required.issubset(user_permissions)


# ============================================================
# 模块：输入安全
# ============================================================

class InputValidator:
    """
    输入安全处理器
    
    防御 SQL 注入、XSS、命令注入、路径遍历等攻击。
    采用白名单策略：只允许已知的安全输入通过。
    """
    
    SAFE_PATTERN = re.compile(r'^[\w\s\.,!?@\-]+$')
    SQL_KEYWORDS = {"DROP", "DELETE", "ALTER", "TRUNCATE", "EXEC"}
    DANGEROUS_TAGS = {"script", "iframe", "object", "embed", "form"}

    @staticmethod
    def validate_text(text: str) -> bool:
        if not text:
            return True
        return bool(InputValidator.SAFE_PATTERN.match(text))

    @staticmethod
    def sanitize_html(text: str) -> str:
        for tag in InputValidator.DANGEROUS_TAGS:
            text = re.sub(
                f'<{tag}[^>]*>.*?</{tag}>', '', text,
                flags=re.IGNORECASE | re.DOTALL
            )
            text = re.sub(f'<{tag}[^>]*/?>', '', text, flags=re.IGNORECASE)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    @staticmethod
    def validate_file_path(path: str, base_dir: str) -> Optional[str]:
        real_path = os.path.realpath(os.path.join(base_dir, path))
        real_base = os.path.realpath(base_dir)
        if not real_path.startswith(real_base):
            return None
        return real_path

    @staticmethod
    def validate_command(cmd: str, allowed: Set[str]) -> bool:
        if not cmd:
            return False
        cmd_name = cmd.split()[0] if ' ' in cmd else cmd
        return cmd_name in allowed


# ============================================================
# 模块：数据保护
# ============================================================

class DataProtector:
    """
    数据保护器
    
    处理敏感数据的脱敏和哈希存储。
    自动识别邮箱、API 密钥、信用卡号等敏感模式。
    """
    
    PATTERNS = {
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        "api_key": re.compile(r'\b(?:sk|pk|api)[-_]?[a-zA-Z0-9]{20,}\b'),
    }

    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        for name, pattern in DataProtector.PATTERNS.items():
            def replacer(match):
                original = match.group(0)
                if len(original) > 8:
                    return original[:4] + "*" * (len(original) - 8) + original[-4:]
                return "***"
            text = pattern.sub(replacer, text)
        return text

    @staticmethod
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


# ============================================================
# 模块：速率限制
# ============================================================

class RateLimiter:
    """
    速率限制器
    
    使用滑动窗口算法实现速率限制，
    防止 API 滥用和 DDoS 攻击。
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        self.requests[client_id] = [
            t for t in self.requests[client_id]
            if now - t < self.window
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        if client_id not in self.requests:
            return self.max_requests
        active = [t for t in self.requests[client_id] if now - t < self.window]
        return max(0, self.max_requests - len(active))


# ============================================================
# 模块：审计日志
# ============================================================

class AuditLogger:
    """
    审计日志记录器
    
    记录所有安全相关事件，用于事后分析和合规审计。
    日志格式为 JSON，便于集成到日志管理系统（如 ELK Stack）。
    """
    
    def __init__(self, log_file: str = "mcp_audit.log"):
        self.log_file = log_file

    def log(self, event_type: str, user_id: str,
            details: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "event": event_type,
            "user_id": user_id,
            "details": details,
            "success": success,
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        return log_entry

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        events = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except FileNotFoundError:
            pass
        return events[-limit:]


# ============================================================
# 模块：安全工具包装器
# ============================================================

class SecureTool:
    """
    安全工具包装器
    
    为普通工具函数添加安全检查：
    1. 权限验证
    2. 输入清理
    3. 输出脱敏
    """
    
    def __init__(self, name: str, func: Callable, context: SecurityContext):
        self.name = name
        self.func = func
        self.context = context

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 权限检查
        if not self.context.is_authorized(self.name):
            return {
                "error": "Access Denied",
                "message": f"User {self.context.user_id} not authorized for {self.name}"
            }
        
        # 2. 输入验证
        for key, value in arguments.items():
            if isinstance(value, str):
                if not InputValidator.validate_text(value):
                    return {
                        "error": "Invalid Input",
                        "message": f"Parameter {key} contains invalid characters"
                    }
        
        # 3. 执行工具
        try:
            result = self.func(**arguments)
        except Exception as e:
            return {"error": "Execution Error", "message": str(e)}
        
        # 4. 输出脱敏
        if isinstance(result, str):
            result = DataProtector.mask_sensitive_data(result)
        
        return {"success": True, "data": result}


# ============================================================
# 模块：示例工具
# ============================================================

def get_user_profile(user_id: str) -> str:
    return f"User {user_id}: admin@example.com, Phone: 138-0000-1234, API Key: sk-1234567890abcdef"

def query_database(query: str) -> str:
    return f"Query result for: {query}"


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP 安全最佳实践演示")
    print("=" * 60)

    # 1. 安全上下文
    print("\n 1. 安全上下文")
    context = SecurityContext(user_id="user_123")
    context.authorize_tool("get_user_profile")
    print(f"  用户: {context.user_id}")
    print(f"  授权工具: {context.authorized_tools}")

    # 2. 安全工具调用
    print("\n 2. 安全工具调用")
    tool = SecureTool("get_user_profile", get_user_profile, context)
    result = tool.execute({"user_id": "alice"})
    print(f"  授权调用: {result['data']}")

    tool2 = SecureTool("query_database", query_database, context)
    result2 = tool2.execute({"query": "SELECT * FROM users"})
    print(f"  未授权调用: {result2}")

    # 3. 输入验证
    print("\n 3. 输入验证")
    print(f"  'Hello World' 安全: {InputValidator.validate_text('Hello World')}")
    print(f"  '<script>' 安全: {InputValidator.validate_text('<script>alert(1)</script>')}")
    dirty = "Text <script>alert('XSS')</script> More"
    print(f"  HTML 清理: '{InputValidator.sanitize_html(dirty)}'")

    # 4. 数据保护
    print("\n 4. 数据保护")
    data = "Contact: admin@example.com, Key: sk-1234567890abcdef"
    print(f"  脱敏: {DataProtector.mask_sensitive_data(data)}")

    # 5. 身份验证
    print("\n 5. 身份验证")
    auth = MCPAuthenticator()
    auth.register_api_key("secret-key-123", "user_alice")
    uid = auth.authenticate_api_key("secret-key-123")
    print(f"  API Key 认证: {'成功' if uid else '失败'} ({uid})")
    token = auth.issue_token("user_alice", ["admin"])
    print(f"  令牌: {token[:20]}...")
    print(f"  令牌验证: {'有效' if auth.validate_token(token) else '无效'}")

    # 6. 授权控制
    print("\n 6. 授权控制")
    authorizer = MCPAuthorizer()
    authorizer.assign_role("alice", "admin")
    authorizer.assign_role("bob", "viewer")
    authorizer.set_tool_permission("admin_tool", "admin")
    authorizer.set_tool_permission("read_tool", "read")
    print(f"  Alice(admin) -> admin_tool: {authorizer.check_access('alice', 'admin_tool')}")
    print(f"  Bob(viewer) -> admin_tool: {authorizer.check_access('bob', 'admin_tool')}")

    # 7. 速率限制
    print("\n 7. 速率限制")
    limiter = RateLimiter(max_requests=5, window_seconds=10)
    for i in range(7):
        allowed = limiter.is_allowed("user_alice")
        print(f"  请求 {i+1}: {'允许' if allowed else '拒绝'}")

    # 8. 审计日志
    print("\n 8. 审计日志")
    audit = AuditLogger("mcp_audit_demo.log")
    audit.log("LOGIN", "user_alice", {"ip": "192.168.1.1"}, True)
    audit.log("TOOL_CALL", "user_alice", {"tool": "get_weather"}, True)
    audit.log("AUTH_FAILURE", "unknown", {"method": "tools/call"}, False)
    events = audit.get_recent_events()
    print(f"  事件数: {len(events)}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
