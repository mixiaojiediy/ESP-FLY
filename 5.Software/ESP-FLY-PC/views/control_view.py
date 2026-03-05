"""
ControlView - 控制面板
用于控制无人机的姿态角和油门
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QDoubleSpinBox,
    QSlider,
    QSpinBox,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot


class ControlView(QWidget):
    """
    控制面板View（纯View，通过信号与ViewModel通信）

    用户操作通过信号发送给ViewModel，
    ViewModel的属性变化通过Slot接收并更新UI
    """

    # 用户操作信号（发送给ViewModel）
    roll_value_changed = pyqtSignal(float)
    pitch_value_changed = pyqtSignal(float)
    yaw_value_changed = pyqtSignal(float)
    thrust_value_changed = pyqtSignal(int)
    reset_requested = pyqtSignal()

    def __init__(
        self,
        max_angle: float = 30.0,
        max_yaw: float = 180.0,
        max_thrust: int = 65535,
        parent=None,
    ):
        super().__init__(parent)

        self._max_angle = max_angle
        self._max_yaw = max_yaw
        self._max_thrust = max_thrust

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 姿态角控制组
        attitude_group = self._create_attitude_group()
        layout.addWidget(attitude_group)

        # 油门控制组
        thrust_group = self._create_thrust_group()
        layout.addWidget(thrust_group)

        # 控制按钮
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

        layout.addStretch()

    def _create_attitude_group(self) -> QGroupBox:
        """创建姿态角控制组"""
        group = QGroupBox("姿态角控制")
        layout = QVBoxLayout(group)

        # Roll控制
        roll_layout = QHBoxLayout()
        roll_layout.addWidget(QLabel("横滚角 (Roll):"))
        self._roll_spin = QDoubleSpinBox()
        self._roll_spin.setRange(-self._max_angle, self._max_angle)
        self._roll_spin.setSingleStep(1.0)
        self._roll_spin.setValue(0.0)
        self._roll_spin.setSuffix("°")
        self._roll_spin.valueChanged.connect(self._on_roll_changed)
        roll_layout.addWidget(self._roll_spin)
        layout.addLayout(roll_layout)

        # Pitch控制
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("俯仰角 (Pitch):"))
        self._pitch_spin = QDoubleSpinBox()
        self._pitch_spin.setRange(-self._max_angle, self._max_angle)
        self._pitch_spin.setSingleStep(1.0)
        self._pitch_spin.setValue(0.0)
        self._pitch_spin.setSuffix("°")
        self._pitch_spin.valueChanged.connect(self._on_pitch_changed)
        pitch_layout.addWidget(self._pitch_spin)
        layout.addLayout(pitch_layout)

        # Yaw控制
        yaw_layout = QHBoxLayout()
        yaw_layout.addWidget(QLabel("偏航角 (Yaw):"))
        self._yaw_spin = QDoubleSpinBox()
        self._yaw_spin.setRange(-self._max_yaw, self._max_yaw)
        self._yaw_spin.setSingleStep(1.0)
        self._yaw_spin.setValue(0.0)
        self._yaw_spin.setSuffix("°")
        self._yaw_spin.valueChanged.connect(self._on_yaw_changed)
        yaw_layout.addWidget(self._yaw_spin)
        layout.addLayout(yaw_layout)

        return group

    def _create_thrust_group(self) -> QGroupBox:
        """创建油门控制组"""
        group = QGroupBox("油门控制")
        layout = QVBoxLayout(group)

        # 油门滑块
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("油门:"))

        self._thrust_slider = QSlider(Qt.Orientation.Horizontal)
        self._thrust_slider.setRange(0, self._max_thrust)
        self._thrust_slider.setSingleStep(1000)
        self._thrust_slider.setValue(0)
        self._thrust_slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self._thrust_slider)

        self._thrust_spin = QSpinBox()
        self._thrust_spin.setRange(0, self._max_thrust)
        self._thrust_spin.setSingleStep(1000)
        self._thrust_spin.setValue(0)
        self._thrust_spin.valueChanged.connect(self._on_spin_changed)
        slider_layout.addWidget(self._thrust_spin)

        layout.addLayout(slider_layout)

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

    def _on_roll_changed(self, value: float):
        """Roll值变化"""
        self.roll_value_changed.emit(value)

    def _on_pitch_changed(self, value: float):
        """Pitch值变化"""
        self.pitch_value_changed.emit(value)

    def _on_yaw_changed(self, value: float):
        """Yaw值变化"""
        self.yaw_value_changed.emit(value)

    def _on_slider_changed(self, value: int):
        """油门滑块变化"""
        self._thrust_spin.blockSignals(True)
        self._thrust_spin.setValue(value)
        self._thrust_spin.blockSignals(False)
        self.thrust_value_changed.emit(value)

    def _on_spin_changed(self, value: int):
        """油门输入框变化"""
        self._thrust_slider.blockSignals(True)
        self._thrust_slider.setValue(value)
        self._thrust_slider.blockSignals(False)
        self.thrust_value_changed.emit(value)

    def _on_reset_clicked(self):
        """重置按钮点击"""
        self._roll_spin.setValue(0.0)
        self._pitch_spin.setValue(0.0)
        self._yaw_spin.setValue(0.0)
        self._thrust_slider.setValue(0)
        self.reset_requested.emit()

    # ========== Data Binding Slots ==========

    @pyqtSlot(float)
    def update_roll(self, value: float):
        """更新Roll显示"""
        self._roll_spin.blockSignals(True)
        self._roll_spin.setValue(value)
        self._roll_spin.blockSignals(False)

    @pyqtSlot(float)
    def update_pitch(self, value: float):
        """更新Pitch显示"""
        self._pitch_spin.blockSignals(True)
        self._pitch_spin.setValue(value)
        self._pitch_spin.blockSignals(False)

    @pyqtSlot(float)
    def update_yaw(self, value: float):
        """更新Yaw显示"""
        self._yaw_spin.blockSignals(True)
        self._yaw_spin.setValue(value)
        self._yaw_spin.blockSignals(False)

    @pyqtSlot(int)
    def update_thrust(self, value: int):
        """更新油门显示"""
        self._thrust_slider.blockSignals(True)
        self._thrust_spin.blockSignals(True)
        self._thrust_slider.setValue(value)
        self._thrust_spin.setValue(value)
        self._thrust_slider.blockSignals(False)
        self._thrust_spin.blockSignals(False)
