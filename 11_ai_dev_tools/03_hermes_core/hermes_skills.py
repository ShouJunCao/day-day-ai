"""
hermes_skills.py — Hermes Agent 核心功能演示
演示 Skills、Memory、Cron、多平台集成等核心功能。
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
# 模块：Skill 系统
# ============================================================

@dataclass
class Skill:
    """Skill 定义"""
    name: str
    category: str
    description: str
    trigger: str  # 触发场景
    steps: List[str] = field(default_factory=list)


SKILLS_DB = [
    Skill(
        name="learning-content-generation",
        category="content-creation",
        description="生成技术学习资料 HTML",
        trigger="用户要求生成学习资料",
        steps=["分析主题", "编写内容", "生成 SVG 图表", "生成代码", "自检"]
    ),
    Skill(
        name="debugging",
        category="software-development",
        description="代码调试方法论",
        trigger="用户遇到代码错误",
        steps=["复现问题", "定位根因", "修复验证"]
    ),
    Skill(
        name="github-workflow",
        category="github",
        description="GitHub 工作流管理",
        trigger="用户要求管理 PR/Issue",
        steps=["认证", "分支管理", "PR 操作", "CI/CD"]
    ),
    Skill(
        name="ai-music-generation",
        category="media",
        description="AI 音乐生成",
        trigger="用户要求生成音乐",
        steps=["选择模型", "配置参数", "生成音频"]
    ),
    Skill(
        name="hermes-agent",
        category="autonomous-ai-agents",
        description="Hermes Agent 配置和扩展",
        trigger="用户询问 Hermes 配置",
        steps=["加载 skill", "读取文档", "执行命令"]
    ),
]


class SkillManager:
    """Skill 管理器"""
    
    def __init__(self):
        self.skills = SKILLS_DB.copy()
        self.loaded: List[str] = []
    
    def search(self, query: str) -> List[Skill]:
        """根据查询搜索 Skill"""
        results = []
        query_lower = query.lower()
        for skill in self.skills:
            if (query_lower in skill.name.lower() or
                query_lower in skill.description.lower() or
                query_lower in skill.trigger.lower() or
                query_lower in skill.category.lower()):
                results.append(skill)
        return results
    
    def load(self, name: str) -> Optional[Skill]:
        """加载 Skill"""
        skill = next((s for s in self.skills if s.name == name), None)
        if skill and name not in self.loaded:
            self.loaded.append(name)
        return skill
    
    def list_by_category(self, category: str) -> List[Skill]:
        """按分类列出 Skill"""
        return [s for s in self.skills if s.category == category]
    
    def get_categories(self) -> List[str]:
        return list(set(s.category for s in self.skills))


# ============================================================
# 模块：Memory 系统
# ============================================================

class MemoryStore:
    """Memory 存储"""
    
    def __init__(self, max_entries: int = 50):
        self.entries: List[Dict[str, Any]] = []
        self.max_entries = max_entries
    
    def add(self, content: str, target: str = "memory") -> Dict[str, Any]:
        """添加记忆"""
        entry = {
            "id": str(uuid.uuid4())[:8],
            "content": content,
            "target": target,
            "created_at": datetime.now().isoformat()
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        return entry
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索记忆"""
        query_lower = query.lower()
        return [
            e for e in self.entries
            if query_lower in e["content"].lower()
        ]
    
    def get_all(self, target: str = None) -> List[Dict[str, Any]]:
        """获取所有记忆"""
        if target:
            return [e for e in self.entries if e["target"] == target]
        return self.entries.copy()
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_entries": len(self.entries),
            "max_entries": self.max_entries,
            "targets": list(set(e["target"] for e in self.entries))
        }


# ============================================================
# 模块：Cron 系统
# ============================================================

@dataclass
class CronJob:
    """定时任务"""
    name: str
    schedule: str
    prompt: str
    enabled: bool = True
    last_run: Optional[str] = None


