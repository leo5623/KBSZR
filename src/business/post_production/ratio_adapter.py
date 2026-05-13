"""横竖屏自适应"""
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

from loguru import logger


class VideoRatio(Enum):
    """视频比例"""
    PORTRAIT_9_16 = "9:16"      # 竖屏 9:16 (抖音/快手/小红书)
    LANDSCAPE_16_9 = "16:9"     # 横屏 16:9 (B站/西瓜)
    SQUARE_1_1 = "1:1"          # 方屏 1:1 (Instagram)
    LANDSCAPE_4_3 = "4:3"      # 横屏 4:3


@dataclass
class RatioAdaptConfig:
    """比例适配配置"""
    output_ratios: List[VideoRatio] = None  # 输出的比例列表
    default_primary: VideoRatio = VideoRatio.PORTRAIT_9_16
    auto_generate_all: bool = True  # 是否自动生成所有比例版本


# 各平台推荐比例
PLATFORM_RATIOS = {
    "douyin": VideoRatio.PORTRAIT_9_16,
    "kuaishou": VideoRatio.PORTRAIT_9_16,
    "xiaohongshu": VideoRatio.PORTRAIT_9_16,
    "weixin": VideoRatio.PORTRAIT_9_16,
    "bilibili": VideoRatio.LANDSCAPE_16_9,
    "weibo": VideoRatio.LANDSCAPE_16_9,
    "xg": VideoRatio.LANDSCAPE_16_9,
}


@dataclass
class RatioAdaptResult:
    """适配结果"""
    original_ratio: VideoRatio
    adapted_ratios: List[Tuple[VideoRatio, str]]  # (比例, 输出路径) 列表
    primary_path: str  # 主版本路径


@dataclass
class VideoCenterCrop:
    """中心裁剪配置"""
    ratio: VideoRatio
    focus_point_x: float = 0.5  # 焦点 X (0-1)
    focus_point_y: float = 0.5  # 焦点 Y (0-1)


