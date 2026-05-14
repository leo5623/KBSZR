"""Cyberpunk主题 - 颜色常量、样式和工具函数"""
import os
import re
from typing import Optional, Dict

# 配置文件路径
_THEME_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "theme.txt")

# 缓存最后修改时间
_last_config_mtime = 0


def _parse_color_value(value: str) -> str:
    """解析颜色值，去除空格和#号"""
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    return value.upper()


def load_colors_from_config() -> Dict[str, str]:
    """从配置文件加载颜色"""
    global _last_config_mtime
    config_path = _THEME_CONFIG_PATH

    if not os.path.exists(config_path):
        return {}

    try:
        current_mtime = os.path.getmtime(config_path)
        if current_mtime == _last_config_mtime:
            return {}  # 没有变化，不重新加载

        _last_config_mtime = current_mtime

        colors = {}
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    colors[key.strip()] = _parse_color_value(value.strip())

        return colors
    except Exception:
        return {}


def reload_theme_if_changed():
    """检查并重新加载主题（如果配置文件已更改）"""
    new_colors = load_colors_from_config()
    if new_colors:
        COLORS.update(new_colors)
        return True
    return False


# 主色调
COLORS = {
    # 背景色 - 浅色主题
    "BACKGROUND": "#F5F5F7",      # 主窗口背景 - 浅灰白
    "SURFACE": "#FFFFFF",        # 卡片/面板背景 - 纯白
    "CARD": "#F0F0F3",           # 提升的卡片表面
    "CARD_HOVER": "#E8E8EC",      # 卡片hover状态

    # 霓虹色 - 深色对比
    "PRIMARY_NEON": "#00A0A0",    # 青色霓虹（主色）- 深青色更易读
    "PRIMARY_GLOW": "rgba(0, 160, 160, 0.4)",
    "SECONDARY_NEON": "#CC00CC",   # 品红霓虹（次色）
    "SECONDARY_GLOW": "rgba(204, 0, 204, 0.4)",
    "ACCENT": "#0066CC",          # 电蓝色点缀
    "ACCENT_GLOW": "rgba(0, 102, 204, 0.4)",

    # 文字色 - 深色对比
    "TEXT_PRIMARY": "#1A1A1A",    # 主文字 - 深黑
    "TEXT_SECONDARY": "#4A4A5A",  # 次级文字 - 深灰
    "TEXT_MUTED": "#7A7A8A",       # 暗淡文字

    # 状态色
    "SUCCESS": "#00A050",         # 深绿色
    "WARNING": "#CC7700",        # 深橙色
    "ERROR": "#CC2244",          # 深红色

    # 边框
    "BORDER": "#D0D0D8",          # 浅色边框
    "BORDER_HOVER": "#B0B0C0",    # hover边框
}

# 尝试从配置文件加载
_initial_colors = load_colors_from_config()
if _initial_colors:
    COLORS.update(_initial_colors)


def get_neon_glow(color: str, intensity: float = 0.5) -> str:
    """获取霓虹发光效果字符串"""
    if color == "cyan":
        return f"0 0 8px rgba(0, 160, 160, {intensity}), 0 0 16px rgba(0, 160, 160, {intensity * 0.4})"
    elif color == "magenta":
        return f"0 0 8px rgba(204, 0, 204, {intensity}), 0 0 16px rgba(204, 0, 204, {intensity * 0.4})"
    elif color == "blue":
        return f"0 0 8px rgba(0, 102, 204, {intensity}), 0 0 16px rgba(0, 102, 204, {intensity * 0.4})"
    return ""


def get_card_qss(hover: bool = False, neon_color: str = "cyan") -> str:
    """获取卡片QSS样式"""
    glow = get_neon_glow(neon_color, 0.25) if hover else ""
    border_color = COLORS["PRIMARY_NEON"] if neon_color == "cyan" else COLORS["SECONDARY_NEON"]
    border = f"border: 2px solid {border_color};" if hover else ""

    return f"""
        QFrame {{
            background-color: {COLORS['CARD']};
            border-radius: 8px;
            border: 1px solid {COLORS['BORDER']};
        }}
        QFrame:hover {{
            background-color: {COLORS['CARD_HOVER']};
            {border}
            box-shadow: {glow};
        }}
    """