class CronManager:
    """Cron 管理器"""
    
    def __init__(self):
        self.jobs: List[CronJob] = []
    
    def create(self, name: str, schedule: str, prompt: str) -> CronJob:
        """创建定时任务"""
        job = CronJob(name=name, schedule=schedule, prompt=prompt)
        self.jobs.append(job)
        return job
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return [
            {
                "name": j.name,
                "schedule": j.schedule,
                "enabled": j.enabled,
                "last_run": j.last_run
            }
            for j in self.jobs
        ]
    
    def enable(self, name: str) -> bool:
        """启用任务"""
        for job in self.jobs:
            if job.name == name:
                job.enabled = True
                return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用任务"""
        for job in self.jobs:
            if job.name == name:
                job.enabled = False
                return True
        return False


# ============================================================
# 模块：多平台集成
# ============================================================

@dataclass
class Platform:
    """平台集成定义"""
    name: str
    type: str
    features: List[str] = field(default_factory=list)
    status: str = "connected"


PLATFORMS = [
    Platform(
        name="Telegram",
        type="messaging",
        features=["文本消息", "图片", "语音", "文件", "群组", "Inline Bot"],
        status="connected"
    ),
    Platform(
        name="WhatsApp",
        type="messaging",
        features=["文本消息", "图片", "语音", "文件"],
        status="connected"
    ),
    Platform(
        name="Discord",
        type="messaging",
        features=["文本消息", "图片", "语音", "频道", "Thread"],
        status="connected"
    ),
    Platform(
        name="Signal",
        type="messaging",
        features=["文本消息", "图片", "语音"],
        status="connected"
    ),
    Platform(
        name="Web Chat",
        type="web",
        features=["文本消息", "文件上传", "代码高亮", "Markdown"],
        status="connected"
    ),
]


class PlatformManager:
    """平台管理器"""
    
    def list_platforms(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": p.name,
                "type": p.type,
                "features": p.features,
                "status": p.status
            }
            for p in PLATFORMS
        ]
    
    def get_platform(self, name: str) -> Optional[Dict[str, Any]]:
        platform = next((p for p in PLATFORMS if p.name == name), None)
        if platform:
            return {
                "name": platform.name,
                "type": platform.type,
                "features": platform.features,
                "status": platform.status
            }
        return None


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Hermes Agent 核心功能演示")
    print("=" * 60)

    # 1. Skill 系统
    print("\n 1. Skill 系统")
    sm = SkillManager()
    
    print(f"  分类: {sm.get_categories()}")
    
    results = sm.search("生成")
    print(f"  搜索'生成': {[s.name for s in results]}")
    
    skill = sm.load("learning-content-generation")
    print(f"  已加载: {sm.loaded}")
    if skill:
        print(f"  步骤: {skill.steps}")

    # 2. Memory 系统
    print("\n 2. Memory 系统")
    ms = MemoryStore()
    
    ms.add("用户偏好：Python 为主，不要过度强调 Java", target="user")
    ms.add("项目使用 pytest 框架", target="memory")
    ms.add("DashScope API Key 已配置", target="memory")
    
    print(f"  统计: {ms.stats()}")
    print(f"  搜索'Python': {[e['content'][:30] for e in ms.search('Python')]}")

    # 3. Cron 系统
    print("\n 3. Cron 系统")
    cm = CronManager()
    
    cm.create("AI 日报", "0 9 * * *", "生成 AI 行业日报")
    cm.create("代码审查", "every 2h", "检查 PR 并生成审查报告")
    cm.create("热点监控", "30m", "监控热点话题")
    
    print(f"  任务列表: {cm.list_jobs()}")

    # 4. 多平台集成
    print("\n⭐ 4. 多平台集成")
    pm = PlatformManager()
    
    print("  已连接平台:")
    for p in pm.list_platforms():
        print(f"    • {p['name']} ({p['type']}) - {p['status']}")
        print(f"      功能: {', '.join(p['features'])}")

    print("\n" + "=" * 60)
    print("  演示完成")
    print("=" * 60)
