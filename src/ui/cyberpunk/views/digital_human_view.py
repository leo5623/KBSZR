"""数字人视图 - 数字人选择+预览"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QGridLayout, QScrollArea,
    QSlider, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..theme import COLORS, get_card_qss, get_input_qss, get_slider_qss, get_neon_glow
from ..widgets import CyberCard, NeonButton


class DigitalHumanView(QWidget):
    """
    数字人配置视图
    左侧：数字人选择网格
    右侧：预览面板+背景选择+参数设置
    """

    avatar_selected = pyqtSignal(str)  # 数字人ID
    background_selected = pyqtSignal(str)  # 背景ID
    generate_requested = pyqtSignal(dict)  # 生成请求

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_avatar = None
        self._selected_background = "bg_001"
        self._init_ui()
        self._load_avatars()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 左侧：数字人选择区
        left_panel = self._create_avatar_panel()
        main_layout.addWidget(left_panel, 2)

        # 右侧：预览+参数区
        right_panel = self._create_preview_panel()
        main_layout.addWidget(right_panel, 1)

    def _create_avatar_panel(self) -> QFrame:
        """创建数字人选择面板"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title = QLabel("👤 选择数字人")
        title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        # 分类筛选
        filter_layout = QHBoxLayout()
        filter_label = QLabel("分类:")
        filter_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")

        self._category_combo = QComboBox()
        self._category_combo.addItems(["全部", "女生", "男生", "民族风", "健身", "商务", "综合"])
        self._category_combo.setStyleSheet(get_input_qss())
        self._category_combo.currentTextChanged.connect(self._on_category_changed)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self._category_combo)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # 数字人网格（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.Box)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        self._avatar_grid = QWidget()
        self._avatar_grid_layout = QGridLayout(self._avatar_grid)
        self._avatar_grid_layout.setSpacing(12)
        self._avatar_grid_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self._avatar_grid)
        layout.addWidget(scroll)

        return frame

    def _create_preview_panel(self) -> QFrame:
        """创建预览面板"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['SURFACE']};
                border-radius: 12px;
                border: 1px solid {COLORS['BORDER']};
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title = QLabel("🎬 预览与参数")
        title.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 16px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        # 预览区域
        preview_label = QLabel("数字人预览")
        preview_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")
        layout.addWidget(preview_label)

        self._preview_frame = QFrame()
        self._preview_frame.setFixedHeight(280)
        self._preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['CARD']};
                border-radius: 8px;
                border: 1px dashed {COLORS['BORDER']};
            }}
        """)
        preview_layout = QVBoxLayout(self._preview_frame)

        self._preview_placeholder = QLabel("👤\n\n选择数字人后\n在此预览")
        self._preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_placeholder.setStyleSheet(f"""
            color: {COLORS['TEXT_MUTED']};
            font-size: 14px;
        """)
        preview_layout.addWidget(self._preview_placeholder)

        self._avatar_name_label = QLabel("")
        self._avatar_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_name_label.setStyleSheet(f"""
            color: {COLORS['PRIMARY_NEON']};
            font-size: 14px;
            font-weight: 600;
        """)
        self._avatar_name_label.hide()
        preview_layout.addWidget(self._avatar_name_label)

        layout.addWidget(self._preview_frame)

        # 背景选择
        bg_label = QLabel("背景")
        bg_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")
        layout.addWidget(bg_label)

        self._background_list = QListWidget()
        self._background_list.setFlow(QListWidget.Flow.LeftToRight)
        self._background_list.setIconSize(80, 45)
        self._background_list.currentRowChanged.connect(self._on_background_changed)

        backgrounds = [
            ("bg_001", "演播室"),
            ("bg_002", "办公室"),
            ("bg_003", "客厅"),
            ("bg_004", "户外"),
            ("bg_005", "商品展示"),
            ("bg_006", "抽象背景"),
        ]

        for bg_id, bg_name in backgrounds:
            item = QListWidgetItem(bg_name)
            item.setData(Qt.ItemDataRole.UserRole, bg_id)
            self._background_list.addItem(item)

        self._background_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['CARD']};
                border: 1px solid {COLORS['BORDER']};
                border-radius: 6px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 4px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(0, 255, 255, 0.2);
                border: 1px solid {COLORS['PRIMARY_NEON']};
            }}
        """)
        layout.addWidget(self._background_list)

        # 参数设置
        params_label = QLabel("参数设置")
        params_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")
        layout.addWidget(params_label)

        # 运动模式
        motion_layout = QHBoxLayout()
        motion_label = QLabel("运动:")
        motion_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")

        self._motion_combo = QComboBox()
        self._motion_combo.addItems(["无", "轻微", "中等"])
        self._motion_combo.setStyleSheet(get_input_qss())

        motion_layout.addWidget(motion_label)
        motion_layout.addWidget(self._motion_combo)
        motion_layout.addStretch()

        layout.addLayout(motion_layout)

        # 比例选择
        ratio_layout = QHBoxLayout()
        ratio_label = QLabel("比例:")
        ratio_label.setStyleSheet(f"color: {COLORS['TEXT_SECONDARY']}; font-size: 13px;")

        self._ratio_combo = QComboBox()
        self._ratio_combo.addItems(["9:16 (竖屏)", "16:9 (横屏)"])
        self._ratio_combo.setStyleSheet(get_input_qss())

        ratio_layout.addWidget(ratio_label)
        ratio_layout.addWidget(self._ratio_combo)
        ratio_layout.addStretch()

        layout.addLayout(ratio_layout)

        # 生成按钮
        layout.addStretch()

        self._generate_btn = NeonButton("🎬 生成视频", variant="primary")
        self._generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self._generate_btn)

        return frame

    def _load_avatars(self):
        """加载数字人列表"""
        # 数字人数据（来自 aliyun_client.py）
        avatars = [
            {"id": "avatar_001", "name": "小美", "category": "女生"},
            {"id": "avatar_002", "name": "小雅", "category": "女生"},
            {"id": "avatar_003", "name": "小帅", "category": "男生"},
            {"id": "avatar_004", "name": "老王", "category": "男生"},
            {"id": "avatar_005", "name": "阿娜", "category": "民族风"},
            {"id": "avatar_006", "name": "健身教练", "category": "健身"},
            {"id": "avatar_007", "name": "商务精英", "category": "商务"},
            {"id": "avatar_008", "name": "主播小雪", "category": "综合"},
        ]

        self._avatars = avatars
        self._populate_avatar_grid(avatars)

    def _populate_avatar_grid(self, avatars):
        """填充数字人网格"""
        # 清除现有项
        while self._avatar_grid_layout.count():
            item = self._avatar_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加数字人卡片
        for i, avatar in enumerate(avatars):
            row = i // 2
            col = i % 2

            card = self._create_avatar_card(avatar)
            self._avatar_grid_layout.addWidget(card, row, col)

    def _create_avatar_card(self, avatar: dict) -> QFrame:
        """创建数字人卡片"""
        card = QFrame()
        card.setFixedHeight(100)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['CARD']};
                border-radius: 8px;
                border: 1px solid {COLORS['BORDER']};
            }}
            QFrame:hover {{
                border: 1px solid {COLORS['PRIMARY_NEON']};
            }}
        """)
        card.setData = avatar  # 存储数据
        card.mousePressEvent = lambda e, a=avatar: self._on_avatar_clicked(a)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)

        # 头像占位符
        avatar_label = QLabel("👤")
        avatar_label.setFixedSize(60, 60)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet(f"""
            background-color: {COLORS['SURFACE']};
            border-radius: 30px;
            font-size: 28px;
        """)

        # 信息
        info_layout = QVBoxLayout()

        name_label = QLabel(avatar["name"])
        name_label.setStyleSheet(f"""
            color: {COLORS['TEXT_PRIMARY']};
            font-size: 14px;
            font-weight: 600;
        """)

        category_label = QLabel(avatar["category"])
        category_label.setStyleSheet(f"""
            color: {COLORS['TEXT_SECONDARY']};
            font-size: 12px;
        """)

        info_layout.addWidget(name_label)
        info_layout.addWidget(category_label)
        info_layout.addStretch()

        layout.addWidget(avatar_label)
        layout.addLayout(info_layout, 1)

        return card

    def _on_avatar_clicked(self, avatar: dict):
        """数字人卡片点击"""
        self._selected_avatar = avatar["id"]

        # 更新预览
        self._preview_placeholder.hide()
        self._avatar_name_label.setText(avatar["name"])
        self._avatar_name_label.show()

        # 发送信号
        self.avatar_selected.emit(avatar["id"])

    def _on_background_changed(self, index: int):
        """背景选择变化"""
        item = self._background_list.item(index)
        if item:
            self._selected_background = item.data(Qt.ItemDataRole.UserRole)
            self.background_selected.emit(self._selected_background)

    def _on_category_changed(self, category: str):
        """分类筛选变化"""
        if category == "全部":
            filtered = self._avatars
        else:
            filtered = [a for a in self._avatars if a["category"] == category]

        self._populate_avatar_grid(filtered)

    def _on_generate_clicked(self):
        """生成按钮点击"""
        if not self._selected_avatar:
            # TODO: 显示提示
            return

        self.generate_requested.emit({
            "avatar_id": self._selected_avatar,
            "background_id": self._selected_background,
            "motion": self._motion_combo.currentText(),
            "aspect_ratio": "9:16" if "竖屏" in self._ratio_combo.currentText() else "16:9"
        })