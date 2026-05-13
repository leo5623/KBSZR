"""TTS模块测试"""
import asyncio
import sys
sys.path.insert(0, "D:/小程序代码/KBSZR")

from src.business.tts.router import TTSRouter, TTSConfig, TTSRequest, TTSMode
from src.business.tts.aliyun_client import ALIYUN_VOICES, AliyunTTS


async def test_list_voices():
    """测试音色列表"""
    print("=== 测试音色列表 ===")

    voices = ALIYUN_VOICES
    print(f"阿里云预置音色 ({len(voices)}个):")
    for v in voices:
        print(f"  - {v.voice_id}: {v.name} ({v.description})")

    print()


async def test_tts_router_init():
    """测试TTS路由器初始化"""
    print("=== 测试TTS路由器 ===")

    config = TTSConfig(
        mode=TTSMode.CLOUD,
        provider="aliyun",
        aliyun_api_key="test_key",
        aliyun_region="cn-shanghai"
    )

    router = TTSRouter(config)
    print(f"TTS路由器初始化成功")
    print(f"  模式: {router.config.mode.value}")
    print(f"  供应商: {router.config.provider}")

    # 健康检查
    health = await router.health_check()
    print(f"  健康状态: {health}")

    # 列出音色
    voices = router.list_voices()
    print(f"  可用音色数: {len(voices)}")

    await router.close()
    print()


async def test_voice_clone():
    """测试声音克隆（不实际调用API）"""
    print("=== 测试声音克隆 ===")

    from src.business.tts.voice_clone import VoiceClone

    cloner = VoiceClone(api_key="test_key")
    print(f"VoiceClone 初始化成功")
    print(f"  base_url: {cloner.base_url}")

    await cloner.close()
    print()


async def main():
    print("=" * 50)
    print("TTS模块测试")
    print("=" * 50)
    print()

    # 测试音色列表
    await test_list_voices()

    # 测试TTS路由器
    await test_tts_router_init()

    # 测试声音克隆
    await test_voice_clone()

    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())