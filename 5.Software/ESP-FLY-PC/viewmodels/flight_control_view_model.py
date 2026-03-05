"""
FlightControlViewModel - 飞行控制ViewModel
管理飞行控制参数，负责50Hz周期发送控制命令
"""

import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from models.flight_control_model import FlightControlModel
from services.network_service import NetworkService
from services.protocol_service import ProtocolService


class FlightControlViewModel(QObject):
    """
    飞行控制ViewModel
    
    职责：
    - 管理FlightControlModel数据
    - 处理用户控制输入
    - 50Hz周期发送控制命令
    - 发射属性变化信号供View绑定
    """
    
    # Property Changed信号
    target_roll_changed = pyqtSignal(float)
    target_pitch_changed = pyqtSignal(float)
    target_yaw_changed = pyqtSignal(float)
    thrust_changed = pyqtSignal(int)
    is_enabled_changed = pyqtSignal(bool)
    
    # 命令结果信号
    command_sent = pyqtSignal(bool)
    
    # 发送频率
    CONTROL_FREQUENCY = 50  # Hz
    
    def __init__(self, network_service: NetworkService, protocol_service: ProtocolService):
        super().__init__()
        
        # Model
        self._model = FlightControlModel()
        
        # Services
        self._network_service = network_service
        self._protocol_service = protocol_service
        
        # 发送线程
        self._send_thread = None
        self._is_sending = False
        
        # 统计
        self._command_count = 0
    
    # ========== Properties ==========
    
    @property
    def target_roll(self) -> float:
        return self._model.target_roll
    
    @target_roll.setter
    def target_roll(self, value: float):
        value = max(-self._model.max_angle, min(value, self._model.max_angle))
        if self._model.target_roll != value:
            self._model.target_roll = value
            self.target_roll_changed.emit(value)
            self._update_sending_state()
    
    @property
    def target_pitch(self) -> float:
        return self._model.target_pitch
    
    @target_pitch.setter
    def target_pitch(self, value: float):
        value = max(-self._model.max_angle, min(value, self._model.max_angle))
        if self._model.target_pitch != value:
            self._model.target_pitch = value
            self.target_pitch_changed.emit(value)
            self._update_sending_state()
    
    @property
    def target_yaw(self) -> float:
        return self._model.target_yaw
    
    @target_yaw.setter
    def target_yaw(self, value: float):
        value = max(-self._model.max_yaw, min(value, self._model.max_yaw))
        if self._model.target_yaw != value:
            self._model.target_yaw = value
            self.target_yaw_changed.emit(value)
            self._update_sending_state()
    
    @property
    def thrust(self) -> int:
        return self._model.thrust
    
    @thrust.setter
    def thrust(self, value: int):
        value = max(self._model.min_thrust, min(value, self._model.max_thrust))
        if self._model.thrust != value:
            self._model.thrust = value
            self.thrust_changed.emit(value)
            self._update_sending_state()
    
    @property
    def is_enabled(self) -> bool:
        return self._model.is_enabled
    
    @property
    def max_angle(self) -> float:
        return self._model.max_angle
    
    @property
    def max_yaw(self) -> float:
        return self._model.max_yaw
    
    @property
    def max_thrust(self) -> int:
        return self._model.max_thrust
    
    @property
    def command_count(self) -> int:
        return self._command_count
    
    # ========== Commands ==========
    
    @pyqtSlot()
    def enable_control_command(self):
        """启用控制命令"""
        if not self._model.is_enabled:
            self._model.is_enabled = True
            self.is_enabled_changed.emit(True)
            self._start_sending_loop()
    
    @pyqtSlot()
    def disable_control_command(self):
        """禁用控制命令"""
        if self._model.is_enabled:
            self._stop_sending_loop()
            self._model.is_enabled = False
            self.is_enabled_changed.emit(False)
    
    @pyqtSlot()
    def reset_control_command(self):
        """重置控制参数命令"""
        # 先停止自动更新发送状态，避免重复触发
        was_sending = self._is_sending
        
        # 设置所有值为0（不触发自动发送状态更新）
        self._model.target_roll = 0.0
        self._model.target_pitch = 0.0
        self._model.target_yaw = 0.0
        self._model.thrust = 0
        
        # 发送信号更新UI
        self.target_roll_changed.emit(0.0)
        self.target_pitch_changed.emit(0.0)
        self.target_yaw_changed.emit(0.0)
        self.thrust_changed.emit(0)
        
        # 如果已连接，强制发送一次全零命令
        if self._network_service.is_connected:
            self._send_control_packet()
        
        # 如果之前正在发送，停止发送循环
        if was_sending:
            self.disable_control_command()
    
    @pyqtSlot(float)
    def set_roll_command(self, value: float):
        """设置Roll命令"""
        self.target_roll = value
    
    @pyqtSlot(float)
    def set_pitch_command(self, value: float):
        """设置Pitch命令"""
        self.target_pitch = value
    
    @pyqtSlot(float)
    def set_yaw_command(self, value: float):
        """设置Yaw命令"""
        self.target_yaw = value
    
    @pyqtSlot(int)
    def set_thrust_command(self, value: int):
        """设置油门命令"""
        self.thrust = value
    
    @pyqtSlot(float, float, float, int)
    def set_control_command(self, roll: float, pitch: float, yaw: float, thrust: int):
        """设置所有控制参数命令"""
        self.target_roll = roll
        self.target_pitch = pitch
        self.target_yaw = yaw
        self.thrust = thrust
    
    # ========== 配置方法 ==========
    
    def set_limits(self, max_angle: float = None, max_yaw: float = None, max_thrust: int = None):
        """设置控制限制"""
        if max_angle is not None:
            self._model.max_angle = max_angle
        if max_yaw is not None:
            self._model.max_yaw = max_yaw
        if max_thrust is not None:
            self._model.max_thrust = max_thrust
    
    # ========== Private Methods ==========
    
    def _has_control_input(self) -> bool:
        """检查是否有非零的控制输入"""
        return (
            self._model.target_roll != 0.0 or 
            self._model.target_pitch != 0.0 or 
            self._model.target_yaw != 0.0 or 
            self._model.thrust != 0
        )
    
    def _update_sending_state(self):
        """根据控制输入状态自动启动或停止发送"""
        if not self._network_service.is_connected:
            return
        
        has_input = self._has_control_input()
        
        if has_input and not self._is_sending:
            # 有控制输入且未在发送，启动发送循环
            self.enable_control_command()
        elif not has_input and self._is_sending:
            # 从非零变为全零且正在发送时，发送最后一次全零命令后停止
            self._send_final_zero_and_stop()
    
    def _send_final_zero_and_stop(self):
        """发送最后一次全零命令并停止发送"""
        # 发送一次全零命令
        self._send_control_packet()
        # 停止发送循环
        self.disable_control_command()
    
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
            
            # 发送控制命令
            success = self._send_control_packet()
            self.command_sent.emit(success)
            
            # 保持固定频率
            elapsed = time.time() - start_time
            sleep_time = period - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _send_control_packet(self) -> bool:
        """发送控制数据包"""
        if not self._network_service.is_connected:
            return False
        
        packet = self._protocol_service.build_flight_control_packet(
            self._model.target_roll,
            self._model.target_pitch,
            self._model.target_yaw,
            self._model.thrust
        )
        
        success = self._network_service.send_packet(packet)
        if success:
            self._command_count += 1
        
        return success
    
    def __del__(self):
        """析构函数"""
        self._stop_sending_loop()
