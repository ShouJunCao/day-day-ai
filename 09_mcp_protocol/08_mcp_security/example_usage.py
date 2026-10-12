"""
example_usage.py — MCP 安全最佳实践演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_security import (
    SecurityContext,
    InputValidator,
    DataProtector,
    SecureTool,
    MCPAuthenticator,
    MCPAuthorizer,
    RateLimiter,
    AuditLogger,
    get_user_profile,
    query_database,
)


def demo_security_context():
    print("=" * 60)
    print("  安全上下文")
    print("=" * 60)
    context = SecurityContext(user_id="user_123")
    context.authorize_tool("get_user_profile")
    print(f"  用户: {context.user_id}")
    print(f"  授权工具: {context.authorized_tools}")
    print(f"  get_user_profile 授权: {context.is_authorized('get_user_profile')}")
    print(f"  query_database 授权: {context.is_authorized('query_database')}")


def demo_tool_security():
    print("\n" + "=" * 60)
    print("  安全工具调用")
    print("=" * 60)
    context = SecurityContext(user_id="user_123")
    context.authorize_tool("get_user_profile")
    print("\n  调用授权工具 get_user_profile:")
    tool = SecureTool("get_user_profile", get_user_profile, context)
    result = tool.execute({"user_id": "alice"})
    print(f"    结果: {result}")
    print("\n  调用未授权工具 query_database:")
    tool2 = SecureTool("query_database", query_database, context)
    result2 = tool2.execute({"query": "SELECT * FROM users"})
    print(f"    结果: {result2}")


def demo_input_validation():
    print("\n" + "=" * 60)
    print("  输入验证")
    print("=" * 60)
    tests = [
        ("Hello World", True),
        ("abc123@email.com", True),
        ("<script>alert('XSS')</script>", False),
        ("SELECT * FROM users; DROP TABLE users", False),
    ]
    print("\n  文本安全验证:")
    for text, expected in tests:
        result = InputValidator.validate_text(text)
        status = "✅" if result == expected else "❌"
        print(f"    {status} '{text[:30]}...' -> {result}")
    print("\n  HTML 清理:")
    dirty = "Normal text <script>alert('XSS')</script> More text"
    clean = InputValidator.sanitize_html(dirty)
    print(f"    原始: {dirty}")
    print(f"    清理: {clean}")


def demo_data_protection():
    print("\n" + "=" * 60)
    print("  数据保护")
    print("=" * 60)
    print("\n  数据脱敏:")
    data = "Contact: admin@example.com, Phone: 138-0000-1234, Key: sk-1234567890abcdef"
    masked = DataProtector.mask_sensitive_data(data)
    print(f"    原始: {data}")
    print(f"    脱敏: {masked}")
    print("\n  数据哈希:")
    hash1 = DataProtector.compute_hash("Important config data")
    hash2 = DataProtector.compute_hash("Modified config data")
    print(f"    原文哈希: {hash1[:32]}...")
    print(f"    修改哈希: {hash2[:32]}...")
    print(f"    哈希不同: {hash1 != hash2}")


def demo_authenticator():
    print("\n" + "=" * 60)
    print("  身份验证器")
    print("=" * 60)
    auth = MCPAuthenticator()
    auth.register_api_key("my-secret-key-123", "user_alice")
    user_id = auth.authenticate_api_key("my-secret-key-123")
    print(f"  API Key 认证: {'成功' if user_id else '失败'} (user={user_id})")
    token = auth.issue_token("user_alice", ["admin"], expires_in=3600)
    print(f"  令牌颁发: {token[:20]}...")
    validated = auth.validate_token(token)
    print(f"  令牌验证: {'有效' if validated else '无效'}")


def demo_authorizer():
    print("\n" + "=" * 60)
    print("  授权控制器")
    print("=" * 60)
    authorizer = MCPAuthorizer()
    authorizer.assign_role("user_alice", "admin")
    authorizer.assign_role("user_bob", "viewer")
    authorizer.set_tool_permission("admin_tool", "admin")
    authorizer.set_tool_permission("read_tool", "read")
    print(f"  Alice (admin) 访问 admin_tool: {authorizer.check_access('user_alice', 'admin_tool')}")
    print(f"  Bob (viewer) 访问 admin_tool: {authorizer.check_access('user_bob', 'admin_tool')}")
    print(f"  Bob (viewer) 访问 read_tool: {authorizer.check_access('user_bob', 'read_tool')}")


def demo_rate_limiter():
    print("\n" + "=" * 60)
    print("  速率限制器")
    print("=" * 60)
    limiter = RateLimiter(max_requests=5, window_seconds=10)
    for i in range(7):
        allowed = limiter.is_allowed("user_alice")
        remaining = limiter.get_remaining("user_alice")
        print(f"  请求 {i+1}: {'允许' if allowed else '拒绝'} (剩余: {remaining})")


def demo_audit():
    print("\n" + "=" * 60)
    print("  审计日志")
    print("=" * 60)
    audit = AuditLogger("mcp_audit_demo.log")
    audit.log("LOGIN", "user_alice", {"ip": "192.168.1.1"}, success=True)
    audit.log("TOOL_CALL", "user_alice", {"tool": "get_weather"}, success=True)
    audit.log("AUTH_FAILURE", "unknown", {"method": "tools/call"}, success=False)
    events = audit.get_recent_events()
    print(f"  记录事件: {len(events)} 条")
    for event in events:
        print(f"    {event['timestamp']} | {event['event']} | {event['user_id']}")


if __name__ == "__main__":
    demo_security_context()
    demo_tool_security()
    demo_input_validation()
    demo_data_protection()
    demo_authenticator()
    demo_authorizer()
    demo_rate_limiter()
    demo_audit()