def get_button_qss(variant: str = "primary") -> str:
    """获取按钮QSS样式"""
    if variant == "primary":
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                box-shadow: {get_neon_glow('cyan', 0.5)};
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #008888, stop:1 #005599);
            }}
            QPushButton:disabled {{
                background: {COLORS['SURFACE']};
                color: {COLORS['TEXT_MUTED']};
            }}
        """
    elif variant == "secondary":
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['PRIMARY_NEON']};
                border: 2px solid {COLORS['PRIMARY_NEON']};
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 160, 160, 0.1);
                box-shadow: {get_neon_glow('cyan', 0.3)};
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 160, 160, 0.2);
            }}
        """
    elif variant == "ghost":
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['TEXT_SECONDARY']};
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {COLORS['PRIMARY_NEON']};
                background-color: {COLORS['CARD']};
            }}
        """
    return ""


def get_input_qss() -> str:
    """获取输入框QSS样式"""
    return f"""
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {COLORS['SURFACE']};
            color: {COLORS['TEXT_PRIMARY']};
            border: 1px solid {COLORS['BORDER']};
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 14px;
            selection-background-color: {COLORS['PRIMARY_NEON']};
            selection-color: #FFFFFF;
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {COLORS['PRIMARY_NEON']};
            background-color: {COLORS['SURFACE']};
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {COLORS['CARD']};
            color: {COLORS['TEXT_MUTED']};
        }}
        QComboBox {{
            padding-right: 30px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {COLORS['TEXT_SECONDARY']};
            margin-right: 10px;
        }}
    """


def get_scrollbar_qss() -> str:
    """获取滚动条QSS样式"""
    return f"""
        QScrollBar:vertical {{
            background-color: {COLORS['CARD']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['BORDER']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['PRIMARY_NEON']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {COLORS['CARD']};
            height: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {COLORS['BORDER']};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['PRIMARY_NEON']};
        }}
    """


def get_window_qss() -> str:
    """获取主窗口QSS样式"""
    return f"""
        QMainWindow, QWidget {{
            background-color: {COLORS['BACKGROUND']};
            color: {COLORS['TEXT_PRIMARY']};
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        }}
        QLabel, QTextEdit, QLineEdit, QComboBox {{
            color: {COLORS['TEXT_PRIMARY']};
            background-color: transparent;
        }}
        QMessageBox {{
            background-color: {COLORS['SURFACE']};
        }}
        QMessageBox QLabel {{
            color: {COLORS['TEXT_PRIMARY']};
            background-color: transparent;
        }}
        {get_scrollbar_qss()}
    """


def get_nav_item_qss(selected: bool = False) -> str:
    """获取导航项QSS样式"""
    if selected:
        return f"""
            QPushButton {{
                background-color: rgba(0, 160, 160, 0.15);
                color: {COLORS['PRIMARY_NEON']};
                border: none;
                border-left: 3px solid {COLORS['PRIMARY_NEON']};
                padding: 12px 0px 12px 17px;
                text-align: left;
                font-size: 13px;
            }}
        """
    return f"""
        QPushButton {{
            background-color: {COLORS['SURFACE']};
            color: {COLORS['TEXT_SECONDARY']};
            border: none;
            border-left: 3px solid transparent;
            padding: 12px 0px 12px 17px;
            text-align: left;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['CARD']};
            color: {COLORS['PRIMARY_NEON']};
        }}
    """


def get_slider_qss() -> str:
    """获取滑块QSS样式"""
    return f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 4px;
            background: {COLORS['BORDER']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {COLORS['PRIMARY_NEON']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            box-shadow: {get_neon_glow('cyan', 0.6)};
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['PRIMARY_NEON']}, stop:1 {COLORS['ACCENT']});
            border-radius: 2px;
        }}
    """