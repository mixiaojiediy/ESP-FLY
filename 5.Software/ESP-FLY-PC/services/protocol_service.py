"""
ProtocolService - 协议服务
负责数据包的解析和构建
"""

import struct
from typing import Optional, Dict, Any
from enum import IntEnum
from dataclasses import dataclass


class PacketType(IntEnum):
    """数据包类型ID"""

    # 上行数据包 (PC → MCU)
    FLIGHT_CONTROL = 0x01  # 飞行控制命令
    PID_CONFIG = 0x02  # PID参数配置
    MOTOR_TEST = 0x03  # 电机测试

    # 下行数据包 (MCU → PC)
    HIGH_FREQ_DATA = 0x81  # 高频飞行数据 (50Hz)
    BATTERY_STATUS = 0x82  # 电池状态 (1Hz)
    PID_RESPONSE = 0x83  # PID参数响应 (1Hz)


@dataclass
class ParsedPacket:
    """解析后的数据包"""

    packet_type: int
    data: Dict[str, Any]

    def get(self, key: str, default=None):
        return self.data.get(key, default)


class ProtocolService:
    """
    协议服务

    职责：
    - 解析接收到的数据包
    - 构建要发送的数据包
    - 校验和计算和验证
    """

    MAX_PAYLOAD_SIZE = 120

    def __init__(self):
        pass

    # ========== 数据包解析 ==========

    def parse_packet(self, raw_data: bytes) -> Optional[ParsedPacket]:
        """
        解析原始数据包

        Args:
            raw_data: 原始字节数据

        Returns:
            ParsedPacket: 解析后的数据包，失败返回None
        """
        if len(raw_data) < 3:
            return None

        packet_id = raw_data[0]
        length = raw_data[1]

        if len(raw_data) < 2 + length + 1:
            return None

        payload = raw_data[2 : 2 + length]
        checksum = raw_data[2 + length]

        # 验证校验和
        calculated_checksum = self._calculate_checksum(packet_id, length, payload)
        if calculated_checksum != checksum:
            return None

        # 根据类型解析
        if packet_id == PacketType.HIGH_FREQ_DATA:
            return self._parse_high_freq_data(payload)
        elif packet_id == PacketType.BATTERY_STATUS:
            return self._parse_battery_status(payload)
        elif packet_id == PacketType.PID_RESPONSE:
            return self._parse_pid_response(payload)
        elif packet_id == PacketType.CONSOLE_LOG:
            return self._parse_console_log(payload)
        elif packet_id == PacketType.HEARTBEAT_RESP:
            return ParsedPacket(PacketType.HEARTBEAT_RESP, {})

        return None

    def _parse_high_freq_data(self, payload: bytes) -> Optional[ParsedPacket]:
        """
        解析高频飞行数据（50Hz）

        Payload结构（64 bytes）:
        - 姿态角: roll, pitch, yaw (3 x float = 12 bytes)
        - 期望角速度: rollRateDesired, pitchRateDesired, yawRateDesired (3 x float = 12 bytes)
        - 控制量: rollControl, pitchControl, yawControl (3 x int16 = 6 bytes)
        - 电机PWM: motor1-4 (4 x uint16 = 8 bytes)
        - 陀螺仪: gyroX, gyroY, gyroZ (3 x float = 12 bytes)
        - 加速度: accX, accY, accZ (3 x float = 12 bytes)
        - 时间戳: timestamp (1 x uint16 = 2 bytes)
        总计: 64 bytes
        """
        if len(payload) < 64:
            return None

        try:
            # 解析数据
            data = struct.unpack("<6f3h4H6fH", payload[:64])

            return ParsedPacket(
                PacketType.HIGH_FREQ_DATA,
                {
                    # 姿态角
                    "roll": data[0],
                    "pitch": data[1],
                    "yaw": data[2],
                    # 期望角速度（外环输出）
                    "roll_rate_desired": data[3],
                    "pitch_rate_desired": data[4],
                    "yaw_rate_desired": data[5],
                    # 控制量（内环输出）
                    "roll_control_output": data[6],
                    "pitch_control_output": data[7],
                    "yaw_control_output": data[8],
                    # 电机PWM
                    "motor1_pwm": data[9],
                    "motor2_pwm": data[10],
                    "motor3_pwm": data[11],
                    "motor4_pwm": data[12],
                    # 陀螺仪
                    "gyro_x": data[13],
                    "gyro_y": data[14],
                    "gyro_z": data[15],
                    # 加速度
                    "acc_x": data[16],
                    "acc_y": data[17],
                    "acc_z": data[18],
                    # 时间戳
                    "timestamp_ms": data[19],
                },
            )
        except struct.error:
            return None

    def _parse_battery_status(self, payload: bytes) -> Optional[ParsedPacket]:
        """
        解析电池状态（1Hz）

        Payload结构（8 bytes）:
        - voltage: float (4 bytes)
        - voltage_mv: uint16 (2 bytes)
        - level: uint8 (1 byte)
        - state: uint8 (1 byte)
        """
        if len(payload) < 8:
            return None

        try:
            voltage, voltage_mv, level, state = struct.unpack("<fHBB", payload[:8])

            state_names = {0: "正常", 1: "充电中", 2: "已充满", 3: "低电量", 4: "关机"}

            return ParsedPacket(
                PacketType.BATTERY_STATUS,
                {
                    "voltage": voltage,
                    "voltage_mv": voltage_mv,
                    "percentage": level,
                    "state": state,
                    "state_name": state_names.get(state, "未知"),
                },
            )
        except struct.error:
            return None

    def _parse_pid_response(self, payload: bytes) -> Optional[ParsedPacket]:
        """
        解析PID参数响应（1Hz）

        Payload结构（72 bytes）:
        - 角度环PID: roll(kp,ki,kd), pitch(kp,ki,kd), yaw(kp,ki,kd) (9 x float = 36 bytes)
        - 角速度环PID: roll(kp,ki,kd), pitch(kp,ki,kd), yaw(kp,ki,kd) (9 x float = 36 bytes)
        总计: 72 bytes
        """
        if len(payload) < 72:
            return None

        try:
            data = struct.unpack("<18f", payload[:72])

            return ParsedPacket(
                PacketType.PID_RESPONSE,
                {
                    # 角度环（外环）
                    "angle_roll_kp": data[0],
                    "angle_roll_ki": data[1],
                    "angle_roll_kd": data[2],
                    "angle_pitch_kp": data[3],
                    "angle_pitch_ki": data[4],
                    "angle_pitch_kd": data[5],
                    "angle_yaw_kp": data[6],
                    "angle_yaw_ki": data[7],
                    "angle_yaw_kd": data[8],
                    # 角速度环（内环）
                    "rate_roll_kp": data[9],
                    "rate_roll_ki": data[10],
                    "rate_roll_kd": data[11],
                    "rate_pitch_kp": data[12],
                    "rate_pitch_ki": data[13],
                    "rate_pitch_kd": data[14],
                    "rate_yaw_kp": data[15],
                    "rate_yaw_ki": data[16],
                    "rate_yaw_kd": data[17],
                },
            )
        except struct.error:
            return None

    def _parse_console_log(self, payload: bytes) -> Optional[ParsedPacket]:
        """解析控制台日志"""
        try:
            text = payload.decode("utf-8", errors="ignore").rstrip("\x00")
            return ParsedPacket(PacketType.CONSOLE_LOG, {"text": text})
        except:
            return None

    # ========== 数据包构建 ==========

    def build_flight_control_packet(
        self, roll: float, pitch: float, yaw: float, thrust: int
    ) -> bytes:
        """
        构建飞行控制数据包（0x01）

        Args:
            roll: 横滚角度（-30.0 ~ +30.0）
            pitch: 俯仰角度（-30.0 ~ +30.0）
            yaw: 偏航角度（-180.0 ~ +180.0）
            thrust: 推力值（0 ~ 65535）

        Returns:
            bytes: 完整数据包
        """
        packet_id = PacketType.FLIGHT_CONTROL
        payload = struct.pack("<3fH", roll, pitch, yaw, thrust)
        return self._build_packet(packet_id, payload)

    def build_pid_config_packet(
        self,
        angle_roll_kp: float,
        angle_roll_ki: float,
        angle_roll_kd: float,
        angle_pitch_kp: float,
        angle_pitch_ki: float,
        angle_pitch_kd: float,
        angle_yaw_kp: float,
        angle_yaw_ki: float,
        angle_yaw_kd: float,
        rate_roll_kp: float,
        rate_roll_ki: float,
        rate_roll_kd: float,
        rate_pitch_kp: float,
        rate_pitch_ki: float,
        rate_pitch_kd: float,
        rate_yaw_kp: float,
        rate_yaw_ki: float,
        rate_yaw_kd: float,
    ) -> bytes:
        """
        构建PID配置数据包（0x02）

        Args:
            角度环和角速度环的18个PID参数

        Returns:
            bytes: 完整数据包（72 bytes payload）
        """
        packet_id = PacketType.PID_CONFIG
        payload = struct.pack(
            "<18f",
            angle_roll_kp,
            angle_roll_ki,
            angle_roll_kd,
            angle_pitch_kp,
            angle_pitch_ki,
            angle_pitch_kd,
            angle_yaw_kp,
            angle_yaw_ki,
            angle_yaw_kd,
            rate_roll_kp,
            rate_roll_ki,
            rate_roll_kd,
            rate_pitch_kp,
            rate_pitch_ki,
            rate_pitch_kd,
            rate_yaw_kp,
            rate_yaw_ki,
            rate_yaw_kd,
        )
        return self._build_packet(packet_id, payload)

    def build_motor_test_packet(
        self, m1_pwm: int, m2_pwm: int, m3_pwm: int, m4_pwm: int, enable: bool
    ) -> bytes:
        """
        构建电机测试数据包（0x03）

        Args:
            m1_pwm: 电机1 PWM值（0-65535）
            m2_pwm: 电机2 PWM值（0-65535）
            m3_pwm: 电机3 PWM值（0-65535）
            m4_pwm: 电机4 PWM值（0-65535）
            enable: 测试使能（True=启用测试, False=停止测试）

        Returns:
            bytes: 完整数据包
        """
        packet_id = PacketType.MOTOR_TEST
        payload = struct.pack(
            "<HHHHB", m1_pwm, m2_pwm, m3_pwm, m4_pwm, 1 if enable else 0
        )
        return self._build_packet(packet_id, payload)

    def build_heartbeat_packet(self) -> bytes:
        """构建心跳包（0x10）"""
        return self._build_packet(PacketType.HEARTBEAT, b"")

    # ========== 辅助方法 ==========

    def _build_packet(self, packet_id: int, payload: bytes) -> bytes:
        """
        构建完整数据包

        Args:
            packet_id: 数据包ID
            payload: 有效载荷

        Returns:
            bytes: PacketID + Length + Payload + Checksum
        """
        length = len(payload)
        checksum = self._calculate_checksum(packet_id, length, payload)
        return bytes([packet_id, length]) + payload + bytes([checksum])

    def _calculate_checksum(self, packet_id: int, length: int, payload: bytes) -> int:
        """
        计算校验和

        Checksum = (PacketID + Length + 所有Payload字节) & 0xFF
        """
        total = packet_id + length + sum(payload)
        return total & 0xFF
