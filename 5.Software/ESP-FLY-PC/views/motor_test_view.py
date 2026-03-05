"""
MotorTestView - 电机测试面板
用于测试四个电机
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QSpinBox,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot


class MotorTestView(QWidget):
    """
    电机测试面板View

    用户操作通过信号发送给ViewModel
    """

    # 用户操作信号
    motor_pwm_changed = pyqtSignal(int, int)  # motor_id, pwm
    reset_requested = pyqtSignal()

    def __init__(self, max_pwm: int = 65535, parent=None):
        super().__init__(parent)

        self._max_pwm = max_pwm
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 警告提示
        warning_label = QLabel("⚠️ 注意：电机测试时请移除螺旋桨！")
        warning_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(warning_label)

        # 电机控制组
        motors_group = self._create_motors_group()
        layout.addWidget(motors_group)

        # 控制按钮
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

        layout.addStretch()

    def _create_motors_group(self) -> QGroupBox:
        """创建电机控制组"""
        group = QGroupBox("单独电机控制")
        layout = QVBoxLayout(group)

        # 电机1-4
        for i in range(1, 5):
            motor_layout = QHBoxLayout()

            motor_layout.addWidget(QLabel(f"电机{i}:"))

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, self._max_pwm)
            slider.setValue(0)
            slider.valueChanged.connect(
                lambda v, m=i: self._on_motor_slider_changed(m, v)
            )
            motor_layout.addWidget(slider)

            spin = QSpinBox()
            spin.setRange(0, self._max_pwm)
            spin.setValue(0)
            spin.valueChanged.connect(lambda v, m=i: self._on_motor_spin_changed(m, v))
            motor_layout.addWidget(spin)

            # 保存控件引用
            setattr(self, f"_motor{i}_slider", slider)
            setattr(self, f"_motor{i}_spin", spin)

            layout.addLayout(motor_layout)

        return group

    def _create_button_layout(self) -> QHBoxLayout:
        """创建控制按钮"""
        layout = QHBoxLayout()

        # 重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._on_reset_clicked)
        layout.addWidget(reset_btn)

        return layout

    # ========== Private Event Handlers ==========

    def _on_motor_slider_changed(self, motor_id: int, value: int):
        """电机滑块变化"""
        spin = getattr(self, f"_motor{motor_id}_spin")
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)
        self.motor_pwm_changed.emit(motor_id, value)

    def _on_motor_spin_changed(self, motor_id: int, value: int):
        """电机输入框变化"""
        slider = getattr(self, f"_motor{motor_id}_slider")
        slider.blockSignals(True)
        slider.setValue(value)
        slider.blockSignals(False)
        self.motor_pwm_changed.emit(motor_id, value)

    def _on_reset_clicked(self):
        """重置按钮点击"""
        # 重置所有滑块为0
        for i in range(1, 5):
            slider = getattr(self, f"_motor{i}_slider")
            spin = getattr(self, f"_motor{i}_spin")
            slider.blockSignals(True)
            spin.blockSignals(True)
            slider.setValue(0)
            spin.setValue(0)
            slider.blockSignals(False)
            spin.blockSignals(False)
        self.reset_requested.emit()

    # ========== Data Binding Slots ==========

    @pyqtSlot(int)
    def update_motor1_pwm(self, value: int):
        """更新电机1 PWM"""
        self._motor1_slider.blockSignals(True)
        self._motor1_spin.blockSignals(True)
        self._motor1_slider.setValue(value)
        self._motor1_spin.setValue(value)
        self._motor1_slider.blockSignals(False)
        self._motor1_spin.blockSignals(False)

    @pyqtSlot(int)
    def update_motor2_pwm(self, value: int):
        """更新电机2 PWM"""
        self._motor2_slider.blockSignals(True)
        self._motor2_spin.blockSignals(True)
        self._motor2_slider.setValue(value)
        self._motor2_spin.setValue(value)
        self._motor2_slider.blockSignals(False)
        self._motor2_spin.blockSignals(False)

    @pyqtSlot(int)
    def update_motor3_pwm(self, value: int):
        """更新电机3 PWM"""
        self._motor3_slider.blockSignals(True)
        self._motor3_spin.blockSignals(True)
        self._motor3_slider.setValue(value)
        self._motor3_spin.setValue(value)
        self._motor3_slider.blockSignals(False)
        self._motor3_spin.blockSignals(False)

    @pyqtSlot(int)
    def update_motor4_pwm(self, value: int):
        """更新电机4 PWM"""
        self._motor4_slider.blockSignals(True)
        self._motor4_spin.blockSignals(True)
        self._motor4_slider.setValue(value)
        self._motor4_spin.setValue(value)
        self._motor4_slider.blockSignals(False)
        self._motor4_spin.blockSignals(False)
