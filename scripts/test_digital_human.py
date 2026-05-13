"""数字人模块测试"""
import asyncio
import sys
sys.path.insert(0, "D:/小程序代码/KBSZR")

from src.business.digital_human.router import (
    DigitalHumanRouter, DigitalHumanConfig, DigitalHumanMode,
    DigitalHumanRequest, get_avatar_manager, get_background_manager
)
from src.business.digital_human.local_renderer import LocalRenderer


async def test_avatar_manager():
    """测试形象管理器"""
    print("=== 测试形象管理器 ===")

    manager = get_avatar_manager()

    # 列出分类
    categories = manager.list_categories()
    print(f"形象分类: {[c['name'] for c in categories]}")

    # 列出某个分类的形象
    avatars = manager.list_avatars("女生")
    print(f"女生类形象 ({len(avatars)}个):")
    for a in avatars:
        print(f"  - {a.avatar_id}: {a.name} ({a.description})")

    print()


async def test_background_manager():
    """测试背景管理器"""
    print("=== 测试背景管理器 ===")

    manager = get_background_manager()

    backgrounds = manager.list_backgrounds()
    print(f"背景列表 ({len(backgrounds)}个):")
    for bg in backgrounds:
        print(f"  - {bg['id']}: {bg['name']} ({bg.get('category', '')})")

    print()


async def test_local_renderer():
    """测试本地渲染器"""
    print("=== 测试本地渲染器 ===")

    renderer = LocalRenderer()

    health = await renderer.health_check()
    print(f"本地渲染环境:")
    print(f"  FFmpeg: {'OK' if health['ffmpeg'] else 'NOT FOUND'}")
    print(f"  Python: {'OK' if health['python'] else 'NOT FOUND'}")
    print(f"  可用模型: {health['models']}")

    # 模型要求
    print(f"\n模型要求:")
    for model in ["sadtalker", "wav2lip"]:
        req = renderer.get_model_requirements(model)
        print(f"  {model}: GPU推荐={req.get('gpu_recommended')}, 最低显存={req.get('min_gpu_memory')}")

    print()


async def test_digital_human_router():
    """测试数字人路由器"""
    print("=== 测试数字人路由器 ===")

    # 云端模式
    config = DigitalHumanConfig(
        mode=DigitalHumanMode.CLOUD,
        provider="aliyun",
        aliyun_api_key="test_key",
        aliyun_region="cn-shanghai"
    )

    router = DigitalHumanRouter(config)
    print(f"路由器初始化成功")
    print(f"  模式: {router.config.mode.value}")
    print(f"  供应商: {router.config.provider}")

    # 健康检查
    health = await router.health_check()
    print(f"  健康状态: {health}")

    # 形象和背景管理器
    print(f"  形象分类: {[c['name'] for c in router.avatar_manager.list_categories()]}")
    print(f"  背景数: {len(router.background_manager.list_backgrounds())}")

    await router.close()
    print()


async def test_local_mode():
    """测试本地模式"""
    print("=== 测试本地模式 ===")

    config = DigitalHumanConfig(
        mode=DigitalHumanMode.LOCAL,
        provider="aliyun"
    )

    router = DigitalHumanRouter(config)
    print(f"本地模式路由器初始化成功")

    health = await router.health_check()
    print(f"  健康状态: {health}")

    await router.close()
    print()


async def main():
    print("=" * 50)
    print("数字人模块测试")
    print("=" * 50)
    print()

    await test_avatar_manager()
    await test_background_manager()
    await test_local_renderer()
    await test_digital_human_router()
    await test_local_mode()

    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())