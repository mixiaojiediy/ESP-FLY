"""
DroneStateModel - 无人机状态数据模型
存储从ESP32接收的所有飞行状态数据
"""

from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class DroneStateModel:
    """
    无人机状态数据模型（纯数据类）
    
    包含两类数据：
    - 高频飞行数据（50Hz更新）：姿态、角速度、加速度、PID输出、电机PWM
    - 低频状态数据（1Hz更新）：电池状态、PID配置参数
    """
    
    # ========== 高频飞行数据（50Hz更新）==========
    
    # 姿态角（度）
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    
    # 角速度（度/秒）
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    
    # 加速度（g）
    acc_x: float = 0.0
    acc_y: float = 0.0
    acc_z: float = 0.0
    
    # PID输出（双层控制）
    # 外环：角度环输出 = 期望角速度（作为内环输入）
    roll_rate_desired: float = 0.0
    pitch_rate_desired: float = 0.0
    yaw_rate_desired: float = 0.0
    
    # 内环：角速度环输出 = 控制量
    roll_control_output: int = 0
    pitch_control_output: int = 0
    yaw_control_output: int = 0
    
    # 电机PWM输出（0-65535）
    motor1_pwm: int = 0
    motor2_pwm: int = 0
    motor3_pwm: int = 0
    motor4_pwm: int = 0
    
    # ========== 低频状态数据（1Hz更新）==========
    
    # 电池状态
    battery_voltage: float = 0.0
    battery_percentage: int = 0
    battery_state: str = "未知"
    
    # PID配置参数上报（ESP32 → PC，显示在终端监控）
    # 角度环（外环）PID参数
    angle_roll_kp: float = 0.0
    angle_roll_ki: float = 0.0
    angle_roll_kd: float = 0.0
    angle_pitch_kp: float = 0.0
    angle_pitch_ki: float = 0.0
    angle_pitch_kd: float = 0.0
    angle_yaw_kp: float = 0.0
    angle_yaw_ki: float = 0.0
    angle_yaw_kd: float = 0.0
    
    # 角速度环（内环）PID参数
    rate_roll_kp: float = 0.0
    rate_roll_ki: float = 0.0
    rate_roll_kd: float = 0.0
    rate_pitch_kp: float = 0.0
    rate_pitch_ki: float = 0.0
    rate_pitch_kd: float = 0.0
    rate_yaw_kp: float = 0.0
    rate_yaw_ki: float = 0.0
    rate_yaw_kd: float = 0.0
    
    # ========== 元数据 ==========
    
    # 时间戳（毫秒）
    timestamp_ms: int = 0
    
    # 最后更新时间（用于检测数据新鲜度）
    last_update_time: float = field(default_factory=time.time)
    
    # 接收包计数
    packet_count: int = 0
    
    def is_data_fresh(self, timeout_sec: float = 1.0) -> bool:
        """检查数据是否新鲜（最近接收）"""
        return (time.time() - self.last_update_time) < timeout_sec
    
    def reset(self):
        """重置所有数据为默认值"""
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.acc_z = 0.0
        self.roll_rate_desired = 0.0
        self.pitch_rate_desired = 0.0
        self.yaw_rate_desired = 0.0
        self.roll_control_output = 0
        self.pitch_control_output = 0
        self.yaw_control_output = 0
        self.motor1_pwm = 0
        self.motor2_pwm = 0
        self.motor3_pwm = 0
        self.motor4_pwm = 0
        self.battery_voltage = 0.0
        self.battery_percentage = 0
        self.battery_state = "未知"
        self.timestamp_ms = 0
        self.last_update_time = time.time()
        self.packet_count = 0
