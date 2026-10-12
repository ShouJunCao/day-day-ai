"""
example_usage.py — MCP 实战：综合服务器演示
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_practical import (
    PracticalMCPServer,
    DatabaseTool,
    FileTool,
    WebSearchTool,
    InputValidator,
    DataProtector,
)


def demo_database():
    """演示数据库工具"""
    print("=" * 60)
    print("  数据库工具")
    print("=" * 60)
    db = DatabaseTool()

    print("\n  表列表:")
    result = db.list_tables()
    print(f"    {result}")

    print("\n  查询所有用户:")
    result = db.execute_query("SELECT * FROM users")
    print(f"    记录数: {result.get('count')}")
    for row in result.get("rows", [])[:3]:
        print(f"    {row}")

    print("\n  查询文章:")
    result = db.execute_query("SELECT title, author_id FROM articles WHERE id <= 2")
    print(f"    记录数: {result.get('count')}")
    for row in result.get("rows", []):
        print(f"    {row}")

    print("\n  SQL 注入防护测试:")
    result = db.execute_query("DROP TABLE users")
    print(f"    结果: {result}")
    result = db.execute_query("SELECT * FROM users; DELETE FROM users")
    print(f"    结果: {result}")


def demo_files():
    """演示文件工具"""
    print("\n" + "=" * 60)
    print("  文件工具")
    print("=" * 60)
    files = FileTool("./demo_workspace")

    print("\n  写入文件:")
    result = files.write_file("readme.md", "# 项目说明\n\n这是一个 MCP 实战项目。")
    print(f"    {result}")

    print("\n  读取文件:")
    result = files.read_file("readme.md")
    if result.get("success"):
        print(f"    内容: {result.get('content', '')[:50]}...")

    print("\n  路径遍历防护:")
    result = files.read_file("../../etc/passwd")
    print(f"    结果: {result}")

    print("\n  文件类型限制:")
    result = files.write_file("test.exe", "binary data")
    print(f"    结果: {result}")


def demo_search():
    """演示搜索工具"""
    print("\n" + "=" * 60)
    print("  Web 搜索工具")
    print("=" * 60)
    search = WebSearchTool()

    print("\n  搜索 'MCP 协议':")
    result = search.search("MCP 协议", limit=3)
    if result.get("success"):
        print(f"    找到 {result.get('total')} 条结果")
        for item in result.get("results", []):
            print(f"    • {item['title']}")

    print("\n  搜索 'Python':")
    result = search.search("Python", limit=3)
    if result.get("success"):
        print(f"    找到 {result.get('total')} 条结果")
        for item in result.get("results", []):
            print(f"    • {item['title']}")


def demo_comprehensive():
    """演示综合服务器"""
    print("\n" + "=" * 60)
    print("  综合 MCP 服务器")
    print("=" * 60)
    server = PracticalMCPServer("./demo_workspace")

    print(f"\n  可用工具: {len(server.get_capabilities()['tools'])} 个")

    # 数据库操作
    print("\n  数据库查询:")
    result = server.handle_tool_call("db_query", {"sql": "SELECT name, email FROM users"})
    print(f"    结果: {result.get('count')} 条")
    for row in result.get("rows", []):
        print(f"    {row}")

    # 文件操作
    print("\n  文件写入:")
    result = server.handle_tool_call("file_write", {"path": "notes.md", "content": "# 笔记\n\nMCP 学习笔记"})
    print(f"    {result}")

    # Web 搜索
    print("\n  Web 搜索:")
    result = server.handle_tool_call("web_search", {"query": "MCP", "limit": 2})
    if result.get("success"):
        for item in result.get("results", []):
            print(f"    • {item['title']}: {item['summary'][:30]}...")

    # 审计日志
    print("\n  审计日志:")
    print(f"    总调用: {len(server.audit_log)} 次")
    success = sum(1 for log in server.audit_log if log["success"])
    print(f"    成功: {success}, 失败: {len(server.audit_log) - success}")


if __name__ == "__main__":
    demo_database()
    demo_files()
    demo_search()
    demo_comprehensive()
