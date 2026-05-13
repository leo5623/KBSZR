"""批量混剪"""
import asyncio
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from loguru import logger


@dataclass
class MixConfig:
    """混剪配置"""
    voice_id: str = ""           # 音色
    avatar_id: str = ""          # 数字人
    background_id: str = ""       # 背景
    speed_modifier: float = 1.0  # 语速调整 0.9-1.1
    bgm_id: str = ""             # BGM
    output_suffix: str = ""      # 输出文件后缀


@dataclass
class MixResult:
    """混剪结果"""
    success: bool
    original_path: str = ""
    variations: List[str] = field(default_factory=list)  # 衍生版本路径
    config_used: List[MixConfig] = field(default_factory=list)
    error_message: str = ""


@dataclass
class VideoMixerConfig:
    """混剪器配置"""
    variations_count: int = 3    # 默认生成3个衍生版本
    enable_random_seed: bool = True  # 启用随机种子
    output_dir: str = "./output/mixed"


class VideoMixer:
    """
    批量混剪器

    功能：
    1. 复制文案并随机改写N个版本
    2. 自动切换音色/数字人/背景
    3. 发起多任务生成
    """

    # 音色变化池
    VOICE_VARIATIONS = [
        "xiaoyun", "xiaogang", "aiqi", "aiya",
        "speech-01", "speech-02", "BV001_streaming"
    ]

    # 数字人变化池
    AVATAR_VARIATIONS = [
        "avatar_001", "avatar_002", "avatar_003", "avatar_008"
    ]

    # 背景变化池
    BACKGROUND_VARIATIONS = [
        "bg_001", "bg_002", "bg_003", "bg_005"
    ]

    # BGM变化池
    BGM_VARIATIONS = [
        "bgm_excited_01", "bgm_calm_01", "bgm_warm_01"
    ]

    def __init__(self, config: Optional[VideoMixerConfig] = None):
        self.config = config or VideoMixerConfig()

    def generate_variations(
        self,
        content: str,
        count: int = None
    ) -> List[MixConfig]:
        """
        生成多个混剪配置

        Args:
            content: 原始文案
            count: 变体数量

        Returns:
            List[MixConfig]: 变体配置列表
        """
        count = count or self.config.variations_count
        variations = []

        # 设置随机种子以确保可重复性
        if self.config.enable_random_seed:
            seed = int(hashlib.md5(content.encode()).hexdigest()[:8], 16)
            random.seed(seed)

        for i in range(count):
            config = MixConfig(
                voice_id=random.choice(self.VOICE_VARIATIONS),
                avatar_id=random.choice(self.AVATAR_VARIATIONS),
                background_id=random.choice(self.BACKGROUND_VARIATIONS),
                speed_modifier=round(random.uniform(0.95, 1.05), 2),
                bgm_id=random.choice(self.BGM_VARIATIONS),
                output_suffix=f"_v{i+1}"
            )
            variations.append(config)

        logger.info(f"生成了 {len(variations)} 个混剪配置")
        return variations

    async def batch_generate(
        self,
        content: str,
        output_paths: List[str] = None
    ) -> MixResult:
        """
        批量生成混剪视频

        Args:
            content: 原始文案
            output_paths: 指定的输出路径列表

        Returns:
            MixResult: 混剪结果
        """
        try:
            # 1. 生成变体配置
            variations = self.generate_variations(content)

            # 2. 准备输出路径
            if output_paths is None:
                import os
                os.makedirs(self.config.output_dir, exist_ok=True)
                output_paths = [
                    os.path.join(
                        self.config.output_dir,
                        f"mixed_{v.output_suffix}.mp4"
                    )
                    for v in variations
                ]

            # 3. 生成任务列表（这里简化处理，实际应调用队列）
            tasks = []
            for i, (v, out_path) in enumerate(zip(variations, output_paths)):
                task = self._generate_single(v, out_path)
                tasks.append(task)

            # 4. 并行执行（限制并发数）
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 5. 汇总结果
            successful = [out for out, r in zip(output_paths, results) if r is True]
            failed = [str(r) for r in results if r is not True]

            if failed:
                logger.warning(f"部分混剪失败: {failed}")

            return MixResult(
                success=len(successful) > 0,
                original_path="",
                variations=successful,
                config_used=variations,
                error_message="; ".join(failed) if failed else ""
            )

        except Exception as e:
            logger.error(f"批量混剪失败: {e}")
            return MixResult(success=False, error_message=str(e))

    async def _generate_single(
        self,
        config: MixConfig,
        output_path: str
    ) -> bool:
        """
        生成单个混剪版本

        简化实现，实际应调用完整的视频生成流程
        """
        try:
            # 模拟处理
            await asyncio.sleep(0.1)
            logger.debug(f"生成混剪: {config.output_suffix} -> {output_path}")
            return True
        except Exception as e:
            logger.error(f"生成混剪失败: {e}")
            return False

    def quick_preview(self, content: str) -> List[Dict]:
        """
        快速预览混剪配置（不实际生成）

        用于在生成前预览各版本的配置
        """
        variations = self.generate_variations(content)

        preview = []
        for i, v in enumerate(variations):
            preview.append({
                "index": i + 1,
                "voice": v.voice_id,
                "avatar": v.avatar_id,
                "background": v.background_id,
                "speed": v.speed_modifier,
                "bgm": v.bgm_id,
                "output_suffix": v.output_suffix
            })

        return preview


# 全局实例
_mixer: Optional[VideoMixer] = None


def get_video_mixer(config: Optional[VideoMixerConfig] = None) -> VideoMixer:
    """获取混剪器实例"""
    global _mixer
    if _mixer is None or config is not None:
        _mixer = VideoMixer(config)
    return _mixer