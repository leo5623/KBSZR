"""文案改写模块测试"""
import asyncio
import sys
sys.path.insert(0, "D:/小程序代码/KBSZR")

from src.business.rewriter.router import RewriterRouter, RewriteConfig, RewriteMode, RewriteRequest


async def test_local_rewriter():
    """测试本地Ollama改写"""
    print("=== 测试本地Ollama改写 ===")

    router = RewriterRouter(
        config=RewriteConfig(mode=RewriteMode.LOCAL)
    )

    # 健康检查
    health = await router.health_check()
    print(f"健康状态: {health}")

    # 测试改写
    request = RewriteRequest(
        text="今天给大家推荐一款非常好用的面霜",
        industry="beauty",
        scenario="种草安利",
        style="亲切"
    )

    response = await router.rewrite(request)
    print(f"成功: {response.success}")
    print(f"模式: {response.mode}")
    print(f"原文: {request.text}")
    print(f"改写: {response.rewritten_text}")

    if not response.success:
        print(f"错误: {response.error}")

    await router.close()
    print()


async def test_scenario_manager():
    """测试场景管理器"""
    print("=== 测试场景管理器 ===")

    from src.business.rewriter.scenario_manager import get_scenario_manager

    manager = get_scenario_manager()

    # 列出行业
    industries = manager.list_industries()
    print(f"行业列表: {[i['name'] for i in industries]}")

    # 列出场景
    scenarios = manager.list_scenarios("beauty")
    print(f"美妆场景: {[s['name'] for s in scenarios]}")

    # 获取提示词
    prompt = manager.get_prompt("beauty", "种草安利")
    print(f"种草安利的提示词: {prompt[:50]}...")
    print()


async def test_api_rewriter_import():
    """测试API改写器导入"""
    print("=== 测试API改写器导入 ===")

    from src.business.rewriter.api_rewriter import (
        TongyiRewriter,
        OpenAIRewriter,
        ClaudeRewriter,
        DeepSeekRewriter,
        DoubaoRewriter,
        create_rewriter
    )

    print(f"支持的供应商: tongyi, openai, claude, deepseek, doubao")

    # 测试创建
    try:
        rewriter = create_rewriter("tongyi", api_key="test", model="qwen-max")
        print(f"创建通义千问改写器: {type(rewriter).__name__}")
    except Exception as e:
        print(f"创建失败（预期，因为没有真实API key）: {e}")

    print()


async def main():
    print("=" * 50)
    print("文案改写模块测试")
    print("=" * 50)
    print()

    # 测试场景管理器
    await test_scenario_manager()

    # 测试API改写器导入
    await test_api_rewriter_import()

    # 测试本地改写（需要Ollama运行）
    await test_local_rewriter()

    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())