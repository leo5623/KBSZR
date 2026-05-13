"""云端API改写器 - 多供应商支持"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx
from loguru import logger


@dataclass
class RewriteResult:
    """改写结果"""
    success: bool
    text: str = ""
    error: str = ""
    provider: str = ""
    model: str = ""
    usage: Dict[str, Any] = None  # token使用量等


class BaseRewriter(ABC):
    """改写器基类"""

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
            return response.status_code in (200, 400, 401)  # 401表示需要认证但服务可达
        except Exception as e:
            logger.warning(f"Tongyi health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Tongyi rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="tongyi",
                model=self.model
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
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"OpenAI rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="openai",
                model=self.model
            )


class ClaudeRewriter(BaseRewriter):
    """Claude改写器"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
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
            # Claude没有简单的health接口，用models接口代替
            response = await client.post(
                f"{self.base_url}/messages",
                json={"model": self.model, "max_tokens": 1, "messages": []}
            )
            return response.status_code != 401  # 只要不是认证错误就认为服务可达
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Claude rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="claude",
                model=self.model
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
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"DeepSeek rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="deepseek",
                model=self.model
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
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Doubao rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="doubao",
                model=self.model
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
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Wenxin rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="wenxin",
                model=self.model
            )


class HunyuanRewriter(BaseRewriter):
    """腾讯混元改写器"""

    def __init__(self, api_key: str, secret_key: str, model: str = "hunyuan"):
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
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Hunyuan rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="hunyuan",
                model=self.model
            )


class PanguRewriter(BaseRewriter):
    """华为云盘古改写器"""

    def __init__(self, api_key: str, model: str = "pangu-2.0"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://huaweicloud.com/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"PanguRewriter initialized: model={model}")

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
            logger.warning(f"Pangu health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
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
                provider="pangu",
                model=self.model,
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Pangu rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="pangu",
                model=self.model
            )


class SparkRewriter(BaseRewriter):
    """科大讯飞星火改写器"""

    def __init__(self, api_key: str, app_id: str, model: str = "generalv3"):
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
            response = await client.get(f"{self.base_url}/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Spark health check failed: {e}")
            return False

    async def rewrite(
        self,
        text: str,
        scenario: Optional[str] = None,
        industry: Optional[str] = None,
        style: Optional[str] = None
    ) -> RewriteResult:
        prompt = self._build_prompt(text, scenario, industry, style)

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/v3.1/chat",
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
                usage=result.get("usage", {})
            )

        except Exception as e:
            logger.error(f"Spark rewrite failed: {e}")
            return RewriteResult(
                success=False,
                error=str(e),
                provider="spark",
                model=self.model
            )


# 供应商映射
REWRITER_PROVIDERS = {
    "tongyi": TongyiRewriter,
    "openai": OpenAIRewriter,
    "claude": ClaudeRewriter,
    "deepseek": DeepSeekRewriter,
    "doubao": DoubaoRewriter,
    "wenxin": WenxinRewriter,
    "hunyuan": HunyuanRewriter,
    "pangu": PanguRewriter,
    "spark": SparkRewriter,
}


def create_rewriter(provider: str, **kwargs) -> BaseRewriter:
    """创建改写器实例"""
    rewriter_class = REWRITER_PROVIDERS.get(provider.lower())
    if rewriter_class is None:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(REWRITER_PROVIDERS.keys())}")
    return rewriter_class(**kwargs)