"""
tool_definition_spec.py — Tool 定义规范（JSON Schema、参数描述）
"""
import os
import re
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


# ============================================================
# 模块：数据类型
# ============================================================

@dataclass
class ParamDef:
    """参数定义"""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolSchema:
    """工具 Schema 定义"""
    name: str
    description: str
    parameters: List[ParamDef] = field(default_factory=list)

    def to_openai_format(self) -> dict:
        """转换为 OpenAI Function Calling 格式"""
        properties: Dict[str, Dict[str, Any]] = {}
        required = []

        for p in self.parameters:
            prop = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }


# ============================================================
# 模块：Schema 验证器
# ============================================================

class SchemaValidator:
    """
    工具定义验证器：检查工具定义是否符合规范。
    """

    VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object"}
    MAX_DESCRIPTION_LENGTH = 200
    MAX_PARAMS = 20

    def validate(self, schema: ToolSchema) -> List[str]:
        """验证工具定义，返回错误列表"""
        errors = []

        # 1. 名称检查
        if not schema.name:
            errors.append("工具名称不能为空")
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema.name):
            errors.append(f"工具名称 '{schema.name}' 不符合命名规范")

        # 2. 描述检查
        if not schema.description:
            errors.append(f"工具 '{schema.name}' 缺少描述")
        elif len(schema.description) > self.MAX_DESCRIPTION_LENGTH:
            errors.append(f"工具描述过长（>{self.MAX_DESCRIPTION_LENGTH}字）")

        # 3. 参数数量检查
        if len(schema.parameters) > self.MAX_PARAMS:
            errors.append(f"参数数量过多（>{self.MAX_PARAMS}）")

        # 4. 参数检查
        seen_names = set()
        for p in schema.parameters:
            if p.name in seen_names:
                errors.append(f"参数 '{p.name}' 重复定义")
            seen_names.add(p.name)

            if p.type not in self.VALID_TYPES:
                errors.append(f"参数 '{p.name}' 类型 '{p.type}' 无效")

            if not p.description:
                errors.append(f"参数 '{p.name}' 缺少描述")

        return errors


# ============================================================
# 模块：Schema 构建器
# ============================================================

class ToolSchemaBuilder:
    """
    工具 Schema 构建器：通过链式调用构建工具定义。
    """

    def __init__(self, name: str, description: str):
        self.schema = ToolSchema(name=name, description=description)

    def add_param(self, name: str, type: str, description: str,
                  required: bool = False, enum: Optional[List[str]] = None,
                  default: Any = None) -> 'ToolSchemaBuilder':
        """添加参数"""
        self.schema.parameters.append(ParamDef(
            name=name,
            type=type,
            description=description,
            required=required,
            enum=enum,
            default=default,
        ))
        return self

    def build(self) -> ToolSchema:
        """构建并返回 Schema"""
        return self.schema


# ============================================================
# 模块：工具库（预定义工具集合）
# ============================================================

class ToolLibrary:
    """
    工具库：提供预定义的常用工具 Schema。
    """

    @staticmethod
    def weather() -> ToolSchema:
        """天气查询工具"""
        return ToolSchemaBuilder("get_weather", "获取指定城市的天气信息") \
            .add_param("city", "string", "城市名称，如'北京'、'上海'", required=True) \
            .add_param("unit", "string", "温度单位", required=False, enum=["celsius", "fahrenheit"], default="celsius") \
            .build()

    @staticmethod
    def search() -> ToolSchema:
        """知识库搜索工具"""
        return ToolSchemaBuilder("search_knowledge", "搜索内部知识库获取相关信息") \
            .add_param("query", "string", "搜索关键词或问题", required=True) \
            .add_param("max_results", "integer", "最大返回结果数", required=False, default=5) \
            .build()

    @staticmethod
    def calculator() -> ToolSchema:
        """数学计算工具"""
        return ToolSchemaBuilder("calculate", "执行数学计算") \
            .add_param("expression", "string", "数学表达式，如'2 + 3 * 4'", required=True) \
            .build()


# ============================================================
# 模块：入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Tool 定义规范演示")
    print("=" * 60)

    # 1. 使用构建器创建工具
    print("\n📝 使用 ToolSchemaBuilder 创建工具定义:")
    weather_tool = ToolLibrary.weather()
    print(json.dumps(weather_tool.to_openai_format(), indent=2, ensure_ascii=False))

    # 2. 验证工具定义
    print("\n✅ 验证工具定义:")
    validator = SchemaValidator()
    errors = validator.validate(weather_tool)
    if errors:
        print("错误:")
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  工具 '{weather_tool.name}' 验证通过！")

    # 3. 验证不合规的工具
    print("\n❌ 验证不合规的工具:")
    bad_tool = ToolSchema(name="", description="")
    bad_tool.parameters.append(ParamDef(name="", type="invalid", description=""))
    errors = validator.validate(bad_tool)
    for e in errors:
        print(f"  ❌ {e}")

    # 4. 工具库展示
    print("\n📚 预定义工具库:")
    tools = [ToolLibrary.weather(), ToolLibrary.search(), ToolLibrary.calculator()]
    for t in tools:
        params = ", ".join([f"{p.name} ({p.type})" for p in t.parameters])
        print(f"  • {t.name}: {params}")
