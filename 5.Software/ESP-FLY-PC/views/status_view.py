"""
StatusView - 状态显示面板
显示连接状态、电池状态、通信统计等信息
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
)
from PyQt6.QtCore import pyqtSlot


class StatusView(QWidget):
    """
    状态显示面板（纯View，无业务逻辑）

    通过pyqtSlot接收ViewModel的属性变化信号自动更新UI
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 连接状态组
        connection_group = self._create_connection_group()
        layout.addWidget(connection_group)

        # 电池状态组
        battery_group = self._create_battery_group()
        layout.addWidget(battery_group)

        # 统计信息组
        stats_group = self._create_stats_group()
        layout.addWidget(stats_group)

        layout.addStretch()

    def _create_connection_group(self) -> QGroupBox:
        """创建连接状态组"""
        group = QGroupBox("连接状态")
        layout = QVBoxLayout(group)

        self._connection_label = QLabel("未连接")
        self._connection_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self._connection_label)

        return group

    def _create_battery_group(self) -> QGroupBox:
        """创建电池状态组"""
        group = QGroupBox("电池状态")
        layout = QVBoxLayout(group)

        # 电压显示
        voltage_layout = QHBoxLayout()
        voltage_layout.addWidget(QLabel("电压:"))
        self._voltage_label = QLabel("--")
        voltage_layout.addWidget(self._voltage_label)
        voltage_layout.addStretch()
        layout.addLayout(voltage_layout)

        # 电量进度条
        self._battery_progress = QProgressBar()
        self._battery_progress.setRange(0, 100)
        self._battery_progress.setValue(0)
        self._battery_progress.setFormat("%p%")
        layout.addWidget(self._battery_progress)

        return group

    def _create_stats_group(self) -> QGroupBox:
        """创建统计信息组"""
        group = QGroupBox("通信统计")
        layout = QVBoxLayout(group)

        self._recv_count_label = QLabel("接收数据包: 0")
        self._sent_count_label = QLabel("发送数据包: 0")
        self._signal_label = QLabel("WiFi信号强度: -- dBm")

        layout.addWidget(self._recv_count_label)
        layout.addWidget(self._sent_count_label)
        layout.addWidget(self._signal_label)

        return group

    # ========== Data Binding Slots ==========

    @pyqtSlot(bool)
    def update_connection_status(self, connected: bool):
        """更新连接状态"""
        if connected:
            self._connection_label.setText("已连接")
            self._connection_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self._connection_label.setText("未连接")
            self._connection_label.setStyleSheet("color: #d32f2f; font-weight: bold;")

    @pyqtSlot(float)
    def update_battery_voltage(self, voltage: float):
        """更新电池电压"""
        self._voltage_label.setText(f"{voltage:.2f}V")

    @pyqtSlot(int)
    def update_battery_percentage(self, percentage: int):
        """更新电池电量"""
        self._battery_progress.setValue(percentage)

        # 根据电量设置颜色
        if percentage > 50:
            color = "#4caf50"  # 绿色
        elif percentage > 20:
            color = "#ff9800"  # 橙色
        else:
            color = "#d32f2f"  # 红色

        self._battery_progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; }}"
        )

    @pyqtSlot(int)
    def update_recv_count(self, count: int):
        """更新接收包数"""
        self._recv_count_label.setText(f"接收数据包: {count}")

    @pyqtSlot(int)
    def update_sent_count(self, count: int):
        """更新发送包数"""
        self._sent_count_label.setText(f"发送数据包: {count}")

    @pyqtSlot(int, int)
    def update_stats(self, sent: int, recv: int):
        """更新统计信息"""
        self._recv_count_label.setText(f"接收数据包: {recv}")
        self._sent_count_label.setText(f"发送数据包: {sent}")

    @pyqtSlot(int)
    def update_signal_strength(self, rssi: int):
        """更新信号强度"""
        if rssi == 0:
            self._signal_label.setText("WiFi信号强度: -- dBm")
            self._signal_label.setStyleSheet("")
        else:
            self._signal_label.setText(f"WiFi信号强度: {rssi} dBm")

            if rssi >= -50:
                color = "#4caf50"  # 绿色 - 信号很好
            elif rssi >= -70:
                color = "#ff9800"  # 橙色 - 信号一般
            else:
                color = "#d32f2f"  # 红色 - 信号较差

            self._signal_label.setStyleSheet(f"color: {color};")
