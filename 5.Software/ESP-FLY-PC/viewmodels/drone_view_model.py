"""
DroneViewModel - 核心ViewModel
管理无人机状态数据，负责接收数据解析和属性变化通知
"""

import time
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from models.drone_state_model import DroneStateModel
from services.protocol_service import ProtocolService, PacketType


class DroneViewModel(QObject):
    """
    无人机状态ViewModel

    职责：
    - 管理DroneStateModel数据
    - 接收并解析下行数据包
    - 发射属性变化信号供View绑定
    """

    # ========== 高频数据信号（50Hz）==========

    # 姿态角
    roll_changed = pyqtSignal(float)
    pitch_changed = pyqtSignal(float)
    yaw_changed = pyqtSignal(float)

    # 角速度
    gyro_x_changed = pyqtSignal(float)
    gyro_y_changed = pyqtSignal(float)
    gyro_z_changed = pyqtSignal(float)

    # 加速度
    acc_x_changed = pyqtSignal(float)
    acc_y_changed = pyqtSignal(float)
    acc_z_changed = pyqtSignal(float)

    # PID输出 - 外环（角度环输出 = 期望角速度）
    roll_rate_desired_changed = pyqtSignal(float)
    pitch_rate_desired_changed = pyqtSignal(float)
    yaw_rate_desired_changed = pyqtSignal(float)

    # PID输出 - 内环（角速度环输出 = 控制量）
    roll_control_output_changed = pyqtSignal(int)
    pitch_control_output_changed = pyqtSignal(int)
    yaw_control_output_changed = pyqtSignal(int)

    # 电机PWM
    motor1_pwm_changed = pyqtSignal(int)
    motor2_pwm_changed = pyqtSignal(int)
    motor3_pwm_changed = pyqtSignal(int)
    motor4_pwm_changed = pyqtSignal(int)

    # 时间戳
    timestamp_ms_changed = pyqtSignal(int)

    # ========== 低频数据信号（1Hz）==========

    # 电池状态
    battery_voltage_changed = pyqtSignal(float)
    battery_percentage_changed = pyqtSignal(int)
    battery_state_changed = pyqtSignal(str)

    # PID配置参数上报
    # 角度环（外环）
    angle_roll_kp_changed = pyqtSignal(float)
    angle_roll_ki_changed = pyqtSignal(float)
    angle_roll_kd_changed = pyqtSignal(float)
    angle_pitch_kp_changed = pyqtSignal(float)
    angle_pitch_ki_changed = pyqtSignal(float)
    angle_pitch_kd_changed = pyqtSignal(float)
    angle_yaw_kp_changed = pyqtSignal(float)
    angle_yaw_ki_changed = pyqtSignal(float)
    angle_yaw_kd_changed = pyqtSignal(float)

    # 角速度环（内环）
    rate_roll_kp_changed = pyqtSignal(float)
    rate_roll_ki_changed = pyqtSignal(float)
    rate_roll_kd_changed = pyqtSignal(float)
    rate_pitch_kp_changed = pyqtSignal(float)
    rate_pitch_ki_changed = pyqtSignal(float)
    rate_pitch_kd_changed = pyqtSignal(float)
    rate_yaw_kp_changed = pyqtSignal(float)
    rate_yaw_ki_changed = pyqtSignal(float)
    rate_yaw_kd_changed = pyqtSignal(float)

    # ========== 复合信号（批量更新）==========

    # 姿态数据批量更新
    attitude_changed = pyqtSignal(float, float, float)  # roll, pitch, yaw

    # 高频数据全部更新（用于波形显示）
    high_freq_data_changed = pyqtSignal(dict)

    # PID配置参数上报（用于终端监控显示）
    pid_config_reported = pyqtSignal(dict, dict)  # angle_params, rate_params

    # 控制台文本接收（来自MCU的调试输出）
    console_text_received = pyqtSignal(str)

    # 电池状态批量更新（用于终端监控显示）
    battery_status_reported = pyqtSignal(float, int, str)  # voltage, percentage, state

    # 统计信息
    packet_count_changed = pyqtSignal(int)

    def __init__(self, protocol_service: ProtocolService = None, config_service=None):
        super().__init__()

        # Model
        self._model = DroneStateModel()

        # Service
        self._protocol_service = protocol_service or ProtocolService()
        self._config_service = config_service

        # ========== 性能优化：禁用状态监控定时器 ==========
        # 状态监控定时器会每秒打印大量调试信息，在打包后的exe中会导致卡顿
        # 所有状态信息在UI上都有显示，不需要额外打印到控制台
        # self._status_monitor_timer = QTimer()
        # self._status_monitor_timer.timeout.connect(self._print_status_monitor)
        # self._status_monitor_timer.start(1000)  # 1000ms = 1秒

    # ========== Properties ==========

    @property
    def roll(self) -> float:
        return self._model.roll

    @property
    def pitch(self) -> float:
        return self._model.pitch

    @property
    def yaw(self) -> float:
        return self._model.yaw

    @property
    def gyro_x(self) -> float:
        return self._model.gyro_x

    @property
    def gyro_y(self) -> float:
        return self._model.gyro_y

    @property
    def gyro_z(self) -> float:
        return self._model.gyro_z

    @property
    def acc_x(self) -> float:
        return self._model.acc_x

    @property
    def acc_y(self) -> float:
        return self._model.acc_y

    @property
    def acc_z(self) -> float:
        return self._model.acc_z

    @property
    def battery_voltage(self) -> float:
        return self._model.battery_voltage

    @property
    def battery_percentage(self) -> int:
        return self._model.battery_percentage

    @property
    def battery_state(self) -> str:
        return self._model.battery_state

    @property
    def packet_count(self) -> int:
        return self._model.packet_count

    @property
    def model(self) -> DroneStateModel:
        """获取底层Model（只读）"""
        return self._model

    # ========== 数据处理 ==========

    @pyqtSlot(bytes)
    def on_data_received(self, data: bytes):
        """
        处理接收到的数据包

        Args:
            data: 原始数据包
        """
        packet = self._protocol_service.parse_packet(data)
        if packet is None:
            return

        if packet.packet_type == PacketType.HIGH_FREQ_DATA:
            self._update_high_freq_data(packet.data)
        elif packet.packet_type == PacketType.BATTERY_STATUS:
            self._update_battery_data(packet.data)
        elif packet.packet_type == PacketType.PID_RESPONSE:
            self._update_pid_config_data(packet.data)
        elif packet.packet_type == PacketType.CONSOLE_LOG:
            self._update_console_text(packet.data.get("text", ""))

    def _update_high_freq_data(self, data: dict):
        """更新高频数据（50Hz）"""
        # 更新Model
        self._model.roll = data.get("roll", 0.0)
        self._model.pitch = data.get("pitch", 0.0)
        self._model.yaw = data.get("yaw", 0.0)

        self._model.gyro_x = data.get("gyro_x", 0.0)
        self._model.gyro_y = data.get("gyro_y", 0.0)
        self._model.gyro_z = data.get("gyro_z", 0.0)

        self._model.acc_x = data.get("acc_x", 0.0)
        self._model.acc_y = data.get("acc_y", 0.0)
        self._model.acc_z = data.get("acc_z", 0.0)

        self._model.roll_rate_desired = data.get("roll_rate_desired", 0.0)
        self._model.pitch_rate_desired = data.get("pitch_rate_desired", 0.0)
        self._model.yaw_rate_desired = data.get("yaw_rate_desired", 0.0)

        self._model.roll_control_output = data.get("roll_control_output", 0)
        self._model.pitch_control_output = data.get("pitch_control_output", 0)
        self._model.yaw_control_output = data.get("yaw_control_output", 0)

        self._model.motor1_pwm = data.get("motor1_pwm", 0)
        self._model.motor2_pwm = data.get("motor2_pwm", 0)
        self._model.motor3_pwm = data.get("motor3_pwm", 0)
        self._model.motor4_pwm = data.get("motor4_pwm", 0)

        self._model.timestamp_ms = data.get("timestamp_ms", 0)
        self._model.last_update_time = time.time()
        self._model.packet_count += 1

        # ========== 性能优化：减少信号发射，避免打包后卡顿 ==========
        # 原来：每个数据包发射20+个单独信号（50Hz × 20 = 1000次信号/秒）
        # 现在：只发射关键的批量信号（50Hz × 3 = 150次信号/秒）
        # 性能提升：减少85%的信号处理开销
        
        # 只发射姿态角信号（用于3D视图，已添加节流）
        self.attitude_changed.emit(self._model.roll, self._model.pitch, self._model.yaw)

        # 构建WaveformView需要的数据格式
        waveform_data = {
            # 姿态角
            "roll": self._model.roll,
            "pitch": self._model.pitch,
            "yaw": self._model.yaw,
            # 陀螺仪
            "gyro_x": self._model.gyro_x,
            "gyro_y": self._model.gyro_y,
            "gyro_z": self._model.gyro_z,
            # 加速度
            "acc_x": self._model.acc_x,
            "acc_y": self._model.acc_y,
            "acc_z": self._model.acc_z,
            # 外环输出（期望角速度）
            "roll_rate_desired": self._model.roll_rate_desired,
            "pitch_rate_desired": self._model.pitch_rate_desired,
            "yaw_rate_desired": self._model.yaw_rate_desired,
            # 内环输出（控制量）
            "roll_control": self._model.roll_control_output,
            "pitch_control": self._model.pitch_control_output,
            "yaw_control": self._model.yaw_control_output,
            # 电机PWM
            "motor1": self._model.motor1_pwm,
            "motor2": self._model.motor2_pwm,
            "motor3": self._model.motor3_pwm,
            "motor4": self._model.motor4_pwm,
            # 时间戳
            "timestamp": self._model.timestamp_ms,
        }
        self.high_freq_data_changed.emit(waveform_data)
        self.packet_count_changed.emit(self._model.packet_count)

    def _update_battery_data(self, data: dict):
        """更新电池数据（1Hz）"""
        self._model.battery_voltage = data.get("voltage", 0.0)
        self._model.battery_percentage = data.get("percentage", 0)
        self._model.battery_state = data.get("state_name", "未知")

        self.battery_voltage_changed.emit(self._model.battery_voltage)
        self.battery_percentage_changed.emit(self._model.battery_percentage)
        self.battery_state_changed.emit(self._model.battery_state)

        # 复合信号（用于终端监控）
        self.battery_status_reported.emit(
            self._model.battery_voltage,
            self._model.battery_percentage,
            self._model.battery_state,
        )

    def _update_pid_config_data(self, data: dict):
        """更新PID配置数据（1Hz）"""
        # 角度环
        self._model.angle_roll_kp = data.get("angle_roll_kp", 0.0)
        self._model.angle_roll_ki = data.get("angle_roll_ki", 0.0)
        self._model.angle_roll_kd = data.get("angle_roll_kd", 0.0)
        self._model.angle_pitch_kp = data.get("angle_pitch_kp", 0.0)
        self._model.angle_pitch_ki = data.get("angle_pitch_ki", 0.0)
        self._model.angle_pitch_kd = data.get("angle_pitch_kd", 0.0)
        self._model.angle_yaw_kp = data.get("angle_yaw_kp", 0.0)
        self._model.angle_yaw_ki = data.get("angle_yaw_ki", 0.0)
        self._model.angle_yaw_kd = data.get("angle_yaw_kd", 0.0)

        # 角速度环
        self._model.rate_roll_kp = data.get("rate_roll_kp", 0.0)
        self._model.rate_roll_ki = data.get("rate_roll_ki", 0.0)
        self._model.rate_roll_kd = data.get("rate_roll_kd", 0.0)
        self._model.rate_pitch_kp = data.get("rate_pitch_kp", 0.0)
        self._model.rate_pitch_ki = data.get("rate_pitch_ki", 0.0)
        self._model.rate_pitch_kd = data.get("rate_pitch_kd", 0.0)
        self._model.rate_yaw_kp = data.get("rate_yaw_kp", 0.0)
        self._model.rate_yaw_ki = data.get("rate_yaw_ki", 0.0)
        self._model.rate_yaw_kd = data.get("rate_yaw_kd", 0.0)

        # 发射信号
        self.angle_roll_kp_changed.emit(self._model.angle_roll_kp)
        self.angle_roll_ki_changed.emit(self._model.angle_roll_ki)
        self.angle_roll_kd_changed.emit(self._model.angle_roll_kd)
        self.angle_pitch_kp_changed.emit(self._model.angle_pitch_kp)
        self.angle_pitch_ki_changed.emit(self._model.angle_pitch_ki)
        self.angle_pitch_kd_changed.emit(self._model.angle_pitch_kd)
        self.angle_yaw_kp_changed.emit(self._model.angle_yaw_kp)
        self.angle_yaw_ki_changed.emit(self._model.angle_yaw_ki)
        self.angle_yaw_kd_changed.emit(self._model.angle_yaw_kd)

        self.rate_roll_kp_changed.emit(self._model.rate_roll_kp)
        self.rate_roll_ki_changed.emit(self._model.rate_roll_ki)
        self.rate_roll_kd_changed.emit(self._model.rate_roll_kd)
        self.rate_pitch_kp_changed.emit(self._model.rate_pitch_kp)
        self.rate_pitch_ki_changed.emit(self._model.rate_pitch_ki)
        self.rate_pitch_kd_changed.emit(self._model.rate_pitch_kd)
        self.rate_yaw_kp_changed.emit(self._model.rate_yaw_kp)
        self.rate_yaw_ki_changed.emit(self._model.rate_yaw_ki)
        self.rate_yaw_kd_changed.emit(self._model.rate_yaw_kd)

        # 复合信号（用于终端监控）
        angle_params = {
            "roll": {
                "kp": self._model.angle_roll_kp,
                "ki": self._model.angle_roll_ki,
                "kd": self._model.angle_roll_kd,
            },
            "pitch": {
                "kp": self._model.angle_pitch_kp,
                "ki": self._model.angle_pitch_ki,
                "kd": self._model.angle_pitch_kd,
            },
            "yaw": {
                "kp": self._model.angle_yaw_kp,
                "ki": self._model.angle_yaw_ki,
                "kd": self._model.angle_yaw_kd,
            },
        }
        rate_params = {
            "roll": {
                "kp": self._model.rate_roll_kp,
                "ki": self._model.rate_roll_ki,
                "kd": self._model.rate_roll_kd,
            },
            "pitch": {
                "kp": self._model.rate_pitch_kp,
                "ki": self._model.rate_pitch_ki,
                "kd": self._model.rate_pitch_kd,
            },
            "yaw": {
                "kp": self._model.rate_yaw_kp,
                "ki": self._model.rate_yaw_ki,
                "kd": self._model.rate_yaw_kd,
            },
        }
        self.pid_config_reported.emit(angle_params, rate_params)

    def _update_console_text(self, text: str):
        """更新控制台文本（来自MCU的调试输出）"""
        self.console_text_received.emit(text)

    def reset(self):
        """重置所有数据"""
        self._model.reset()

    def _print_status_monitor(self):
        """打印状态监控（每秒调用一次）"""
        if not self._config_service:
            return

        debug_config = self._config_service.get_debug_config()
        if not debug_config.get("print_rx_drone_status", False):
            return

        # 格式化并打印所有状态
        print("\n" + "=" * 80)
        print("无人机状态监控")
        print("=" * 80)

        # 高频飞行数据（50Hz更新）
        print("\n【高频飞行数据】")
        print(
            f"  姿态角: Roll={self._model.roll:7.2f}°, Pitch={self._model.pitch:7.2f}°, Yaw={self._model.yaw:7.2f}°"
        )
        print(
            f"  角速度: X={self._model.gyro_x:7.2f}°/s, Y={self._model.gyro_y:7.2f}°/s, Z={self._model.gyro_z:7.2f}°/s"
        )
        print(
            f"  加速度: X={self._model.acc_x:7.3f}g, Y={self._model.acc_y:7.3f}g, Z={self._model.acc_z:7.3f}g"
        )
        print(
            f"  期望角速度: Roll={self._model.roll_rate_desired:7.2f}°/s, Pitch={self._model.pitch_rate_desired:7.2f}°/s, Yaw={self._model.yaw_rate_desired:7.2f}°/s"
        )
        print(
            f"  控制输出: Roll={self._model.roll_control_output:6d}, Pitch={self._model.pitch_control_output:6d}, Yaw={self._model.yaw_control_output:6d}"
        )
        print(
            f"  电机PWM: M1={self._model.motor1_pwm:5d}, M2={self._model.motor2_pwm:5d}, M3={self._model.motor3_pwm:5d}, M4={self._model.motor4_pwm:5d}"
        )
        print(
            f"  时间戳: {self._model.timestamp_ms}ms, 包计数: {self._model.packet_count}"
        )

        # 低频状态数据（1Hz更新）
        print("\n【低频状态数据】")
        print(
            f"  电池: 电压={self._model.battery_voltage:.2f}V, 电量={self._model.battery_percentage}%, 状态={self._model.battery_state}"
        )

        # PID配置参数
        print("\n【PID配置参数 - 角度环（外环）】")
        print(
            f"  Roll:  kP={self._model.angle_roll_kp:8.3f}, kI={self._model.angle_roll_ki:8.3f}, kD={self._model.angle_roll_kd:8.3f}"
        )
        print(
            f"  Pitch: kP={self._model.angle_pitch_kp:8.3f}, kI={self._model.angle_pitch_ki:8.3f}, kD={self._model.angle_pitch_kd:8.3f}"
        )
        print(
            f"  Yaw:   kP={self._model.angle_yaw_kp:8.3f}, kI={self._model.angle_yaw_ki:8.3f}, kD={self._model.angle_yaw_kd:8.3f}"
        )

        print("\n【PID配置参数 - 角速度环（内环）】")
        print(
            f"  Roll:  kP={self._model.rate_roll_kp:8.3f}, kI={self._model.rate_roll_ki:8.3f}, kD={self._model.rate_roll_kd:8.3f}"
        )
        print(
            f"  Pitch: kP={self._model.rate_pitch_kp:8.3f}, kI={self._model.rate_pitch_ki:8.3f}, kD={self._model.rate_pitch_kd:8.3f}"
        )
        print(
            f"  Yaw:   kP={self._model.rate_yaw_kp:8.3f}, kI={self._model.rate_yaw_ki:8.3f}, kD={self._model.rate_yaw_kd:8.3f}"
        )

        print("=" * 80 + "\n")
