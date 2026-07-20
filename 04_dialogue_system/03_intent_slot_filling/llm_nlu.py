"""
llm_nlu.py — 基于 LLM 的对话理解
使用 Function Calling 和 JSON Schema 进行意图识别和槽位填充。
整合 IntentClassifier 和 SlotFiller，提供端到端的对话理解能力。
"""
import os
import json
import httpx
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class NLUResult:
    """对话理解结果"""
    intent: str = ""
    confidence: float = 0.0
    slots: dict = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class DialogueUnderstandingClient:
    """
    基于 LLM 的对话理解客户端

    使用 JSON Schema 强制输出格式，确保结果可解析。
    支持任意 OpenAI 兼容 API 的 LLM。
    """

    def __init__(self):
        self.api_key = os.getenv("API_KEY", "")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("MODEL", "gpt-4o-mini")

    def understand(self, user_input: str) -> NLUResult:
        """
        解析用户输入的意图和槽位。

        Returns:
            NLUResult: 包含意图、槽位、缺失槽位等完整信息
        """
        # System Prompt 定义理解规则
        system_msg = (
            "你是一个对话理解专家。请分析用户输入，提取意图和槽位。\n"
            "支持的意图包括：book_flight, book_hotel, query_weather, "
            "query_order, cancel_booking, greet, chitchat, unknown\n"
            "请以以下 JSON 格式输出（不要输出其他内容）：\n"
            '{\n'
            '  "intent": "意图名称",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "slots": {"槽位名": "值", ...},\n'
            '  "missing_slots": ["缺失的必要槽位名", ...]\n'
            '}'
        )

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_input},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                result = json.loads(content)

                return NLUResult(
                    intent=result.get("intent", "unknown"),
                    confidence=float(result.get("confidence", 0.0)),
                    slots=result.get("slots", {}),
                    missing_slots=result.get("missing_slots", []),
                    raw_response=content,
                )
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            return NLUResult(
                intent="unknown",
                confidence=0.0,
                missing_slots=[],
                raw_response=f"Error: {e}",
            )


# Schema 定义（用于 JSON Schema 强制输出）
FLIGHT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": [
            "book_flight", "query_weather", "query_order",
            "cancel_booking", "greet", "chitchat", "unknown"
        ]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "slots": {
            "type": "object",
            "properties": {
                "departure": {"type": "string", "description": "出发城市"},
                "arrival": {"type": "string", "description": "到达城市"},
                "date": {
                    "type": "string",
                    "description": "出发日期，格式 YYYY-MM-DD",
                },
                "return_date": {
                    "type": "string",
                    "description": "返回日期（单程时省略）",
                },
                "cabin_class": {
                    "type": "string",
                    "description": "舱位等级（经济舱/商务舱/头等舱）",
                },
                "passengers": {
                    "type": "integer",
                    "description": "乘客人数",
                },
            },
            "required": ["departure", "arrival", "date"],
        },
        "missing_slots": {
            "type": "array",
            "items": {"type": "string"},
            "description": "缺失的必要槽位，用于后续追问",
        },
    },
    "required": ["intent", "confidence", "slots", "missing_slots"],
}


class SchemaBasedNLU:
    """
    基于 JSON Schema 的对话理解
    适用于任何支持 JSON mode 的 LLM，不依赖 Pydantic/OpenAI SDK
    """

    def __init__(self, schema: Optional[dict] = None):
        self.schema = schema or FLIGHT_SCHEMA
        self.api_key = os.getenv("API_KEY", "")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("MODEL", "gpt-4o-mini")

    def extract(self, text: str) -> Optional[dict]:
        """提取意图和槽位"""
        prompt = (
            f"请从以下文本中提取意图和槽位信息。\n\n"
            f"用户输入：{text}\n\n"
            f"请以以下 JSON 格式输出：\n"
            f"{json.dumps(self.schema, indent=2, ensure_ascii=False)}"
        )

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return json.loads(resp.json()["choices"][0]["message"]["content"])

    def validate(self, result: dict) -> tuple[bool, list[str]]:
        """验证提取结果是否完整"""
        errors = []
        if not result.get("intent"):
            errors.append("缺少 intent")
        slots = result.get("slots", {})
        required = self.schema.get("properties", {}).get(
            "slots", {}
        ).get("required", [])
        for field_name in required:
            if field_name not in slots:
                errors.append(f"缺少必要槽位: {field_name}")
        return len(errors) == 0, errors
