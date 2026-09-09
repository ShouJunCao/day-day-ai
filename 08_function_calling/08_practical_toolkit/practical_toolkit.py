"""
practical_toolkit.py — 实战：天气/数据库/API/文件操作工具集
综合运用前面学习的所有 Function Calling 技术。
"""
import os
import json
import time
import sqlite3
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# 模块：数据结构
# ============================================================

@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    success: bool = False
    error: str = ""
    execution_time: float = 0.0


@dataclass
class ToolkitResult:
    """工具集执行结果"""
    results: List[ToolResult]
    total_time: float = 0.0
    summary: str = ""


# ============================================================
# 模块：天气工具
# ============================================================

class WeatherTool:
    """天气查询工具"""

    def __init__(self, api_key: str = "demo_key"):
        self.api_key = api_key
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 分钟缓存

    def get_weather(self, city: str) -> str:
        """获取指定城市天气"""
        # 检查缓存
        now = time.time()
        if city in self._cache:
            cached_time, cached_data = self._cache[city]
            if now - cached_time < self._cache_ttl:
                return cached_data

        # 模拟 API 调用
        weather_data = {
            "北京": {"weather": "晴", "temp": 25, "humidity": 45, "wind": "北风 2 级"},
            "上海": {"weather": "多云", "temp": 28, "humidity": 65, "wind": "东南风 3 级"},
            "广州": {"weather": "雷阵雨", "temp": 32, "humidity": 85, "wind": "南风 1 级"},
        }

        data = weather_data.get(city, {"weather": "未知", "temp": 0, "humidity": 0, "wind": "未知"})
        result = json.dumps({"city": city, **data}, ensure_ascii=False)

        # 缓存结果
        self._cache[city] = (now, result)
        return result

    def get_forecast(self, city: str, days: int = 3) -> str:
        """获取天气预报"""
        forecast = ["晴", "多云", "小雨", "晴", "阴"]
        return json.dumps({
            "city": city,
            "days": days,
            "forecast": forecast[:days],
        }, ensure_ascii=False)


# ============================================================
# 模块：数据库工具
# ============================================================

class DatabaseTool:
    """数据库操作工具（SQLite）"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product TEXT NOT NULL,
                amount REAL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        self.conn.commit()

        # 插入示例数据
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                [
                    ("张三", "zhangsan@example.com"),
                    ("李四", "lisi@example.com"),
                    ("王五", "wangwu@example.com"),
                ]
            )
            cursor.executemany(
                "INSERT INTO orders (user_id, product, amount, status) VALUES (?, ?, ?, ?)",
                [
                    (1, "Python 编程", 59.9, "completed"),
                    (1, "AI 入门", 39.9, "pending"),
                    (2, "数据分析", 49.9, "completed"),
                    (3, "机器学习", 69.9, "shipped"),
                ]
            )
            self.conn.commit()

    def query(self, sql: str) -> str:
        """执行查询"""
        # 安全限制：只允许 SELECT
        if not sql.strip().upper().startswith("SELECT"):
            return json.dumps({"error": "只允许 SELECT 查询"})

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = {
                "columns": columns,
                "rows": [dict(zip(columns, row)) for row in rows],
                "count": len(rows),
            }
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def insert_user(self, name: str, email: str) -> str:
        """插入用户"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (name, email)
            )
            self.conn.commit()
            return json.dumps({"success": True, "user_id": cursor.lastrowid})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_user_orders(self, user_id: int) -> str:
        """获取用户订单"""
        return self.query(
            f"SELECT o.id, o.product, o.amount, o.status "
            f"FROM orders o WHERE o.user_id = {user_id}"
        )

    def close(self):
        """关闭连接"""
        self.conn.close()


# ============================================================
# 模块：API 工具
# ============================================================

