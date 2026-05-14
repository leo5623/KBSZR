"""时间线视图 - 视频剪辑时间轴"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSlider, QToolButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
from ..theme import COLORS, get_neon_glow
from ..widgets import NeonButton


class TimelineRuler(QWidget):
    """时间标尺"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self._zoom = 1.0
        self._duration = 60  # 60秒

    def setDuration(self, seconds: float):
        """设置时长"""
        self._duration = seconds
        self.update()

    def setZoom(self, zoom: float):
        """设置缩放"""
        self._zoom = zoom
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 背景
        painter.fillRect(0, 0, width, height, QColor(COLORS["CARD"]))

        # 刻度
        painter.setPen(QColor(COLORS["TEXT_SECONDARY"]))

        # 根据缩放计算刻度间隔
        if self._zoom < 0.5:
            interval = 10  # 10秒
        elif self._zoom < 1.5:
            interval = 5   # 5秒
        else:
            interval = 1  # 1秒

        pixels_per_second = 50 * self._zoom

        for sec in range(0, int(self._duration) + 1, interval):
            x = int(sec * pixels_per_second)

            # 主刻度
            painter.drawLine(x, height - 10, x, height)

            # 时间标签
            time_text = f"{sec}s"
            painter.drawText(x + 2, height - 15, time_text)

            # 细分刻度
            if interval >= 5:
                for sub_sec in range(1, interval):
                    sub_x = int((sec + sub_sec) * pixels_per_second)
                    painter.drawLine(sub_x, height - 5, sub_x, height)


class TimelineTrack(QFrame):
    """时间线轨道"""

    def __init__(self, name: str, color: str, parent=None):
        super().__init__(parent)
        self._name = name
        self._color = color
        self._clips = []

        self.setFixedHeight(50)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 4px;
                border-left: 3px solid {color};
            }}
        """)

    def addClip(self, start: float, duration: float, label: str):
        """添加片段"""
        clip = {
            "start": start,
            "duration": duration,
            "label": label
        }
        self._clips.append(clip)
        self.update()


class TimelineView(QWidget):
    """
    时间线视图
    视频剪辑时间轴：工具栏+时间标尺+脚本/音频/视频轨道
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 工具栏
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        # 时间线容器
        timeline_container = QFrame()
        timeline_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['CARD']};
                border-radius: 8px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(0)

        # 时间标尺
        self._ruler = TimelineRuler()
        timeline_layout.addWidget(self._ruler)

        # 轨道区域（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(180)
        scroll.setFrameShape(QFrame.Shape.Box)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        tracks_widget = QWidget()
        tracks_layout = QVBoxLayout(tracks_widget)
        tracks_layout.setSpacing(8)
        tracks_layout.setContentsMargins(16, 16, 16, 16)

        # 创建轨道
        self._script_track = TimelineTrack("📝 脚本", COLORS["PRIMARY_NEON"])
        self._audio_track = TimelineTrack("🎵 音频", COLORS["SECONDARY_NEON"])
        self._video_track = TimelineTrack("🎬 视频", COLORS["ACCENT"])

        tracks_layout.addWidget(self._script_track)
        tracks_layout.addWidget(self._audio_track)
        tracks_layout.addWidget(self._video_track)

        scroll.setWidget(tracks_widget)
        timeline_layout.addWidget(scroll)

        main_layout.addWidget(timeline_container)

        # 播放控制栏
        controls = self._create_controls()
        main_layout.addWidget(controls)

    def _create_toolbar(self) -> QFrame:
        """创建工具栏"""
        frame = QFrame()
        frame.setFixedHeight(50)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)

        # 缩放控制
        zoom_label = QLabel("缩放:")
        zoom_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setMinimum(10)
        self._zoom_slider.setMaximum(30)
        self._zoom_slider.setValue(20)
        self._zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._zoom_slider.setTickInterval(5)
        self._zoom_slider.setFixedWidth(150)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)

        from ..theme import get_slider_qss
        self._zoom_slider.setStyleSheet(get_slider_qss())

        layout.addWidget(zoom_label)
        layout.addWidget(self._zoom_slider)

        layout.addStretch()

        # 操作按钮
        add_btn = NeonButton("➕ 添加片段", variant="ghost")
        split_btn = NeonButton("✂️ 分割", variant="ghost")
        delete_btn = NeonButton("🗑️ 删除", variant="ghost")
        export_btn = NeonButton("📤 导出", variant="primary")

        layout.addWidget(add_btn)
        layout.addWidget(split_btn)
        layout.addWidget(delete_btn)
        layout.addWidget(export_btn)

        return frame

    def _create_controls(self) -> QFrame:
        """创建播放控制栏"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)

        # 播放按钮
        play_btn = NeonButton("▶️ 播放", variant="secondary")

        # 时间显示
        self._time_label = QLabel("00:00 / 01:00")
        self._time_label.setStyleSheet(f"""
            color: {COLORS['PRIMARY_NEON']};
            font-size: 16px;
            font-weight: 600;
            font-family: monospace;
        """)

        layout.addWidget(play_btn)
        layout.addStretch()
        layout.addWidget(self._time_label)
        layout.addStretch()

        # 快捷操作
        preview_btn = NeonButton("👁️ 预览", variant="ghost")
        layout.addWidget(preview_btn)

        return frame

    def _on_zoom_changed(self, value: int):
        """缩放变化"""
        zoom = value / 20.0
        self._ruler.setZoom(zoom)

    def setDuration(self, seconds: float):
        """设置视频时长"""
        self._ruler.setDuration(seconds)
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        self._time_label.setText(f"00:00 / {minutes:02d}:{secs:02d}")