class RatioAdapter:
    """
    横竖屏自适应适配器

    功能：
    1. 单一视频输出多比例版本
    2. 智能裁剪（保持主体在画面中心）
    3. 平台推荐比例
    """

    def __init__(self, config: Optional[RatioAdaptConfig] = None):
        self.config = config or RatioAdaptConfig(
            output_ratios=[
                VideoRatio.PORTRAIT_9_16,
                VideoRatio.LANDSCAPE_16_9,
                VideoRatio.SQUARE_1_1
            ],
            default_primary=VideoRatio.PORTRAIT_9_16
        )

    def get_recommended_ratio(self, platform: str) -> VideoRatio:
        """获取平台推荐比例"""
        return PLATFORM_RATIOS.get(platform, self.config.default_primary)

    def calculate_crop_params(
        self,
        source_width: int,
        source_height: int,
        target_ratio: VideoRatio
    ) -> Tuple[int, int, int, int]:
        """
        计算裁剪参数

        Args:
            source_width: 源视频宽度
            source_height: 源视频高度
            target_ratio: 目标比例

        Returns:
            (crop_x, crop_y, crop_width, crop_height)
        """
        source_ratio = source_width / source_height

        # 解析目标比例
        if target_ratio == VideoRatio.PORTRAIT_9_16:
            target_w_h = 9 / 16
        elif target_ratio == VideoRatio.LANDSCAPE_16_9:
            target_w_h = 16 / 9
        elif target_ratio == VideoRatio.SQUARE_1_1:
            target_w_h = 1.0
        elif target_ratio == VideoRatio.LANDSCAPE_4_3:
            target_w_h = 4 / 3
        else:
            target_w_h = 16 / 9

        # 计算裁剪区域
        if source_ratio > target_w_h:
            # 源视频更宽，需要裁剪宽度
            crop_height = source_height
            crop_width = int(source_height * target_w_h)
            crop_x = (source_width - crop_width) // 2
            crop_y = 0
        else:
            # 源视频更高，需要裁剪高度
            crop_width = source_width
            crop_height = int(source_width / target_w_h)
            crop_x = 0
            crop_y = (source_height - crop_height) // 2

        return crop_x, crop_y, crop_width, crop_height

    def generate_all_versions(
        self,
        video_path: str,
        output_dir: str,
        prefix: str = "output"
    ) -> RatioAdaptResult:
        """
        生成所有比例版本

        Args:
            video_path: 输入视频路径
            output_dir: 输出目录
            prefix: 输出文件前缀

        Returns:
            RatioAdaptResult: 适配结果
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        adapted = []

        for ratio in self.config.output_ratios:
            output_path = os.path.join(
                output_dir,
                f"{prefix}_{ratio.value.replace(':', 'x')}.mp4"
            )
            adapted.append((ratio, output_path))

        # 找主版本路径（通常是竖屏）
        primary_path = ""
        for ratio, path in adapted:
            if ratio == self.config.default_primary:
                primary_path = path
                break
        if not primary_path and adapted:
            primary_path = adapted[0][1]

        return RatioAdaptResult(
            original_ratio=self.config.default_primary,
            adapted_ratios=adapted,
            primary_path=primary_path
        )

    def get_scale_params(
        self,
        target_width: int,
        target_height: int,
        ratio: VideoRatio
    ) -> Tuple[int, int]:
        """
        获取缩放参数

        用于 FFmpeg 缩放到目标分辨率
        """
        if ratio == VideoRatio.PORTRAIT_9_16:
            return target_width, target_width * 16 // 9
        elif ratio == VideoRatio.LANDSCAPE_16_9:
            return target_height * 16 // 9, target_height
        elif ratio == VideoRatio.SQUARE_1_1:
            return target_width, target_width
        elif ratio == VideoRatio.LANDSCAPE_4_3:
            return target_height * 4 // 3, target_height
        return target_width, target_height

    def build_ffmpeg_crop_filter(
        self,
        source_width: int,
        source_height: int,
        target_ratio: VideoRatio,
        focus_x: float = 0.5,
        focus_y: float = 0.5
    ) -> str:
        """
        构建 FFmpeg 裁剪滤镜

        Args:
            source_width: 源宽度
            source_height: 源高度
            target_ratio: 目标比例
            focus_x: 焦点 X (0-1)
            focus_y: 焦点 Y (0-1)

        Returns:
            FFmpeg crop 滤镜字符串
        """
        crop_x, crop_y, crop_w, crop_h = self.calculate_crop_params(
            source_width, source_height, target_ratio
        )

        # 调整焦点
        if focus_x != 0.5 or focus_y != 0.5:
            offset_x = int((focus_x - 0.5) * (source_width - crop_w))
            offset_y = int((focus_y - 0.5) * (source_height - crop_h))
            crop_x = max(0, crop_x + offset_x)
            crop_y = max(0, crop_y + offset_y)

            # 确保裁剪区域不超出边界
            crop_x = min(crop_x, source_width - crop_w)
            crop_y = min(crop_y, source_height - crop_h)

        return f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"

    def get_placeholder_image(
        self,
        ratio: VideoRatio,
        text: str = ""
    ) -> str:
        """获取占位图（用于填充）"""
        # 返回渐变色占位图配置
        placeholders = {
            VideoRatio.PORTRAIT_9_16: {"width": 720, "height": 1280, "color": "#1a1a2e"},
            VideoRatio.LANDSCAPE_16_9: {"width": 1920, "height": 1080, "color": "#16213e"},
            VideoRatio.SQUARE_1_1: {"width": 1080, "height": 1080, "color": "#0f3460"},
        }

        config = placeholders.get(ratio, placeholders[VideoRatio.PORTRAIT_9_16])
        return f"color=c={config['color']}:s={config['width']}x{config['height']}:d=5"


# 全局实例
_adapter: Optional[RatioAdapter] = None


def get_ratio_adapter(config: Optional[RatioAdaptConfig] = None) -> RatioAdapter:
    """获取适配器实例"""
    global _adapter
    if _adapter is None or config is not None:
        _adapter = RatioAdapter(config)
    return _adapter