"""本地Ollama改写器"""
from typing import Optional
import httpx
from loguru import logger


class LocalRewriter:
    """基于本地Ollama的文案改写"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"LocalRewriter initialized: {base_url}, model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def check_health(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        使用Ollama生成改写后的文案

        Args:
            prompt: 用户输入的文案
            system_prompt: 系统提示词（可选）

        Returns:
            改写后的文案
        """
        client = await self._get_client()

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("message", {}).get("content", "")
            logger.debug(f"Ollama generated {len(generated_text)} chars")
            return generated_text

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> str:
        """
        改写文案

        Args:
            text: 原始文案
            scenario: 场景类型（如"种草安利"、"干货分享"）
            industry: 行业（如"beauty"、"knowledge"）
            style: 风格偏好（如"亲切"、"专业"）

        Returns:
            改写后的文案
        """
        # 构建提示词
        prompt = self._build_prompt(text, scenario, industry, style)

        # 生成改写
        result = await self.generate(prompt)

        return result

    def _build_prompt(
        self,
        text: str,
        scenario: Optional[str],
        industry: Optional[str],
        style: Optional[str]
    ) -> str:
        """构建提示词"""
        parts = []

        # 角色设定
        if industry == "beauty":
            role = "你是一位专业美妆博主，用亲切、热情的语气改写以下文案。"
        elif industry == "knowledge":
            role = "你是一位知识博主，用权威但易懂的语气改写以下文案。"
        elif industry == "ecommerce":
            role = "你是一位专业带货主播，用有说服力的语气改写以下文案。"
        else:
            role = "你是一位专业的内容创作者，改写以下文案使其更吸引人。"

        parts.append(role)

        # 场景补充
        if scenario:
            scenario_hints = {
                "种草安利": "突出产品卖点，强调使用效果，让读者产生购买欲望。",
                "干货分享": "用简洁清晰的语言传达有价值的信息，让读者觉得有用。",
                "教程分享": "用步骤化的方式讲解，确保读者能轻松上手。",
                "产品介绍": "突出产品特点，强调优势和性价比。",
                "限时优惠": "营造紧迫感，强调限时限量，促进行动。"
            }
            hint = scenario_hints.get(scenario, "")
            if hint:
                parts.append(hint)

        # 风格补充
        if style:
            style_hints = {
                "亲切": "语气温暖，像朋友聊天一样",
                "专业": "措辞严谨，展现专业性",
                "活泼": "语言轻快，有活力",
                "沉稳": "语气稳重，给人可靠感"
            }
            hint = style_hints.get(style, "")
            if hint:
                parts.append(f"风格要求：{hint}")

        parts.append(f"\n原始文案：\n{text}")
        parts.append("\n请直接输出改写后的文案，不需要解释。")

        return "\n".join(parts)


# 便捷函数
async def rewrite_with_local(
    text: str,
    scenario: Optional[str] = None,
    industry: Optional[str] = None,
    style: Optional[str] = None
) -> str:
    """使用本地Ollama改写文案"""
    rewriter = LocalRewriter()
    try:
        return await rewriter.rewrite(text, scenario, industry, style)
    finally:
        await rewriter.close()