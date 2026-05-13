"""字幕样式预设"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from loguru import logger


class SubtitleStyle(Enum):
    """预设字幕样式"""
    DEFAULT = "default"           # 默认样式
    MOVIE = "movie"               # 电影字幕
    LIVE = "live"                 # 直播字幕
    MINIMAL = "minimal"           # 极简字幕
    CREATIVE = "creative"         # 创意字幕


@dataclass
class SubtitleStyleConfig:
    """字幕样式配置"""
    name: str
    font_family: str = "黑体"
    font_size: int = 24
    font_color: str = "#FFFFFF"       # 白色
    stroke_color: str = "#000000"     # 黑色描边
    stroke_width: float = 2.0        # 描边宽度
    background_color: str = ""        # 背景色（空=透明）
    background_opacity: float = 0.0   # 背景透明度
    position: str = "bottom"          # 位置: top / center / bottom
    alignment: str = "center"         # 对齐: left / center / right
    vertical_margin: int = 50         # 垂直边距
    max_chars_per_line: int = 20      # 每行最大字符数
    highlight_keywords: List[str] = field(default_factory=list)  # 高亮关键词


# 预设样式配置
PRESET_STYLES: dict[SubtitleStyle, SubtitleStyleConfig] = {
    SubtitleStyle.DEFAULT: SubtitleStyleConfig(
        name="默认样式",
        font_family="黑体",
        font_size=24,
        font_color="#FFFFFF",
        stroke_color="#000000",
        stroke_width=1.5,
        position="bottom",
        alignment="center",
        vertical_margin=50
    ),
    SubtitleStyle.MOVIE: SubtitleStyleConfig(
        name="电影字幕",
        font_family="微软雅黑",
        font_size=28,
        font_color="#FFFFFF",
        stroke_color="#000000",
        stroke_width=2.5,
        position="bottom",
        alignment="center",
        vertical_margin=60,
        max_chars_per_line=18
    ),
    SubtitleStyle.LIVE: SubtitleStyleConfig(
        name="直播字幕",
        font_family="黑体",
        font_size=32,
        font_color="#FFFF00",         # 黄色
        stroke_color="#FF0000",       # 红色描边
        stroke_width=3.0,
        position="top",
        alignment="center",
        vertical_margin=30,
        background_color="#000000",
        background_opacity=0.6
    ),
    SubtitleStyle.MINIMAL: SubtitleStyleConfig(
        name="极简字幕",
        font_family="苹方",
        font_size=20,
        font_color="#FFFFFF",
        stroke_color="",
        stroke_width=0,
        position="bottom",
        alignment="center",
        vertical_margin=40,
        max_chars_per_line=25
    ),
    SubtitleStyle.CREATIVE: SubtitleStyleConfig(
        name="创意字幕",
        font_family="华康楷体",
        font_size=26,
        font_color="#FF69B4",         # 粉色
        stroke_color="#FFFFFF",
        stroke_width=1.0,
        position="center",
        alignment="center",
        vertical_margin=0,
        highlight_keywords=["推荐", "种草", "必看"]
    ),
}


@dataclass
class SubtitleStyleManagerConfig:
    """字幕样式管理器配置"""
    default_style: SubtitleStyle = SubtitleStyle.DEFAULT
    custom_styles_path: str = "./config/subtitle_styles.json"


class SubtitleStyleManager:
    """
    字幕样式管理器

    功能：
    1. 管理预设样式
    2. 管理自定义样式
    3. 样式预览
    4. 导出样式配置
    """

    def __init__(self, config: Optional[SubtitleStyleManagerConfig] = None):
        self.config = config or SubtitleStyleManagerConfig()
        self._custom_styles: dict[str, SubtitleStyleConfig] = {}
        self._current_style = PRESET_STYLES[self.config.default_style]

    def get_style(self, style_name: str) -> SubtitleStyleConfig:
        """获取样式配置"""
        # 先检查预设
        for preset_style, config in PRESET_STYLES.items():
            if preset_style.value == style_name or config.name == style_name:
                return config

        # 再检查自定义
        if style_name in self._custom_styles:
            return self._custom_styles[style_name]

        # 返回默认
        return self._current_style

    def set_current_style(self, style: SubtitleStyle):
        """设置当前使用的样式"""
        if style in PRESET_STYLES:
            self._current_style = PRESET_STYLES[style]
            logger.info(f"字幕样式切换为: {self._current_style.name}")

    def list_preset_styles(self) -> List[dict]:
        """列出所有预设样式"""
        return [
            {
                "id": style.value,
                "name": config.name,
                "preview": f"字体:{config.font_family} {config.font_size}px"
            }
            for style, config in PRESET_STYLES.items()
        ]

    def add_custom_style(self, style_id: str, config: SubtitleStyleConfig) -> bool:
        """添加自定义样式"""
        if style_id in PRESET_STYLES:
            logger.warning(f"样式ID {style_id} 已存在（预设）")
            return False

        self._custom_styles[style_id] = config
        logger.info(f"添加自定义字幕样式: {config.name}")
        return True

    def remove_custom_style(self, style_id: str) -> bool:
        """移除自定义样式"""
        if style_id in self._custom_styles:
            del self._custom_styles[style_id]
            logger.info(f"移除自定义字幕样式: {style_id}")
            return True
        return False

    def export_style_config(self, style: SubtitleStyleConfig) -> dict:
        """
        导出样式配置

        返回可用于剪映/ffmpeg 等工具的配置格式
        """
        return {
            "font": style.font_family,
            "fontsize": style.font_size,
            "fontcolor": style.font_color,
            "strokecolor": style.stroke_color,
            "strokewidth": style.stroke_width,
            "bordercolor": style.stroke_color,
            "borderwidth": style.stroke_width,
            "margin": style.vertical_margin,
            "position": style.position,
            "alignment": style.alignment,
            "max_chars_per_line": style.max_chars_per_line
        }

    def get_style_for_platform(self, platform: str) -> SubtitleStyleConfig:
        """
        根据平台获取推荐的字幕样式

        Args:
            platform: 平台名称 (douyin/kuaishou/xiaohongshu)

        Returns:
            SubtitleStyleConfig
        """
        platform_styles = {
            "douyin": SubtitleStyle.DEFAULT,
            "kuaishou": SubtitleStyle.MINIMAL,
            "xiaohongshu": SubtitleStyle.CREATIVE,
            "weixin": SubtitleStyle.MOVIE
        }

        style = platform_styles.get(platform, SubtitleStyle.DEFAULT)
        return PRESET_STYLES[style]


# 全局实例
_style_manager: Optional[SubtitleStyleManager] = None


def get_subtitle_style_manager(
    config: Optional[SubtitleStyleManagerConfig] = None
) -> SubtitleStyleManager:
    """获取字幕样式管理器"""
    global _style_manager
    if _style_manager is None or config is not None:
        _style_manager = SubtitleStyleManager(config)
    return _style_manager