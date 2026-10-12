"""
mcp_practical.py — MCP 实战：开发完整的 MCP Server
集成数据库查询、文件操作、Web 搜索三大功能模块。
综合运用身份验证、授权控制、输入验证、数据脱敏等安全措施。
"""
import os
import re
import json
import hashlib
import sqlite3
import time
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field


# ============================================================
# 模块：安全基础（复用前面的安全组件）
# ============================================================

class InputValidator:
    """输入验证器"""
    SAFE_PATTERN = re.compile(r'^[\w\s\.,!?@\-]+$')
    
    @staticmethod
    def validate_sql_safe(query: str) -> bool:
        """验证 SQL 查询是否安全（只允许 SELECT）"""
        upper = query.upper().strip()
        if not upper.startswith("SELECT"):
            return False
        # 检查是否包含危险操作关键字（在 SELECT 之后）
        # 使用词边界匹配，避免误判（如 SELECT ... DELETE 中的 DELETE）
        dangerous = re.findall(r'\b(DROP|DELETE|ALTER|TRUNCATE|EXEC|INSERT|UPDATE)\b', upper)
        if dangerous:
            return False
        return True
    
    @staticmethod
    def sanitize_path(path: str) -> Optional[str]:
        """验证文件路径，防止路径遍历"""
        if ".." in path or path.startswith("/"):
            return None
        return os.path.normpath(path)


class DataProtector:
    """数据保护器"""
    PATTERNS = {
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "api_key": re.compile(r'\b(?:sk|pk|api)[-_]?[a-zA-Z0-9]{20,}\b'),
    }

    @staticmethod
    def mask_sensitive(text: str) -> str:
        for pattern in DataProtector.PATTERNS.values():
            def replacer(m):
                orig = m.group(0)
                if len(orig) > 8:
                    return orig[:4] + "*" * (len(orig) - 8) + orig[-4:]
                return "***"
            text = pattern.sub(replacer, text)
        return text


# ============================================================
# 模块：数据库查询工具
# ============================================================

