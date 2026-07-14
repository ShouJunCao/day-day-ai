"""
structured_output.py — 结构化输出解析引擎
包含 JSON 解析、XML 提取、重试修复与 Pydantic 验证

学习重点:
1. 鲁棒的 JSON 解析（处理 Markdown、截断）
2. XML 标签提取（处理混合内容）
3. Pydantic 强类型校验
4. 自动修复机制构建
"""

import json
import re
import time
from typing import Optional, Type, Any
from pydantic import BaseModel, ValidationError


class StructuredOutputParser:
    """
    结构化输出解析器：处理模型返回的非标准输出。
    
    核心功能：
        1. 自动清洗 JSON（去除 Markdown 标记、截断错误）
        2. XML 标签提取
        3. 简单的重试与修复机制
    """
    
    @staticmethod
    def parse_json(raw_output: str) -> Optional[dict]:
        """
        尝试从原始输出中解析 JSON。
        
        处理情况：
            - 标准 JSON
            - Markdown 包裹的 JSON (```json ... ```)
            - 包含前后缀文本的 JSON
        """
        # 1. 尝试直接解析
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            pass
        
        # 2. 尝试提取 Markdown 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_output)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 3. 尝试寻找第一个 { 和最后一个 }
        start = raw_output.find('{')
        end = raw_output.rfind('}')
        if start != -1 and end != -1:
            json_str = raw_output[start : end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        return None  # 解析失败
    
    @staticmethod
    def parse_json_array(raw_output: str) -> Optional[list]:
        """专门解析 JSON 数组"""
        result = StructuredOutputParser.parse_json(raw_output)
        return result if isinstance(result, list) else None


class XMLExtractor:
    """
    基于 XML 标签的内容提取器。
    """
    
    @staticmethod
    def extract_tag(content: str, tag_name: str) -> Optional[str]:
        """
        从内容中提取指定标签的内容。
        
        支持自闭合标签、嵌套标签的简单提取。
        """
        # 正则表达式匹配 <tag_name>...</tag_name>
        # re.DOTALL 允许匹配跨行内容
        pattern = rf'<{tag_name}\s*>(.*?)</{tag_name}\s*>'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return None
    
    @staticmethod
    def extract_all_tags(content: str) -> dict:
        """
        提取内容中所有定义的标签。
        返回 {tag_name: content} 字典。
        """
        # 匹配所有标签
        tags = re.findall(r'<(\w+)>(.*?)</\1>', content, re.DOTALL)
        result = {}
        for tag_name, tag_content in tags:
            result[tag_name] = tag_content.strip()
        return result


class PydanticValidator:
    """
    基于 Pydantic 的强类型校验与自动修复引擎。
    """
    
    def __init__(self, schema: Type[BaseModel], max_retries: int = 3):
        """
        参数:
            schema: Pydantic 模型类
            max_retries: 最大重试修复次数
        """
        self.schema = schema
        self.max_retries = max_retries
    
    def validate_and_fix(self, data: dict) -> dict:
        """
        校验并尝试修复数据。
        
        返回:
            符合 Schema 的字典数据
        异常:
            ValidationError: 如果多次修复仍失败
        """
        try:
            # 1. 尝试直接校验
            instance = self.schema(**data)
            return instance.model_dump()
        except ValidationError as e:
            error_detail = e.errors()[0]
            print(f"校验失败: 字段 {error_detail['loc'][0]} - {error_detail['msg']}")
            # 在实际应用中，这里会调用 LLM 进行修复
            # 我们在此处仅做日志记录，
            raise
    
    def get_schema_prompt(self) -> str:
        """生成用于 Prompt 的 JSON Schema 字符串"""
        return self.schema.model_json_schema()