class APITool:
    """HTTP API 调用工具（模拟）"""

    def __init__(self, base_url: str = "https://api.example.com"):
        self.base_url = base_url

    def search(self, query: str, limit: int = 5) -> str:
        """模拟搜索 API"""
        results = [
            {"title": f"关于 '{query}' 的文章 {i}", "url": f"https://example.com/{i}", "score": round(0.9 - i * 0.1, 2)}
            for i in range(limit)
        ]
        return json.dumps({"query": query, "results": results}, ensure_ascii=False)

    def get_news(self, category: str = "tech", count: int = 3) -> str:
        """模拟新闻 API"""
        news = {
            "tech": [
                {"title": "GPT-5 发布，性能提升 10 倍", "source": "TechCrunch"},
                {"title": "Apple 发布新一代 M 系列芯片", "source": "The Verge"},
                {"title": "Google 推出 Gemini 2.0", "source": "VentureBeat"},
            ],
            "finance": [
                {"title": "AI 概念股持续上涨", "source": "Bloomberg"},
                {"title": "NVIDIA 市值突破 3 万亿美元", "source": "Reuters"},
                {"title": "科技股财报超预期", "source": "CNBC"},
            ],
        }
        category_news = news.get(category, news["tech"])
        return json.dumps({"category": category, "news": category_news[:count]}, ensure_ascii=False)


# ============================================================
# 模块：文件操作工具
# ============================================================

