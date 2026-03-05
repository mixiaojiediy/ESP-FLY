"""
PidView - PID调参面板
用于配置PID参数
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QTabWidget,
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QMouseEvent


class EditableDoubleSpinBox(QDoubleSpinBox):
    """
    改进的QDoubleSpinBox，解决小数位无法覆盖输入的问题。

    - 点击输入框时自动全选文本，方便直接覆盖输入
    - 通过焦点获取时自动全选，提升输入体验
    """

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # 延迟全选，确保在焦点事件处理完成后执行
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        # 点击时也全选，方便直接覆盖
        QTimer.singleShot(0, self.selectAll)


class PidView(QWidget):
    """
    PID参数调整面板View

    用户操作通过信号发送给ViewModel
    """

    # 用户操作信号
    pid_changed = pyqtSignal(
        str, str, float, float, float
    )  # loop_type, axis, kp, ki, kd
    send_all_requested = pyqtSignal()
    save_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # PID参数范围
        self._kp_min = 0.0
        self._kp_max = 1000.0
        self._ki_min = 0.0
        self._ki_max = 1000.0
        self._kd_min = 0.0
        self._kd_max = 100.0

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # Tab控件（角度环/角速度环）
        tab_widget = QTabWidget()

        # 角度环
        angle_tab = self._create_pid_tab("angle")
        tab_widget.addTab(angle_tab, "角度环 (外环)")

        # 角速度环
        rate_tab = self._create_pid_tab("rate")
        tab_widget.addTab(rate_tab, "角速度环 (内环)")

        layout.addWidget(tab_widget)

        # 控制按钮
        button_layout = QHBoxLayout()

        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_requested.emit)
        button_layout.addWidget(save_btn)

        send_btn = QPushButton("发送到飞控")
        send_btn.clicked.connect(self.send_all_requested.emit)
        button_layout.addWidget(send_btn)

        layout.addLayout(button_layout)

    def _create_pid_tab(self, loop_type: str) -> QWidget:
        """创建PID参数Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Roll PID
        roll_group = self._create_axis_group(loop_type, "roll", "Roll")
        layout.addWidget(roll_group)

        # Pitch PID
        pitch_group = self._create_axis_group(loop_type, "pitch", "Pitch")
        layout.addWidget(pitch_group)

        # Yaw PID
        yaw_group = self._create_axis_group(loop_type, "yaw", "Yaw")
        layout.addWidget(yaw_group)

        layout.addStretch()
        return widget

    def _create_axis_group(self, loop_type: str, axis: str, label: str) -> QGroupBox:
        """创建单个轴的PID参数组"""
        group = QGroupBox(f"{label} PID")
        layout = QHBoxLayout(group)

        # P参数
        layout.addWidget(QLabel("P:"))
        kp_spin = EditableDoubleSpinBox()
        kp_spin.setRange(self._kp_min, self._kp_max)
        kp_spin.setSingleStep(0.1)
        kp_spin.setDecimals(2)
        kp_spin.setKeyboardTracking(False)
        kp_spin.valueChanged.connect(lambda v: self._on_pid_changed(loop_type, axis))
        layout.addWidget(kp_spin)

        # I参数
        layout.addWidget(QLabel("I:"))
        ki_spin = EditableDoubleSpinBox()
        ki_spin.setRange(self._ki_min, self._ki_max)
        ki_spin.setSingleStep(0.1)
        ki_spin.setDecimals(3)
        ki_spin.setKeyboardTracking(False)
        ki_spin.valueChanged.connect(lambda v: self._on_pid_changed(loop_type, axis))
        layout.addWidget(ki_spin)

        # D参数
        layout.addWidget(QLabel("D:"))
        kd_spin = EditableDoubleSpinBox()
        kd_spin.setRange(self._kd_min, self._kd_max)
        kd_spin.setSingleStep(0.01)
        kd_spin.setDecimals(3)
        kd_spin.setKeyboardTracking(False)
        kd_spin.valueChanged.connect(lambda v: self._on_pid_changed(loop_type, axis))
        layout.addWidget(kd_spin)

        # 保存控件引用
        setattr(self, f"_{loop_type}_{axis}_kp", kp_spin)
        setattr(self, f"_{loop_type}_{axis}_ki", ki_spin)
        setattr(self, f"_{loop_type}_{axis}_kd", kd_spin)

        return group

    def _on_pid_changed(self, loop_type: str, axis: str):
        """PID参数变化"""
        kp = getattr(self, f"_{loop_type}_{axis}_kp").value()
        ki = getattr(self, f"_{loop_type}_{axis}_ki").value()
        kd = getattr(self, f"_{loop_type}_{axis}_kd").value()
        self.pid_changed.emit(loop_type, axis, kp, ki, kd)

    # ========== Data Binding Slots ==========

    @pyqtSlot(float, float, float)
    def update_angle_roll(self, kp: float, ki: float, kd: float):
        """更新角度环Roll参数"""
        self._set_pid_values("angle", "roll", kp, ki, kd)

    @pyqtSlot(float, float, float)
    def update_angle_pitch(self, kp: float, ki: float, kd: float):
        """更新角度环Pitch参数"""
        self._set_pid_values("angle", "pitch", kp, ki, kd)

    @pyqtSlot(float, float, float)
    def update_angle_yaw(self, kp: float, ki: float, kd: float):
        """更新角度环Yaw参数"""
        self._set_pid_values("angle", "yaw", kp, ki, kd)

    @pyqtSlot(float, float, float)
    def update_rate_roll(self, kp: float, ki: float, kd: float):
        """更新角速度环Roll参数"""
        self._set_pid_values("rate", "roll", kp, ki, kd)

    @pyqtSlot(float, float, float)
    def update_rate_pitch(self, kp: float, ki: float, kd: float):
        """更新角速度环Pitch参数"""
        self._set_pid_values("rate", "pitch", kp, ki, kd)

    @pyqtSlot(float, float, float)
    def update_rate_yaw(self, kp: float, ki: float, kd: float):
        """更新角速度环Yaw参数"""
        self._set_pid_values("rate", "yaw", kp, ki, kd)

    def _set_pid_values(
        self, loop_type: str, axis: str, kp: float, ki: float, kd: float
    ):
        """设置PID参数值"""
        kp_spin = getattr(self, f"_{loop_type}_{axis}_kp")
        ki_spin = getattr(self, f"_{loop_type}_{axis}_ki")
        kd_spin = getattr(self, f"_{loop_type}_{axis}_kd")

        kp_spin.blockSignals(True)
        ki_spin.blockSignals(True)
        kd_spin.blockSignals(True)

        kp_spin.setValue(kp)
        ki_spin.setValue(ki)
        kd_spin.setValue(kd)

        kp_spin.blockSignals(False)
        ki_spin.blockSignals(False)
        kd_spin.blockSignals(False)

    def get_all_pid_values(self) -> dict:
        """获取所有PID参数值"""
        result = {}
        for loop_type in ["angle", "rate"]:
            result[loop_type] = {}
            for axis in ["roll", "pitch", "yaw"]:
                kp = getattr(self, f"_{loop_type}_{axis}_kp").value()
                ki = getattr(self, f"_{loop_type}_{axis}_ki").value()
                kd = getattr(self, f"_{loop_type}_{axis}_kd").value()
                result[loop_type][axis] = {"kp": kp, "ki": ki, "kd": kd}
        return result
