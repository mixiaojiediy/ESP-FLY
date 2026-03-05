"""
MainView - 主窗口
组合所有子View，管理整体布局
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTabWidget,
    QPushButton,
    QMessageBox,
    QStackedWidget,
    QRadioButton,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon

from common.resource_path import resource_path
from .status_view import StatusView
from .control_view import ControlView
from .pid_view import PidView
from .motor_test_view import MotorTestView
from .terminal_view import TerminalView
from .waveform_view import WaveformView
from .attitude_3d_view import Attitude3DView


class MainView(QMainWindow):
    """
    主窗口View

    组合所有子View，提供：
    - 左侧：3D姿态显示 + 波形显示
    - 右侧：Tab页签（状态/控制/电机测试/PID/终端）
    - 连接/断开按钮
    """

    # 用户操作信号
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        # 子View引用
        self.status_view = None
        self.control_view = None
        self.pid_view = None
        self.motor_test_view = None
        self.terminal_view = None
        self.waveform_view = None
        self.attitude_3d_view = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("ESP-FLY 上位机调试系统 v2.0")
        
        # 设置窗口图标
        icon_path = resource_path("resources/icons/window_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 默认窗口大小，可以从配置读取
        self.resize(1280, 800)

        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：可视化区域
        left_widget = self._create_visualization_area()
        main_splitter.addWidget(left_widget)

        # 右侧：控制和状态面板
        right_widget = self._create_control_area()
        main_splitter.addWidget(right_widget)

        # 设置右侧面板最小宽度，允许用户调整大小
        right_widget.setMinimumWidth(250)

        main_layout.addWidget(main_splitter)

        # 保存分割器引用，以便后续可能需要调整
        self.main_splitter = main_splitter

    def _create_visualization_area(self) -> QWidget:
        """创建可视化区域 - 3D视图和波形面板切换显示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 顶部：视图切换按钮
        button_layout = QHBoxLayout()

        self.view_3d_btn = QRadioButton("3D姿态视图")
        self.view_waveform_btn = QRadioButton("波形面板")
        self.view_3d_btn.setChecked(True)  # 默认显示3D视图

        button_layout.addWidget(self.view_3d_btn)
        button_layout.addWidget(self.view_waveform_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 创建一个GroupBox包裹视图，使其边框样式与右侧面板一致
        view_group = QGroupBox()
        view_group_layout = QVBoxLayout(view_group)
        view_group_layout.setContentsMargins(0, 0, 0, 0)

        # 创建堆叠窗口部件用于切换视图
        self.view_stack = QStackedWidget()

        # 3D姿态视图
        self.attitude_3d_view = Attitude3DView()
        self.view_stack.addWidget(self.attitude_3d_view)

        # 波形显示面板
        self.waveform_view = WaveformView()
        self.view_stack.addWidget(self.waveform_view)

        view_group_layout.addWidget(self.view_stack)
        layout.addWidget(view_group)

        # 连接切换信号
        self.view_3d_btn.toggled.connect(
            lambda checked: self.view_stack.setCurrentIndex(0) if checked else None
        )
        self.view_waveform_btn.toggled.connect(
            lambda checked: self.view_stack.setCurrentIndex(1) if checked else None
        )

        return widget

    def _create_control_area(self) -> QWidget:
        """创建控制区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab控件
        tab_widget = QTabWidget()

        # 状态面板
        self.status_view = StatusView()
        tab_widget.addTab(self.status_view, "状态信息")

        # 控制面板
        self.control_view = ControlView()
        tab_widget.addTab(self.control_view, "飞行控制")

        # 电机测试面板
        self.motor_test_view = MotorTestView()
        tab_widget.addTab(self.motor_test_view, "电机测试")

        # PID调参面板
        self.pid_view = PidView()
        tab_widget.addTab(self.pid_view, "PID调参")

        # 终端监控
        self.terminal_view = TerminalView()
        tab_widget.addTab(self.terminal_view, "终端监控")

        layout.addWidget(tab_widget)

        # 连接按钮
        connect_layout = QHBoxLayout()
        self._connect_btn = QPushButton("连接无人机")
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        connect_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("断开连接")
        self._disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self._disconnect_btn.setEnabled(False)
        connect_layout.addWidget(self._disconnect_btn)

        layout.addLayout(connect_layout)

        return widget

    def _on_connect_clicked(self):
        """连接按钮点击"""
        self.connect_requested.emit()

    def _on_disconnect_clicked(self):
        """断开按钮点击"""
        self.disconnect_requested.emit()

    # ========== Data Binding Slots ==========

    @pyqtSlot(bool)
    def update_connection_buttons(self, connected: bool):
        """
        更新连接按钮状态

        Args:
            connected: 是否已连接
        """
        self._connect_btn.setEnabled(not connected)
        self._disconnect_btn.setEnabled(connected)

    @pyqtSlot(str)
    def show_error_message(self, message: str):
        """
        显示错误消息对话框

        Args:
            message: 错误消息
        """
        QMessageBox.critical(self, "错误", message)

    @pyqtSlot(str)
    def show_info_message(self, message: str):
        """
        显示信息消息对话框

        Args:
            message: 信息消息
        """
        QMessageBox.information(self, "信息", message)

    @pyqtSlot(str)
    def show_warning_message(self, message: str):
        """
        显示警告消息对话框

        Args:
            message: 警告消息
        """
        QMessageBox.warning(self, "警告", message)

    @pyqtSlot(str, str)
    def show_confirm_dialog(self, title: str, message: str) -> bool:
        """
        显示确认对话框

        Args:
            title: 对话框标题
            message: 确认消息

        Returns:
            bool: 用户是否确认
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def showEvent(self, event):
        """
        窗口显示事件
        在窗口显示后设置分割器的初始大小

        Args:
            event: 显示事件
        """
        super().showEvent(event)
        # 窗口显示后设置分割器大小，确保右侧面板默认380像素
        if self.main_splitter:
            # 获取当前窗口宽度，计算左侧和右侧的大小
            window_width = self.width()
            right_width = 380
            left_width = window_width - right_width
            self.main_splitter.setSizes([left_width, right_width])

    def closeEvent(self, event):
        """
        窗口关闭事件

        Args:
            event: 关闭事件
        """
        # 可以在这里添加关闭前的确认逻辑
        event.accept()
