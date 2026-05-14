"""文案改写器测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.business.rewriter.api_rewriter import (
    BaseRewriter, RewriteResult, TongyiRewriter, OpenAIRewriter,
    DeepSeekRewriter, create_rewriter, REWRITER_PROVIDERS,
    REWRITER_PROVIDER_INFO, list_providers, get_provider_info,
    RewriteHistory, get_rewrite_history
)


class TestRewriteResult:
    """RewriteResult数据类测试"""

    def test_rewrite_result_success(self):
        """测试成功结果"""
        result = RewriteResult(
            success=True,
            text="改写后的文案内容",
            provider="tongyi",
            model="qwen-max",
            usage={"tokens": 100},
            rewrite_time=1.5
        )

        assert result.success is True
        assert result.text == "改写后的文案内容"
        assert result.provider == "tongyi"
        assert result.rewrite_time == 1.5

    def test_rewrite_result_failure(self):
        """测试失败结果"""
        result = RewriteResult(
            success=False,
            error="API调用失败",
            provider="openai"
        )

        assert result.success is False
        assert result.error == "API调用失败"


class TestTongyiRewriter:
    """通义千问改写器测试"""

    def test_init(self):
        """测试初始化"""
        rewriter = TongyiRewriter(api_key="test-key", model="qwen-max")

        assert rewriter.api_key == "test-key"
        assert rewriter.model == "qwen-max"
        assert rewriter.base_url == "https://dashscope.aliyuncs.com/api/v1"

    def test_build_prompt_with_industry(self):
        """测试提示词构建（行业）"""
        rewriter = TongyiRewriter(api_key="test")
        prompt = rewriter._build_prompt("原始文案", None, "beauty", None)

        assert "美妆" in prompt
        assert "亲切" in prompt or "热情" in prompt

    def test_build_prompt_with_scenario(self):
        """测试提示词构建（场景）"""
        rewriter = TongyiRewriter(api_key="test")
        prompt = rewriter._build_prompt("原始文案", "种草安利", None, None)

        assert "种草安利" in prompt or "产品卖点" in prompt

    def test_build_prompt_with_style(self):
        """测试提示词构建（风格）"""
        rewriter = TongyiRewriter(api_key="test")
        prompt = rewriter._build_prompt("原始文案", None, None, "亲切")

        assert "亲切" in prompt

    @pytest.mark.asyncio
    async def test_rewrite_success(self):
        """测试成功改写"""
        rewriter = TongyiRewriter(api_key="test-key", model="qwen-max")

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"text": "改写后文案"},
            "usage": {"tokens": 100}
        }

        with patch.object(rewriter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await rewriter.rewrite("原始文案", "种草安利", "beauty")

            assert result.success is True
            assert result.text == "改写后文案"
            assert result.provider == "tongyi"

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """测试健康检查"""
        rewriter = TongyiRewriter(api_key="test-key")

        mock_response = AsyncMock()
        mock_response.status_code = 200

        with patch.object(rewriter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await rewriter.health_check()
            assert result is True


class TestCreateRewriter:
    """create_rewriter工厂函数测试"""

    def test_create_tongyi_rewriter(self):
        """测试创建通义千问改写器"""
        rewriter = create_rewriter("tongyi", api_key="test")
        assert isinstance(rewriter, TongyiRewriter)

    def test_create_openai_rewriter(self):
        """测试创建OpenAI改写器"""
        rewriter = create_rewriter("openai", api_key="test")
        assert isinstance(rewriter, OpenAIRewriter)

    def test_create_deepseek_rewriter(self):
        """测试创建DeepSeek改写器"""
        rewriter = create_rewriter("deepseek", api_key="test")
        assert isinstance(rewriter, DeepSeekRewriter)

    def test_create_unknown_provider(self):
        """测试创建未知供应商"""
        with pytest.raises(ValueError) as exc_info:
            create_rewriter("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)


class TestRewriterProviders:
    """REWRITER_PROVIDERS映射测试"""

    def test_all_providers_available(self):
        """测试所有供应商都可用"""
        providers = ["tongyi", "openai", "claude", "deepseek", "doubao", "wenxin", "hunyuan", "spark", "minimax", "qwen-turbo"]
        for provider in providers:
            assert provider in REWRITER_PROVIDERS

    def test_provider_info(self):
        """测试供应商信息"""
        info = get_provider_info("tongyi")
        assert info is not None
        assert "name" in info
        assert info["name"] == "通义千问"

    def test_list_providers(self):
        """测试列出供应商"""
        providers = list_providers()
        assert len(providers) >= 9
        assert "tongyi" in providers
        assert "openai" in providers


class TestRewriteHistory:
    """RewriteHistory测试"""

    def test_add_history(self):
        """测试添加历史记录"""
        history = get_rewrite_history()
        history.clear()

        from src.business.rewriter.api_rewriter import RewriteHistoryItem
        item = RewriteHistoryItem(
            id="1",
            timestamp=1234567890,
            original_text="原文",
            rewritten_text="改写文",
            provider="tongyi",
            model="qwen-max"
        )

        history.add(item)
        recent = history.get_recent(limit=1)

        assert len(recent) == 1
        assert recent[0].original_text == "原文"

    def test_search_history(self):
        """测试搜索历史"""
        history = get_rewrite_history()
        history.clear()

        from src.business.rewriter.api_rewriter import RewriteHistoryItem
        history.add(RewriteHistoryItem(
            id="1", timestamp=1234567890,
            original_text="美妆产品推荐",
            rewritten_text="改写后内容",
            provider="tongyi", model="qwen-max"
        ))

        results = history.search("美妆")
        assert len(results) >= 1

    def test_export_history(self):
        """测试导出历史"""
        history = get_rewrite_history()
        history.clear()

        from src.business.rewriter.api_rewriter import RewriteHistoryItem
        history.add(RewriteHistoryItem(
            id="1", timestamp=1234567890,
            original_text="原文",
            rewritten_text="改写文",
            provider="tongyi", model="qwen-max"
        ))

        exported = history.export()
        assert len(exported) == 1
        assert exported[0]["original_text"] == "原文"