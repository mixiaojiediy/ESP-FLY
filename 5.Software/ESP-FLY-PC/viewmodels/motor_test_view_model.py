"""
MotorTestViewModel - 电机测试ViewModel
管理电机测试参数，负责循环发送电机测试命令
"""

import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from models.motor_test_model import MotorTestModel
from services.network_service import NetworkService
from services.protocol_service import ProtocolService


class MotorTestViewModel(QObject):
    """
    电机测试ViewModel

    职责：
    - 管理MotorTestModel数据
    - 处理电机测试命令
    - 50Hz循环发送电机测试数据包到ESP32
    - 发射属性变化信号供View绑定
    """

    # Property Changed信号
    motor1_pwm_changed = pyqtSignal(int)
    motor2_pwm_changed = pyqtSignal(int)
    motor3_pwm_changed = pyqtSignal(int)
    motor4_pwm_changed = pyqtSignal(int)

    # 事件信号
    command_sent = pyqtSignal(bool)

    # 发送频率
    CONTROL_FREQUENCY = 50  # Hz

    def __init__(
        self, network_service: NetworkService, protocol_service: ProtocolService
    ):
        super().__init__()

        # Model
        self._model = MotorTestModel()

        # Services
        self._network_service = network_service
        self._protocol_service = protocol_service

        # 发送线程
        self._send_thread = None
        self._is_sending = False

    # ========== Properties ==========

    @property
    def motor1_pwm(self) -> int:
        return self._model.motor1_pwm

    @motor1_pwm.setter
    def motor1_pwm(self, value: int):
        value = max(0, min(value, self._model.max_pwm))
        if self._model.motor1_pwm != value:
            self._model.motor1_pwm = value
            self.motor1_pwm_changed.emit(value)

    @property
    def motor2_pwm(self) -> int:
        return self._model.motor2_pwm

    @motor2_pwm.setter
    def motor2_pwm(self, value: int):
        value = max(0, min(value, self._model.max_pwm))
        if self._model.motor2_pwm != value:
            self._model.motor2_pwm = value
            self.motor2_pwm_changed.emit(value)

    @property
    def motor3_pwm(self) -> int:
        return self._model.motor3_pwm

    @motor3_pwm.setter
    def motor3_pwm(self, value: int):
        value = max(0, min(value, self._model.max_pwm))
        if self._model.motor3_pwm != value:
            self._model.motor3_pwm = value
            self.motor3_pwm_changed.emit(value)

    @property
    def motor4_pwm(self) -> int:
        return self._model.motor4_pwm

    @motor4_pwm.setter
    def motor4_pwm(self, value: int):
        value = max(0, min(value, self._model.max_pwm))
        if self._model.motor4_pwm != value:
            self._model.motor4_pwm = value
            self.motor4_pwm_changed.emit(value)

    @property
    def max_pwm(self) -> int:
        return self._model.max_pwm

    # ========== Commands ==========

    @pyqtSlot(int, int)
    def set_motor_pwm_command(self, motor_id: int, pwm: int):
        """
        设置单个电机PWM命令

        Args:
            motor_id: 电机ID（1-4）
            pwm: PWM值（0-65535）
        """
        # 更新对应电机的PWM值
        if motor_id == 1:
            self.motor1_pwm = pwm
        elif motor_id == 2:
            self.motor2_pwm = pwm
        elif motor_id == 3:
            self.motor3_pwm = pwm
        elif motor_id == 4:
            self.motor4_pwm = pwm

        # 检查是否有任意电机>0
        has_active = self._model.has_any_motor_active()

        if has_active and not self._is_sending:
            # 有电机有值且未在发送，启动循环发送
            self._start_sending_loop()
        elif not has_active and self._is_sending:
            # 所有电机为0且正在发送，先发送停止包再停止循环
            self._send_stop_packet()
            self._stop_sending_loop()

    @pyqtSlot()
    def reset_command(self):
        """重置命令 - 设置所有PWM为0"""
        # 记录之前的发送状态
        was_sending = self._is_sending
        
        # 直接设置所有PWM为0（不触发自动更新）
        self._model.motor1_pwm = 0
        self._model.motor2_pwm = 0
        self._model.motor3_pwm = 0
        self._model.motor4_pwm = 0
        
        # 发送信号更新UI
        self.motor1_pwm_changed.emit(0)
        self.motor2_pwm_changed.emit(0)
        self.motor3_pwm_changed.emit(0)
        self.motor4_pwm_changed.emit(0)
        
        # 如果已连接，强制发送一次停止包（enable=False）
        if self._network_service.is_connected:
            self._send_stop_packet()
        
        # 如果之前正在发送，停止发送循环
        if was_sending:
            self._stop_sending_loop()

    # ========== Private Methods ==========

    def _start_sending_loop(self):
        """启动50Hz发送循环"""
        if self._is_sending:
            return

        self._is_sending = True
        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._send_thread.start()

    def _stop_sending_loop(self):
        """停止发送循环"""
        self._is_sending = False
        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=1.0)
        self._send_thread = None

    def _send_loop(self):
        """发送循环（50Hz）"""
        period = 1.0 / self.CONTROL_FREQUENCY

        while self._is_sending:
            start_time = time.time()

            # 发送电机测试命令
            success = self._send_motor_test(enable=True)
            self.command_sent.emit(success)

            # 保持固定频率
            elapsed = time.time() - start_time
            sleep_time = period - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _send_motor_test(self, enable: bool) -> bool:
        """
        发送电机测试数据包

        Args:
            enable: 测试使能状态

        Returns:
            bool: 发送是否成功
        """
        if not self._network_service.is_connected:
            return False

        # 构建并发送数据包
        packet = self._protocol_service.build_motor_test_packet(
            m1_pwm=self._model.motor1_pwm,
            m2_pwm=self._model.motor2_pwm,
            m3_pwm=self._model.motor3_pwm,
            m4_pwm=self._model.motor4_pwm,
            enable=enable,
        )

        return self._network_service.send_packet(packet)

    def _send_stop_packet(self):
        """发送停止包（enable=False）"""
        self._send_motor_test(enable=False)

    def __del__(self):
        """析构函数"""
        self._stop_sending_loop()
