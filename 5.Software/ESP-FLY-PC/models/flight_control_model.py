"""
FlightControlModel - 飞行控制参数模型
存储PC发送给ESP32的控制指令参数
"""

from dataclasses import dataclass


@dataclass
class FlightControlModel:
    """
    飞行控制参数模型
    
    存储目标姿态角和油门值，用于生成飞行控制命令（0x01）
    """
    
    # 目标姿态角（度）
    target_roll: float = 0.0
    target_pitch: float = 0.0
    target_yaw: float = 0.0
    
    # 油门值（0-65535）
    thrust: int = 0
    
    # 控制限制参数
    max_angle: float = 30.0      # 最大横滚/俯仰角度
    max_yaw: float = 180.0       # 最大偏航角度
    max_thrust: int = 65535      # 最大油门值
    min_thrust: int = 0          # 最小油门值
    
    # 步进值（用于键盘控制）
    angle_step: float = 1.0      # 角度调整步长
    thrust_step: int = 1000      # 油门调整步长
    
    # 控制状态
    is_enabled: bool = False     # 控制是否启用
    
    def validate_and_clamp(self):
        """验证并限制参数范围"""
        self.target_roll = max(-self.max_angle, min(self.target_roll, self.max_angle))
        self.target_pitch = max(-self.max_angle, min(self.target_pitch, self.max_angle))
        self.target_yaw = max(-self.max_yaw, min(self.target_yaw, self.max_yaw))
        self.thrust = max(self.min_thrust, min(self.thrust, self.max_thrust))
    
    def reset(self):
        """重置控制参数为零"""
        self.target_roll = 0.0
        self.target_pitch = 0.0
        self.target_yaw = 0.0
        self.thrust = 0
    
    def to_dict(self) -> dict:
        """转换为字典（用于发送）"""
        return {
            'roll': self.target_roll,
            'pitch': self.target_pitch,
            'yaw': self.target_yaw,
            'thrust': self.thrust,
        }
