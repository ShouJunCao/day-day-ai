"""
slot_filler.py — 槽位填充器
提供三种槽位填充实现：
1. 基于 CRF 的传统序列标注方法
2. 基于正则和规则的轻量方法
3. 基于 LLM 的端到端方法
"""
import os
import re
from typing import Optional
from datetime import datetime, timedelta


class SlotFiller:
    """
    槽位填充器：从用户输入中提取结构化参数。

    提供两种模式：
    - rule: 基于正则表达式和规则匹配，零依赖
    - crf: 基于 CRF 序列标注，需要 sklearn-crfsuite
    """

    def __init__(self, mode: str = "rule"):
        self.mode = mode

    def fill(self, text: str, slot_schema: dict) -> dict:
        """
        从文本中提取槽位值。

        Args:
            text: 用户输入文本
            slot_schema: 槽位定义，格式如:
                {
                    "departure": {"type": "city", "required": True},
                    "arrival": {"type": "city", "required": True},
                    "date": {"type": "date", "required": True},
                }

        Returns:
            {
                "slots": {"slot_name": value, ...},
                "missing": ["slot_name", ...],
                "confidence": float,
            }
        """
        if self.mode == "rule":
            return self._fill_rule(text, slot_schema)
        else:
            return self._fill_crf(text, slot_schema)

    def _fill_rule(self, text: str, slot_schema: dict) -> dict:
        """基于规则的槽位提取"""
        slots = {}
        missing = []

        # 预定义城市列表
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都",
                  "南京", "武汉", "重庆", "西安", "青岛", "厦门"]

        # 找出文本中所有城市出现的位置
        city_positions = []
        for city in cities:
            start = 0
            while True:
                idx = text.find(city, start)
                if idx == -1:
                    break
                city_positions.append((idx, city))
                start = idx + 1
        city_positions.sort()

        # 按出现顺序分配城市到槽位
        city_idx = 0
        dates_found = []
        numbers_found = []

        # 先提取日期和数字
        for match in re.finditer(r"\d{4}-\d{2}-\d{2}", text):
            dates_found.append(match.group())
        today = datetime.now()
        relative = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3}
        for word, days in relative.items():
            if word in text:
                dates_found.append(
                    (today + timedelta(days=days)).strftime("%Y-%m-%d")
                )

        for match in re.finditer(r"(\d+)", text):
            val = match.group()
            # 排除看起来像年份的数字
            if len(val) == 4 and int(val) > 1900 and int(val) < 2100:
                continue
            numbers_found.append(val)

        date_idx = 0
        number_idx = 0

        for slot_name, definition in slot_schema.items():
            slot_type = definition.get("type", "text")
            value = None

            if slot_type == "city":
                if city_idx < len(city_positions):
                    value = city_positions[city_idx][1]
                    city_idx += 1
            elif slot_type == "date":
                if date_idx < len(dates_found):
                    value = dates_found[date_idx]
                    date_idx += 1
            elif slot_type == "number":
                if number_idx < len(numbers_found):
                    value = numbers_found[number_idx]
                    number_idx += 1
            elif slot_type == "order_id":
                value = self._extract_order_id(text)
            else:
                value = text

            if value:
                slots[slot_name] = value
            elif definition.get("required", False):
                missing.append(slot_name)

        return {
            "slots": slots,
            "missing": missing,
            "confidence": 0.7 if not missing else 0.3,
        }

    def _fill_crf(self, text: str, slot_schema: dict) -> dict:
        """
        基于 CRF 的槽位提取（需要 sklearn-crfsuite）。
        使用 BIO 标记法进行序列标注。
        """
        try:
            import sklearn_crfsuite
        except ImportError:
            raise ImportError(
                "CRF 模式需要安装 sklearn-crfsuite: pip install sklearn-crfsuite"
            )

        # 实际实现需要训练数据和特征工程
        # 这里提供接口框架
        return {
            "slots": {},
            "missing": list(slot_schema.keys()),
            "confidence": 0.0,
            "note": "CRF 模式需要训练数据，请使用 rule 模式或提供训练数据",
        }

    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        """
        从文本中提取日期。
        支持格式：YYYY-MM-DD、今天、明天、后天等。
        """
        # 匹配 YYYY-MM-DD 格式
        date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if date_match:
            return date_match.group()

        # 匹配相对日期
        today = datetime.now()
        relative = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3}
        for word, days in relative.items():
            if word in text:
                return (today + timedelta(days=days)).strftime("%Y-%m-%d")

        return None

    @staticmethod
    def _extract_number(text: str) -> Optional[str]:
        """从文本中提取数字"""
        match = re.search(r"(\d+)", text)
        if match:
            return match.group()
        return None

    @staticmethod
    def _extract_order_id(text: str) -> Optional[str]:
        """提取订单号（格式如 #ABC123）"""
        match = re.search(r"#[A-Z0-9]+", text)
        if match:
            return match.group()
        return None


class LLMSlotFiller:
    """
    基于 LLM 的槽位填充器。

    优势：
    - 不需要标注数据
    - 支持复杂语义理解
    - 可以处理模糊表达
    """

    def __init__(self):
        self.api_key = os.getenv("API_KEY", "")
        self.base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("MODEL", "gpt-4o-mini")

    def extract(self, text: str, schema: dict) -> dict:
        """
        使用 LLM 提取槽位信息。

        Args:
            text: 用户输入
            schema: 槽位定义（JSON Schema 格式）

        Returns:
            {"slots": {...}, "missing": [...], "confidence": float}
        """
        import json
        import httpx

        prompt = (
            f"请从以下文本中提取槽位信息。\n\n"
            f"用户输入：{text}\n\n"
            f"请以以下 JSON 格式输出：\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=False)}"
        )

        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"]
            return json.loads(result)
