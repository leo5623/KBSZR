"""本地处理模块测试"""
import asyncio
import sys
sys.path.insert(0, "D:/小程序代码/KBSZR")

from src.services.ffmpeg_service import FFmpegService
from src.business.post_production.subtitle.local_subtitle import SubtitleGenerator
from src.business.post_production.video_composer.local_composer import VideoComposer
from src.business.post_production.router import VideoProcessingRouter


async def test_ffmpeg_service():
    """测试FFmpeg服务"""
    print("=== 测试FFmpeg服务 ===")

    ffmpeg = FFmpegService()

    health = await ffmpeg.health_check()
    print(f"FFmpeg状态:")
    print(f"  可用: {health['available']}")
    if health['available']:
        print(f"  版本: {health.get('version', 'unknown')}")
    else:
        print(f"  错误: {health.get('error', 'unknown')}")

    print()


async def test_subtitle_generator():
    """测试字幕生成器"""
    print("=== 测试字幕生成器 ===")

    generator = SubtitleGenerator(model_size="base")

    health = await generator.health_check()
    print(f"Whisper状态:")
    print(f"  可用: {health['whisper_available']}")
    print(f"  模型已加载: {health['model_loaded']}")
    print(f"  模型大小: {health['model_size']}")
    print(f"  设备: {health['device']}")
    print(f"  FFmpeg: {health['ffmpeg_available']}")

    # 模型信息
    print(f"\n可用模型:")
    for model in generator.list_available_models():
        info = generator.get_model_info(model)
        print(f"  {model}: {info.get('params', '')} - {info.get('speed', '')}")

    print()


async def test_video_composer():
    """测试视频合成器"""
    print("=== 测试视频合成器 ===")

    composer = VideoComposer()
    print(f"VideoComposer初始化成功")

    print()


async def test_video_processing_router():
    """测试视频处理路由"""
    print("=== 测试视频处理路由 ===")

    router = VideoProcessingRouter()

    health = await router.health_check()
    print(f"视频处理路由状态:")
    print(f"  模式: {health['mode']}")
    print(f"  FFmpeg可用: {health['ffmpeg']['available']}")
    print(f"  Whisper可用: {health['whisper']['whisper_available']}")

    await router.close()
    print()


async def test_ffmpeg_functions():
    """测试FFmpeg各功能"""
    print("=== 测试FFmpeg功能 ===")

    ffmpeg = FFmpegService()

    # 检查FFmpeg是否可用
    health = await ffmpeg.health_check()
    if not health['available']:
        print("FFmpeg不可用，跳过功能测试")
        print()
        return

    print("FFmpeg功能列表:")
    print("  - merge_audio_video: 合并音视频")
    print("  - add_subtitle: 添加字幕")
    print("  - convert_ratio: 转换比例(9:16/16:9)")
    print("  - adjust_volume: 调整音量")
    print("  - adjust_speed: 调整语速")
    print("  - mix_bgm: 混音BGM")
    print("  - denoise: 降噪")
    print()


async def main():
    print("=" * 50)
    print("本地处理模块测试")
    print("=" * 50)
    print()

    await test_ffmpeg_service()
    await test_subtitle_generator()
    await test_video_composer()
    await test_video_processing_router()
    await test_ffmpeg_functions()

    print("=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())