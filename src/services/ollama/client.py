"""Ollama本地大模型客户端"""
import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, AsyncIterator

from loguru import logger


@dataclass
class OllamaConfig:
    """Ollama配置"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"  # 默认模型
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    timeout: int = 120


class OllamaClient:
    """
    Ollama本地大模型客户端

    支持的模型（需要先通过ollama pull安装）：
    - qwen2.5:7b / qwen2.5:14b
    - llama3.1:8b
    - deepseek-r1:7b
    - mistral:7b
    - 等
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._base_url = self.config.base_url.rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        对话补全

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称（覆盖配置）
            stream: 是否流式输出

        Returns:
            响应字典
        """
        import httpx

        endpoint = f"{self._base_url}/api/chat"
        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout: {self._base_url}")
            return {"error": "请求超时，请检查Ollama服务是否启动"}
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return {"error": str(e)}

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        文本生成

        Args:
            prompt: 提示词
            model: 模型名称
            system: 系统提示词
            stream: 是否流式输出

        Returns:
            响应字典
        """
        import httpx

        endpoint = f"{self._base_url}/api/generate"
        payload = {
            "model": model or self.config.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": self.config.max_tokens,
            }
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout: {self._base_url}")
            return {"error": "请求超时，请检查Ollama服务是否启动"}
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return {"error": str(e)}

    async def list_models(self) -> List[Dict[str, Any]]:
        """列出已安装的模型"""
        import httpx

        endpoint = f"{self._base_url}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model: str) -> AsyncIterator[str]:
        """
        下载模型（流式）

        Args:
            model: 模型名称

        Yields:
            下载进度信息
        """
        import httpx

        endpoint = f"{self._base_url}/api/pull"
        payload = {"name": model, "stream": True}

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream("POST", endpoint, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "status" in data:
                                    yield data["status"]
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            yield f"下载失败: {e}"

    async def health_check(self) -> Dict[str, Any]:
        """检查Ollama服务健康状态"""
        import httpx

        endpoint = f"{self._base_url}/"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    models = await self.list_models()
                    return {
                        "available": True,
                        "url": self._base_url,
                        "models": [m["name"] for m in models]
                    }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "hint": "请确保Ollama服务已启动：ollama serve"
            }

        return {"available": False}


# 便捷函数
async def chat_once(
    prompt: str,
    model: str = "qwen2.5:7b",
    system: Optional[str] = None
) -> str:
    """单轮对话"""
    config = OllamaConfig(model=model)
    client = OllamaClient(config)

    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})

    result = await client.chat(messages)
    await client.close()

    if "error" in result:
        return f"Error: {result['error']}"

    return result.get("message", {}).get("content", "")


async def rewrite_text(
    text: str,
    style: str = "亲切自然",
    model: str = "qwen2.5:7b"
) -> str:
    """使用本地模型改写文案"""
    config = OllamaConfig(model=model)
    client = OllamaClient(config)

    prompt = f"""你是一个专业的文案改写专家。请将下面的文案改写成"{style}"的风格。

原文：
{text}

要求：
1. 保持原意不变
2. 语言通顺流畅
3. 适合短视频口播

改写后的文案："""

    result = await client.generate(prompt=prompt)
    await client.close()

    if "error" in result:
        return f"Error: {result['error']}"

    return result.get("response", "").strip()