class FileTool:
    """文件操作工具"""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.join(os.path.expanduser("~"), "Desktop", "toolkit_demo")
        self.base_dir = os.path.realpath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def read_file(self, filepath: str) -> str:
        """读取文件内容"""
        # 安全检查：防止路径遍历
        real_path = os.path.realpath(os.path.join(self.base_dir, filepath.lstrip("/")))
        if not real_path.startswith(self.base_dir):
            return json.dumps({"error": "路径遍历攻击被阻止"})

        try:
            if os.path.exists(real_path):
                with open(real_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return json.dumps({
                    "filepath": real_path,
                    "size": len(content),
                    "content": content[:1000],  # 限制长度
                }, ensure_ascii=False)
            return json.dumps({"error": f"文件不存在: {filepath}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def write_file(self, filepath: str, content: str) -> str:
        """写入文件"""
        real_path = os.path.realpath(os.path.join(self.base_dir, filepath.lstrip("/")))
        if not real_path.startswith(self.base_dir):
            return json.dumps({"error": "路径遍历攻击被阻止"})

        try:
            os.makedirs(os.path.dirname(real_path), exist_ok=True)
            with open(real_path, "w", encoding="utf-8") as f:
                f.write(content)
            return json.dumps({"success": True, "filepath": real_path, "size": len(content)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def list_dir(self, dirpath: str = "") -> str:
        """列出目录"""
        real_path = os.path.realpath(os.path.join(self.base_dir, dirpath.lstrip("/")))
        if not real_path.startswith(self.base_dir):
            return json.dumps({"error": "路径遍历攻击被阻止"})

        try:
            items = os.listdir(real_path)
            return json.dumps({"directory": real_path, "items": sorted(items)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})


# ============================================================
# 模块：并行工具集执行器
# ============================================================

class PracticalToolkit:
    """
    实战工具集：整合天气、数据库、API、文件操作。
    支持并行执行多个工具调用。
    """

    def __init__(self, db_path: str = ":memory:"):
        self.weather = WeatherTool()
        self.database = DatabaseTool(db_path)
        self.api = APITool()
        self.files = FileTool()

    def execute(self, tool_calls: List[Dict[str, Any]],
                parallel: bool = True) -> ToolkitResult:
        """执行工具调用列表"""
        start_time = time.time()

        if parallel and len(tool_calls) > 1:
            results = self._execute_parallel(tool_calls)
        else:
            results = self._execute_sequential(tool_calls)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        summary = f"执行 {len(tool_calls)} 个工具调用，{success_count} 个成功，耗时 {total_time:.2f}s"

        return ToolkitResult(results=results, total_time=total_time, summary=summary)

    def _execute_parallel(self, tool_calls: List[Dict]) -> List[ToolResult]:
        """并行执行"""
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._dispatch, call): call
                for call in tool_calls
            }
            for future in as_completed(futures):
                results.append(future.result())
        return results

    def _execute_sequential(self, tool_calls: List[Dict]) -> List[ToolResult]:
        """顺序执行"""
        return [self._dispatch(call) for call in tool_calls]

    def _dispatch(self, call: Dict) -> ToolResult:
        """分发到具体工具"""
        start = time.time()
        tool_name = call.get("tool_name", "")
        arguments = call.get("arguments", {})

        try:
            if tool_name == "get_weather":
                result = self.weather.get_weather(arguments.get("city", "北京"))
            elif tool_name == "get_forecast":
                result = self.weather.get_forecast(
                    arguments.get("city", "北京"),
                    arguments.get("days", 3),
                )
            elif tool_name == "db_query":
                result = self.database.query(arguments.get("sql", "SELECT 1"))
            elif tool_name == "db_user_orders":
                result = self.database.get_user_orders(arguments.get("user_id", 1))
            elif tool_name == "search":
                result = self.api.search(
                    arguments.get("query", ""),
                    arguments.get("limit", 5),
                )
            elif tool_name == "get_news":
                result = self.api.get_news(
                    arguments.get("category", "tech"),
                    arguments.get("count", 3),
                )
            elif tool_name == "read_file":
                result = self.files.read_file(arguments.get("filepath", ""))
            elif tool_name == "write_file":
                result = self.files.write_file(
                    arguments.get("filepath", ""),
                    arguments.get("content", ""),
                )
            else:
                result = json.dumps({"error": f"未知工具: {tool_name}"})

            elapsed = time.time() - start
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = time.time() - start
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                error=str(e),
                success=False,
                execution_time=elapsed,
            )

    def close(self):
        """清理资源"""
        self.database.close()


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  实战工具集：综合运用 Function Calling 技术")
    print("=" * 60)

    toolkit = PracticalToolkit()

    # 场景 1：并行查询天气 + 新闻 + 搜索
    print("\n📋 场景 1：并行综合查询")
    calls_1 = [
        {"tool_name": "get_weather", "arguments": {"city": "北京"}},
        {"tool_name": "get_news", "arguments": {"category": "tech", "count": 3}},
        {"tool_name": "search", "arguments": {"query": "AI", "limit": 3}},
    ]
    result = toolkit.execute(calls_1, parallel=True)
    print(f"  摘要: {result.summary}")
    for r in result.results:
        status = "✅" if r.success else "❌"
        print(f"  {status} {r.tool_name} → {(r.result or '')[:60]}...")

    # 场景 2：数据库查询
    print("\n📋 场景 2：数据库操作")
    calls_2 = [
        {"tool_name": "db_query", "arguments": {"sql": "SELECT * FROM users"}},
        {"tool_name": "db_user_orders", "arguments": {"user_id": 1}},
    ]
    result = toolkit.execute(calls_2, parallel=True)
    print(f"  摘要: {result.summary}")
    for r in result.results:
        status = "✅" if r.success else "❌"
        print(f"  {status} {r.tool_name} → {(r.result or '')[:80]}...")

    # 场景 3：文件操作
    print("\n📋 场景 3：文件操作")
    calls_3 = [
        {"tool_name": "write_file", "arguments": {
            "filepath": "toolkit_output/report.txt",
            "content": "Function Calling 实战报告\n生成时间: 2024-01-15",
        }},
        {"tool_name": "read_file", "arguments": {"filepath": "toolkit_output/report.txt"}},
    ]
    result = toolkit.execute(calls_3, parallel=False)
    print(f"  摘要: {result.summary}")
    for r in result.results:
        status = "✅" if r.success else "❌"
        print(f"  {status} {r.tool_name} → {(r.result or '')[:60]}...")

    # 场景 4：对比并行 vs 顺序
    print("\n📋 场景 4：并行 vs 顺序性能对比")
    calls_4 = [
        {"tool_name": "get_weather", "arguments": {"city": "北京"}},
        {"tool_name": "get_forecast", "arguments": {"city": "北京", "days": 5}},
        {"tool_name": "search", "arguments": {"query": "AI", "limit": 5}},
        {"tool_name": "get_news", "arguments": {"category": "finance", "count": 3}},
    ]

    parallel_result = toolkit.execute(calls_4, parallel=True)
    sequential_result = toolkit.execute(calls_4, parallel=False)

    print(f"  并行耗时: {parallel_result.total_time:.3f}s")
    print(f"  顺序耗时: {sequential_result.total_time:.3f}s")
    if parallel_result.total_time > 0:
        speedup = sequential_result.total_time / parallel_result.total_time
        print(f"  加速比: {speedup:.1f}x")

    toolkit.close()
    print("\n✅ 所有场景执行完成！")
