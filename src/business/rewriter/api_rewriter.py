"""云端API改写器 - 多供应商支持（增强版）"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import httpx
import time
from loguru import logger


class RewriteStyle(Enum):
    """改写风格"""
    PERSONABLE = "personable"  # 亲切自然
    PROFESSIONAL = "professional"  # 专业正式
    CASUAL = "casual"  # 轻松随意
    EMOTIONAL = "emotional"  # 情感丰富
    Humorous = "humorous"  # 幽默风趣


@dataclass
class RewriteResult:
    """改写结果"""
    success: bool
    text: str = ""
    error: str = ""
    provider: str = ""
    model: str = ""
    usage: Dict[str, Any] = None  # token使用量等
    rewrite_time: float = 0.0  # 改写耗时


@dataclass
class RewriteRequest:
    """改写请求"""
    text: str
    scenario: Optional[str] = None
    industry: Optional[str] = None
    style: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    reference_texts: List[str] = field(default_factory=list)  # 参考文案


@dataclass
class BatchRewriteRequest:
    """批量改写请求"""
    texts: List[str]
    scenario: Optional[str] = None
    industry: Optional[str] = None
    style: Optional[str] = None


@dataclass
class BatchRewriteResult:
    """批量改写结果"""
    success: bool
    results: List[RewriteResult] = field(default_factory=list)
    total_time: float = 0.0
    error: str = ""


@dataclass
class RewriteHistoryItem:
    """改写历史记录"""
    id: str
    timestamp: float
    original_text: str
    rewritten_text: str
    provider: str
    model: str
    scenario: str = ""
    industry: str = ""


class BaseRewriter(ABC):
    """改写器基类"""

    # 行业角色映射
    INDUSTRY_ROLES = {
        "beauty": "你是一位专业美妆博主，用亲切、热情的语气改写以下文案。",
        "knowledge": "你是一位知识博主，用权威但易懂的语气改写以下文案。",
        "ecommerce": "你是一位专业带货主播，用有说服力的语气改写以下文案。",
        "food": "你是一位美食达人，用生动、诱人的语气改写以下文案。",
        "education": "你是一位教育专家，用耐心、专业的语气改写以下文案。",
        "fitness": "你是一位健身教练，用充满活力的语气改写以下文案。",
        "tech": "你是一位科技博主，用简洁、专业的语气改写以下文案。",
        "finance": "你是一位财经分析师，用严谨、权威的语气改写以下文案。",
        "entertainment": "你是一位娱乐博主，用轻松、有趣的语气改写以下文案。",
        "travel": "你是一位旅行博主，用向往、美好的语气改写以下文案。",
    }

    # 场景提示映射
    SCENARIO_HINTS = {
        "种草安利": "突出产品卖点，强调使用效果，让读者产生购买欲望。结合个人使用体验，让文案更有说服力。",
        "干货分享": "用简洁清晰的语言传达有价值的信息，让读者觉得学到了东西。多用数字和具体例子。",
        "教程分享": "用步骤化的方式讲解，确保读者能轻松上手。语言要清晰易懂的。",
        "产品介绍": "突出产品特点，强调优势和性价比。描述要具体、有条理。",
        "限时优惠": "营造紧迫感，强调限时限量，促进行动。使用紧迫性词汇如'仅限'、'立即'等。",
        "品牌故事": "讲述品牌背后的故事，传递品牌价值观，建立情感连接。",
        "对比测评": "客观对比产品优劣，帮助读者做出选择。保持中立，不贬低竞品。",
        "使用场景": "描述具体的使用场景，让读者产生代入感。文案要生动、有画面感。",
    }

    # 风格提示映射
    STYLE_HINTS = {
        "亲切": "语气温暖，像朋友聊天一样，多用'咱们'、'小伙伴'等亲和词汇",
        "专业": "措辞严谨，展现专业性，使用行业术语和数据支撑",
        "活泼": "语言轻快，有活力，多用感叹句和活泼的词汇",
        "沉稳": "语气稳重，给人可靠感，句式工整，避免过度情绪化",
        "幽默": "幽默风趣，适当加入梗和段子，让读者觉得有趣",
        "情感": "情感丰富，打动人心，让读者产生共鸣",
        "简洁": "简洁明了，不废话，直接给出核心信息",
        "故事": "用故事的形式表达，有情节、有转折，更吸引人",
    }

    @abstractmethod
    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> RewriteResult:
        """改写文案"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """检查服务是否可用"""
        pass

    def _build_prompt(
        self,
        text: str,
        scenario: Optional[str],
        industry: Optional[str],
        style: Optional[str],
        reference_texts: List[str] = None
    ) -> str:
        """构建提示词"""
        parts = []

        # 角色设定
        role = self.INDUSTRY_ROLES.get(industry, self.INDUSTRY_ROLES.get("ecommerce"))
        parts.append(role)

        # 场景补充
        if scenario and scenario in self.SCENARIO_HINTS:
            parts.append(self.SCENARIO_HINTS[scenario])

        # 风格补充
        if style and style in self.STYLE_HINTS:
            parts.append(f"风格要求：{self.STYLE_HINTS[style]}")

        # 参考文案
        if reference_texts:
            parts.append("\n参考文案风格：")
            for i, ref in enumerate(reference_texts[:3]):  # 最多3篇参考
                parts.append(f"{i+1}. {ref[:200]}...")

        # 加入字数要求
        text_len = len(text)
        if text_len > 500:
            parts.append(f"\n注意：原文较长({text_len}字)，请保持核心信息不变，适当精简冗余内容。")

        parts.append(f"\n原始文案：\n{text}")
        parts.append("\n请直接输出改写后的文案，不需要解释。改写后的文案应该适合口播，长度适中(60-150字)。")

        return "\n".join(parts)

    def _estimate_price(self, text: str, provider: str) -> Dict[str, float]:
        """估算API费用"""
        # 简单估算：假设1字符=1token
        input_tokens = len(text) * 2  # 包含prompt
        output_tokens = min(len(text) * 1.5, 1500)  # 输出约1.5倍

        # 各供应商价格（仅供参考）
        prices = {
            "tongyi": 0.0001,  # $0.001/1K tokens
            "openai": 0.00015,
            "claude": 0.00018,
            "deepseek": 0.00007,
            "doubao": 0.00008,
        }

        rate = prices.get(provider, 0.0001)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": (input_tokens + output_tokens) * rate
        }


class TongyiRewriter(BaseRewriter):
    """通义千问改写器"""

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"TongyiRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/services/aigc/text-generation/generation")
            return response.status_code in (200, 400, 401)
        except Exception as e:
            logger.warning(f"Tongyi health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": temperature,
                "top_p": 0.9,
                "max_tokens": max_tokens
            }
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result.get("output", {}).get("text", "")
            return RewriteResult(
                success=True,
                text=output_text,
                provider="tongyi",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Tongyi rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="tongyi",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class OpenAIRewriter(BaseRewriter):
    """OpenAI GPT改写器"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"OpenAIRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="openai",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"OpenAI rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="openai",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class ClaudeRewriter(BaseRewriter):
    """Claude改写器"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"ClaudeRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/messages",
                json={"model": self.model, "max_tokens": 1, "messages": []}
            )
            return response.status_code != 401
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/messages",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["content"][0]["text"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="claude",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Claude rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="claude",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class DeepSeekRewriter(BaseRewriter):
    """DeepSeek改写器"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"DeepSeekRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"DeepSeek health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="deepseek",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"DeepSeek rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="deepseek",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class DoubaoRewriter(BaseRewriter):
    """豆包改写器"""

    def __init__(self, api_key: str, model: str = "doubao-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"DoubaoRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Doubao health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="doubao",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Doubao rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="doubao",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class WenxinRewriter(BaseRewriter):
    """百度文心一言改写器"""

    def __init__(self, api_key: str, secret_key: str, model: str = "ernie-4.0-8k-latest"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"WenxinRewriter initialized: model={model}")

    async def _get_access_token(self) -> str:
        """获取access_token"""
        if self._access_token:
            return self._access_token

        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, params=params)
            result = response.json()
            self._access_token = result.get("access_token", "")
            return self._access_token

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            token = await self._get_access_token()
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            return await self._get_access_token() != ""
        except Exception as e:
            logger.warning(f"Wenxin health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                "https://qianfan.baidubce.com/v2/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="wenxin",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Wenxin rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="wenxin",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class HunyuanRewriter(BaseRewriter):
    """腾讯混元改写器"""

    def __init__(self, api_key: str, secret_key: str, model: str = "hunyuan-latest"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"HunyuanRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("https://hunyuan.cloud.tencent.com/api/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Hunyuan health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                "https://hunyuan.cloud.tencent.com/api/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="hunyuan",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Hunyuan rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="hunyuan",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class SparkRewriter(BaseRewriter):
    """科大讯飞星火改写器"""

    def __init__(self, api_key: str, app_id: str, model: str = "generalv3.5"):
        self.api_key = api_key
        self.app_id = app_id
        self.model = model
        self.base_url = "https://spark-api.xf-yun.com"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"SparkRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/v3.5/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Spark health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/v3.5/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="spark",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Spark rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="spark",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class MiniMaxRewriter(BaseRewriter):
    """MiniMax改写器"""

    def __init__(self, api_key: str, model: str = "abab6-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.minimax.chat/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"MiniMaxRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"MiniMax health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result["choices"][0]["message"]["content"]
            return RewriteResult(
                success=True,
                text=output_text,
                provider="minimax",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"MiniMax rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="minimax",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


class QwenTurboRewriter(BaseRewriter):
    """通义千问Turbo改写器（更快速）"""

    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"QwenTurboRewriter initialized: model={model}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60.0
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/services/aigc/text-generation/generation")
            return response.status_code in (200, 400, 401)
        except Exception as e:
            logger.warning(f"QwenTurbo health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> RewriteResult:
        start_time = time.time()
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": temperature,
                "top_p": 0.9,
                "max_tokens": max_tokens
            }
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            output_text = result.get("output", {}).get("text", "")
            return RewriteResult(
                success=True,
                text=output_text,
                provider="qwen-turbo",
                model=self.model,
                usage=result.get("usage", {}),
                rewrite_time=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"QwenTurbo rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="qwen-turbo",
                model=self.model,
                rewrite_time=time.time() - start_time
            )


# 供应商映射
REWRITER_PROVIDERS = {
    "tongyi": TongyiRewriter,
    "qwen-turbo": QwenTurboRewriter,
    "openai": OpenAIRewriter,
    "claude": ClaudeRewriter,
    "deepseek": DeepSeekRewriter,
    "doubao": DoubaoRewriter,
    "wenxin": WenxinRewriter,
    "hunyuan": HunyuanRewriter,
    "spark": SparkRewriter,
    "minimax": MiniMaxRewriter,
}


# 供应商信息
REWRITER_PROVIDER_INFO = {
    "tongyi": {"name": "通义千问", "model": "qwen-max", "price_rank": 2, "speed_rank": 3},
    "qwen-turbo": {"name": "通义千问Turbo", "model": "qwen-turbo", "price_rank": 1, "speed_rank": 1},
    "openai": {"name": "OpenAI GPT", "model": "gpt-4o", "price_rank": 4, "speed_rank": 3},
    "claude": {"name": "Claude", "model": "claude-3-5-sonnet", "price_rank": 4, "speed_rank": 3},
    "deepseek": {"name": "DeepSeek", "model": "deepseek-chat", "price_rank": 1, "speed_rank": 2},
    "doubao": {"name": "豆包", "model": "doubao-pro", "price_rank": 2, "speed_rank": 2},
    "wenxin": {"name": "文心一言", "model": "ernie-4.0", "price_rank": 3, "speed_rank": 3},
    "hunyuan": {"name": "腾讯混元", "model": "hunyuan-latest", "price_rank": 3, "speed_rank": 3},
    "spark": {"name": "讯飞星火", "model": "generalv3.5", "price_rank": 3, "speed_rank": 2},
    "minimax": {"name": "MiniMax", "model": "abab6-chat", "price_rank": 2, "speed_rank": 2},
}


def create_rewriter(provider: str, **kwargs) -> BaseRewriter:
    """创建改写器实例"""
    rewriter_class = REWRITER_PROVIDERS.get(provider.lower())
    if rewriter_class is None:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(REWRITER_PROVIDERS.keys())}")
    return rewriter_class(**kwargs)


def list_providers() -> Dict[str, Dict]:
    """列出所有可用的供应商"""
    return REWRITER_PROVIDER_INFO.copy()


def get_provider_info(provider: str) -> Optional[Dict]:
    """获取供应商信息"""
    return REWRITER_PROVIDER_INFO.get(provider)


class RewriteHistory:
    """改写历史记录管理器"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._history: List[RewriteHistoryItem] = []

    def add(self, item: RewriteHistoryItem):
        """添加历史记录"""
        self._history.insert(0, item)
        if len(self._history) > self.max_size:
            self._history.pop()

    def get_recent(self, limit: int = 10) -> List[RewriteHistoryItem]:
        """获取最近的历史记录"""
        return self._history[:limit]

    def search(self, keyword: str) -> List[RewriteHistoryItem]:
        """搜索历史记录"""
        return [item for item in self._history if keyword in item.original_text or keyword in item.rewritten_text]

    def clear(self):
        """清空历史记录"""
        self._history.clear()

    def export(self) -> List[Dict]:
        """导出为列表"""
        return [
            {
                "id": item.id,
                "timestamp": item.timestamp,
                "original_text": item.original_text,
                "rewritten_text": item.rewritten_text,
                "provider": item.provider,
                "scenario": item.scenario,
                "industry": item.industry
            }
            for item in self._history
        ]


# 全局历史记录
_rewrite_history: Optional[RewriteHistory] = None


def get_rewrite_history() -> RewriteHistory:
    """获取改写历史记录管理器"""
    global _rewrite_history
    if _rewrite_history is None:
        _rewrite_history = RewriteHistory()
    return _rewrite_history