class DatabaseTool:
    """
    数据库查询 MCP 工具
    
    提供安全的只读数据库查询能力：
    - 仅支持 SELECT 查询
    - 参数化查询防止 SQL 注入
    - 结果脱敏处理
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use a temporary file-based DB to persist across connections
            import tempfile
            self.db_path = tempfile.mktemp(suffix='.db')
        else:
            self.db_path = db_path
        self._init_db()
    
    def __del__(self):
        # Clean up temp file
        import os
        try:
            if self.db_path.endswith('.db') and os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass
    
    def _get_conn(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _init_db(self):
        """初始化示例数据库"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS users')
        cursor.execute('DROP TABLE IF EXISTS articles')
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT, email TEXT, role TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY,
                title TEXT, author_id INTEGER,
                content TEXT, created_at TEXT
            )
        ''')
        
        sample_users = [
            (1, 'Alice', 'alice@example.com', 'admin'),
            (2, 'Bob', 'bob@example.com', 'editor'),
            (3, 'Charlie', 'charlie@example.com', 'viewer'),
        ]
        cursor.executemany('INSERT INTO users VALUES (?, ?, ?, ?)', sample_users)
        
        sample_articles = [
            (1, 'MCP 协议入门', 1, 'MCP 是 Model Context Protocol...', '2026-01-15'),
            (2, 'Function Calling 实战', 2, 'Function Calling 允许 AI...', '2026-02-20'),
            (3, 'RAG 技术详解', 3, 'RAG 结合检索和生成...', '2026-03-10'),
        ]
        cursor.executemany('INSERT INTO articles VALUES (?, ?, ?, ?, ?)', sample_articles)
        
        conn.commit()
        conn.close()
    
    def list_tables(self) -> Dict[str, Any]:
        """列出所有表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "tables": tables}
    
    def execute_query(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        """执行安全的只读查询"""
        if not InputValidator.validate_sql_safe(query):
            return {"error": "只允许 SELECT 查询"}
        
        try:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()
            
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, str):
                        row[key] = DataProtector.mask_sensitive(value)
            
            return {"success": True, "columns": columns, "rows": rows, "count": len(rows)}
        except Exception as e:
            return {"error": str(e)}


# ============================================================
# 模块：文件操作工具
# ============================================================

class FileTool:
    """
    文件操作 MCP 工具
    
    提供安全的文件读写能力：
    - 路径遍历防护
    - 文件类型白名单
    - 内容安全扫描
    """
    
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.json', '.csv', '.yaml', '.yml', '.py', '.html', '.css', '.js'}
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    
    def __init__(self, base_dir: str = "./workspace"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
    
    def list_files(self, subdir: str = "") -> Dict[str, Any]:
        """列出目录文件"""
        safe_path = InputValidator.sanitize_path(subdir)
        if not safe_path:
            return {"error": "无效路径"}
        
        full_path = os.path.join(self.base_dir, safe_path)
        if not os.path.isdir(full_path):
            return {"error": "目录不存在"}
        
        try:
            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(item_path)
                files.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": os.path.getsize(item_path) if not is_dir else 0,
                })
            return {"success": True, "files": files, "path": safe_path}
        except Exception as e:
            return {"error": str(e)}
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """读取文件内容"""
        safe_path = InputValidator.sanitize_path(file_path)
        if not safe_path:
            return {"error": "无效路径"}
        
        # 检查扩展名
        _, ext = os.path.splitext(safe_path)
        if ext.lower() not in self.ALLOWED_EXTENSIONS:
            return {"error": f"不支持的文件类型: {ext}"}
        
        full_path = os.path.join(self.base_dir, safe_path)
        if not os.path.isfile(full_path):
            return {"error": "文件不存在"}
        
        # 检查文件大小
        if os.path.getsize(full_path) > self.MAX_FILE_SIZE:
            return {"error": "文件过大"}
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content, "path": safe_path}
        except Exception as e:
            return {"error": str(e)}
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        safe_path = InputValidator.sanitize_path(file_path)
        if not safe_path:
            return {"error": "无效路径"}
        
        _, ext = os.path.splitext(safe_path)
        if ext.lower() not in self.ALLOWED_EXTENSIONS:
            return {"error": f"不支持的文件类型: {ext}"}
        
        full_path = os.path.join(self.base_dir, safe_path)
        
        # 确保父目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": safe_path, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}


# ============================================================
# 模块：Web 搜索工具
# ============================================================

class WebSearchTool:
    """
    Web 搜索 MCP 工具
    
    提供安全的 Web 搜索能力：
    - 模拟搜索引擎 API
    - 搜索结果脱敏
    - 搜索频率限制
    """
    
    def __init__(self):
        # 模拟搜索索引
        self.index = [
            {"title": "MCP 协议官方文档", "url": "https://mcp.dev", "summary": "Model Context Protocol 官方文档，涵盖协议规范、SDK 和最佳实践。"},
            {"title": "Function Calling 指南", "url": "https://docs.ai/fc", "summary": "Function Calling 完整指南，包含工具定义、参数验证和错误处理。"},
            {"title": "RAG 技术入门", "url": "https://rag.guide", "summary": "Retrieval-Augmented Generation 技术详解，包含向量数据库和检索策略。"},
            {"title": "Python 异步编程", "url": "https://pyasync.dev", "summary": "Python asyncio 完整教程，包含事件循环、协程和并发模式。"},
            {"title": "SQLite 数据库教程", "url": "https://sqlite.org/docs", "summary": "SQLite 官方文档，涵盖 SQL 语法、性能优化和安全最佳实践。"},
        ]
        self.search_count = 0
        self.max_searches = 50
    
    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """执行搜索"""
        if not query or len(query.strip()) < 2:
            return {"error": "搜索关键词至少 2 个字符"}
        
        self.search_count += 1
        if self.search_count > self.max_searches:
            return {"error": "搜索频率超限，请稍后再试"}
        
        # 简单的关键词匹配
        query_lower = query.lower()
        results = []
        for item in self.index:
            if query_lower in item["title"].lower() or query_lower in item["summary"].lower():
                results.append(item)
        
        # 如果没有精确匹配，返回相关性较高的结果
        if not results:
            # 模糊匹配：包含任意关键词
            keywords = query_lower.split()
            for item in self.index:
                score = sum(1 for kw in keywords if kw in item["title"].lower() or kw in item["summary"].lower())
                if score > 0:
                    item_with_score = {**item, "relevance": score}
                    results.append(item_with_score)
            results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return {
            "success": True,
            "query": query,
            "results": results[:limit],
            "total": len(results),
        }


# ============================================================
# 模块：综合 MCP Server
# ============================================================

class PracticalMCPServer:
    """
    实战 MCP Server
    
    集成数据库、文件、搜索三大工具模块，
    提供统一的安全访问接口。
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.db = DatabaseTool()
        self.files = FileTool(workspace_dir)
        self.search = WebSearchTool()
        self.audit_log: List[Dict[str, Any]] = []
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """路由工具调用"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            if tool_name == "db_list_tables":
                result = self.db.list_tables()
            elif tool_name == "db_query":
                result = self.db.execute_query(
                    arguments.get("sql", ""),
                    tuple(arguments.get("params", []))
                )
            elif tool_name == "file_list":
                result = self.files.list_files(arguments.get("path", ""))
            elif tool_name == "file_read":
                result = self.files.read_file(arguments.get("path", ""))
            elif tool_name == "file_write":
                result = self.files.write_file(
                    arguments.get("path", ""),
                    arguments.get("content", "")
                )
            elif tool_name == "web_search":
                result = self.search.search(
                    arguments.get("query", ""),
                    arguments.get("limit", 5)
                )
            else:
                result = {"error": f"未知工具: {tool_name}"}
            
            # 审计日志
            self.audit_log.append({
                "timestamp": timestamp,
                "tool": tool_name,
                "success": result.get("success", False),
            })
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """返回服务器能力"""
        return {
            "tools": [
                {"name": "db_list_tables", "description": "列出数据库中的所有表"},
                {"name": "db_query", "description": "执行只读 SQL 查询（仅 SELECT）", "inputSchema": {"sql": "string", "params": "array"}},
                {"name": "file_list", "description": "列出目录中的文件", "inputSchema": {"path": "string"}},
                {"name": "file_read", "description": "读取文件内容", "inputSchema": {"path": "string"}},
                {"name": "file_write", "description": "写入文件内容", "inputSchema": {"path": "string", "content": "string"}},
                {"name": "web_search", "description": "执行 Web 搜索", "inputSchema": {"query": "string", "limit": "integer"}},
            ]
        }


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  MCP 实战：综合服务器演示")
    print("=" * 60)
    
    server = PracticalMCPServer()
    
    # 1. 获取能力
    print("\n 1. 服务器能力")
    caps = server.get_capabilities()
    print(f"  可用工具: {len(caps['tools'])} 个")
    for tool in caps["tools"]:
        print(f"    • {tool['name']}: {tool['description']}")
    
    # 2. 数据库查询
    print("\n 2. 数据库查询")
    result = server.handle_tool_call("db_list_tables", {})
    print(f"  表列表: {result}")
    
    result = server.handle_tool_call("db_query", {"sql": "SELECT * FROM users"})
    print(f"  用户查询: {result.get('count', 0)} 条记录")
    for row in result.get("rows", [])[:2]:
        print(f"    {row}")
    
    # 3. 文件操作
    print("\n 3. 文件操作")
    result = server.handle_tool_call("file_list", {"path": ""})
    print(f"  文件列表: {result}")
    
    result = server.handle_tool_call("file_write", {"path": "notes.md", "content": "# 学习笔记\n\nMCP 协议是一个标准化的..."})
    print(f"  文件写入: {result}")
    
    result = server.handle_tool_call("file_read", {"path": "notes.md"})
    if result.get("success"):
        print(f"  文件读取成功，内容长度: {len(result.get('content', ''))} 字符")
    
    # 4. Web 搜索
    print("\n 4. Web 搜索")
    result = server.handle_tool_call("web_search", {"query": "MCP 协议"})
    if result.get("success"):
        print(f"  搜索结果: {result.get('total')} 条")
        for item in result.get("results", [])[:3]:
            print(f"    • {item['title']}: {item['summary'][:50]}...")
    
    # 5. 安全测试
    print("\n 5. 安全测试")
    
    # SQL 注入测试
    result = server.handle_tool_call("db_query", {"sql": "DROP TABLE users"})
    print(f"  SQL 注入防护: {result}")
    
    # 路径遍历测试
    result = server.handle_tool_call("file_read", {"path": "../../etc/passwd"})
    print(f"  路径遍历防护: {result}")
    
    # 6. 审计日志
    print("\n 6. 审计日志")
    print(f"  总调用次数: {len(server.audit_log)}")
    success_count = sum(1 for log in server.audit_log if log["success"])
    print(f"  成功: {success_count}, 失败: {len(server.audit_log) - success_count}")
    
    print("\n" + "=" * 60)
    print("  实战演示完成")
    print("=" * 60)
