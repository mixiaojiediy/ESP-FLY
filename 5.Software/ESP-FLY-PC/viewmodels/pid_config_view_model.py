"""
PidConfigViewModel - PID配置ViewModel
管理PID参数配置，负责发送PID配置命令
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from models.pid_config_model import PidConfigModel, PidAxisConfig
from services.network_service import NetworkService
from services.protocol_service import ProtocolService
from services.config_service import ConfigService


class PidConfigViewModel(QObject):
    """
    PID配置ViewModel

    职责：
    - 管理PidConfigModel数据
    - 处理PID参数修改
    - 发送PID配置命令到ESP32
    - 发射属性变化信号供View绑定
    """

    # Property Changed信号 - 角度环（外环）
    angle_roll_changed = pyqtSignal(float, float, float)  # kp, ki, kd
    angle_pitch_changed = pyqtSignal(float, float, float)
    angle_yaw_changed = pyqtSignal(float, float, float)

    # Property Changed信号 - 角速度环（内环）
    rate_roll_changed = pyqtSignal(float, float, float)
    rate_pitch_changed = pyqtSignal(float, float, float)
    rate_yaw_changed = pyqtSignal(float, float, float)

    # 范围变化信号
    pid_range_changed = pyqtSignal(float, float, float, float, float, float)  # p_min, p_max, i_min, i_max, d_min, d_max

    # 事件信号
    config_sent = pyqtSignal(bool)
    config_saved = pyqtSignal(bool)

    def __init__(
        self,
        network_service: NetworkService,
        protocol_service: ProtocolService,
        config_service: ConfigService = None,
    ):
        super().__init__()

        # Model
        self._model = PidConfigModel()

        # Services
        self._network_service = network_service
        self._protocol_service = protocol_service
        self._config_service = config_service

        # 如果提供了ConfigService，从config.ini加载PID配置（只加载数据，不发送信号）
        # 符合MVVM模式：ViewModel初始化时只管理数据，不关心View是否存在
        if self._config_service:
            self._load_from_config_service(emit_signals=False)

    # ========== Properties ==========

    @property
    def model(self) -> PidConfigModel:
        return self._model

    def get_axis_config(self, loop_type: str, axis: str) -> PidAxisConfig:
        """获取指定轴的PID配置"""
        return self._model.get_axis_config(loop_type, axis)

    def initialize_ui(self):
        """
        初始化UI显示（在数据绑定建立后调用）
        符合MVVM模式：View绑定后，ViewModel通知View获取初始值
        """
        self.pid_range_changed.emit(
            self._model.kp_min,
            self._model.kp_max,
            self._model.ki_min,
            self._model.ki_max,
            self._model.kd_min,
            self._model.kd_max,
        )
        self._emit_all_changed()

    # ========== Commands ==========

    @pyqtSlot(str, str, float, float, float)
    def set_pid_command(
        self, loop_type: str, axis: str, kp: float, ki: float, kd: float
    ):
        """
        设置PID参数命令

        Args:
            loop_type: 'angle' 或 'rate'
            axis: 'roll', 'pitch', 'yaw'
            kp, ki, kd: PID参数值
        """
        self._model.set_axis_config(loop_type, axis, kp, ki, kd)

        # 发射变化信号
        if loop_type == "angle":
            if axis == "roll":
                config = self._model.angle_roll
                self.angle_roll_changed.emit(config.kp, config.ki, config.kd)
            elif axis == "pitch":
                config = self._model.angle_pitch
                self.angle_pitch_changed.emit(config.kp, config.ki, config.kd)
            elif axis == "yaw":
                config = self._model.angle_yaw
                self.angle_yaw_changed.emit(config.kp, config.ki, config.kd)
        elif loop_type == "rate":
            if axis == "roll":
                config = self._model.rate_roll
                self.rate_roll_changed.emit(config.kp, config.ki, config.kd)
            elif axis == "pitch":
                config = self._model.rate_pitch
                self.rate_pitch_changed.emit(config.kp, config.ki, config.kd)
            elif axis == "yaw":
                config = self._model.rate_yaw
                self.rate_yaw_changed.emit(config.kp, config.ki, config.kd)

    @pyqtSlot()
    def send_config_command(self) -> bool:
        """发送PID配置到ESP32命令"""
        if not self._network_service.is_connected:
            self.config_sent.emit(False)
            return False

        packet = self._protocol_service.build_pid_config_packet(
            # 角度环
            self._model.angle_roll.kp,
            self._model.angle_roll.ki,
            self._model.angle_roll.kd,
            self._model.angle_pitch.kp,
            self._model.angle_pitch.ki,
            self._model.angle_pitch.kd,
            self._model.angle_yaw.kp,
            self._model.angle_yaw.ki,
            self._model.angle_yaw.kd,
            # 角速度环
            self._model.rate_roll.kp,
            self._model.rate_roll.ki,
            self._model.rate_roll.kd,
            self._model.rate_pitch.kp,
            self._model.rate_pitch.ki,
            self._model.rate_pitch.kd,
            self._model.rate_yaw.kp,
            self._model.rate_yaw.ki,
            self._model.rate_yaw.kd,
        )

        success = self._network_service.send_packet(packet)
        self.config_sent.emit(success)
        return success

    @pyqtSlot()
    def save_config_command(self) -> bool:
        """保存PID配置到config.ini命令"""
        config_service = self._config_service
        if not config_service:
            # 如果没有ConfigService，创建新实例保存到config.ini
            config_service = ConfigService()

        config_dict = self._model.to_config_dict()
        success = config_service.save_pid_config(config_dict)
        self.config_saved.emit(success)
        return success

    def _load_from_config_service(self, emit_signals: bool = True):
        """
        从ConfigService加载PID配置

        Args:
            emit_signals: 是否发送信号更新UI（初始化时为False，避免信号丢失）
        """
        if self._config_service:
            config_dict = self._config_service.get_pid_config()
            self._model = PidConfigModel.from_config_dict(config_dict)
            if emit_signals:
                self._emit_all_changed()

    @pyqtSlot()
    def reset_to_default_command(self):
        """重置为默认值命令"""
        self._model.reset_to_default()
        self._emit_all_changed()

    # ========== Private Methods ==========

    def _emit_all_changed(self):
        """发射所有参数变化信号"""
        self.angle_roll_changed.emit(
            self._model.angle_roll.kp,
            self._model.angle_roll.ki,
            self._model.angle_roll.kd,
        )
        self.angle_pitch_changed.emit(
            self._model.angle_pitch.kp,
            self._model.angle_pitch.ki,
            self._model.angle_pitch.kd,
        )
        self.angle_yaw_changed.emit(
            self._model.angle_yaw.kp, self._model.angle_yaw.ki, self._model.angle_yaw.kd
        )
        self.rate_roll_changed.emit(
            self._model.rate_roll.kp, self._model.rate_roll.ki, self._model.rate_roll.kd
        )
        self.rate_pitch_changed.emit(
            self._model.rate_pitch.kp,
            self._model.rate_pitch.ki,
            self._model.rate_pitch.kd,
        )
        self.rate_yaw_changed.emit(
            self._model.rate_yaw.kp, self._model.rate_yaw.ki, self._model.rate_yaw.kd
        )
