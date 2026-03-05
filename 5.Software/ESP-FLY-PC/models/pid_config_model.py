"""
PidConfigModel - PID配置参数模型
存储PC发送给ESP32的PID配置参数
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class PidAxisConfig:
    """单轴PID配置"""

    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {"kp": self.kp, "ki": self.ki, "kd": self.kd}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PidAxisConfig":
        return cls(
            kp=data.get("kp", 0.0), ki=data.get("ki", 0.0), kd=data.get("kd", 0.0)
        )


@dataclass
class PidConfigModel:
    """
    PID配置模型

    包含6组PID参数：
    - 角度环（外环）：roll, pitch, yaw
    - 角速度环（内环）：roll, pitch, yaw

    用于生成PID配置命令（0x02）发送给ESP32
    """

    # 角度环（外环）PID参数
    angle_roll: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=5.9, ki=2.9, kd=0.0)
    )
    angle_pitch: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=5.9, ki=2.9, kd=0.0)
    )
    angle_yaw: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=6.0, ki=1.0, kd=0.35)
    )

    # 角速度环（内环）PID参数
    rate_roll: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=250.0, ki=500.0, kd=2.5)
    )
    rate_pitch: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=250.0, ki=500.0, kd=2.5)
    )
    rate_yaw: PidAxisConfig = field(
        default_factory=lambda: PidAxisConfig(kp=120.0, ki=16.7, kd=0.0)
    )

    # PID参数范围限制
    kp_min: float = 0.0
    kp_max: float = 1000.0
    ki_min: float = 0.0
    ki_max: float = 1000.0
    kd_min: float = 0.0
    kd_max: float = 100.0

    def get_axis_config(self, loop_type: str, axis: str) -> PidAxisConfig:
        """
        获取指定轴的PID配置

        Args:
            loop_type: 'angle' 或 'rate'
            axis: 'roll', 'pitch', 'yaw'
        """
        attr_name = f"{loop_type}_{axis}"
        return getattr(self, attr_name, PidAxisConfig())

    def set_axis_config(
        self, loop_type: str, axis: str, kp: float, ki: float, kd: float
    ):
        """
        设置指定轴的PID配置

        Args:
            loop_type: 'angle' 或 'rate'
            axis: 'roll', 'pitch', 'yaw'
            kp, ki, kd: PID参数值
        """
        attr_name = f"{loop_type}_{axis}"
        config = getattr(self, attr_name, None)
        if config:
            config.kp = max(self.kp_min, min(kp, self.kp_max))
            config.ki = max(self.ki_min, min(ki, self.ki_max))
            config.kd = max(self.kd_min, min(kd, self.kd_max))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "angle": {
                "roll": self.angle_roll.to_dict(),
                "pitch": self.angle_pitch.to_dict(),
                "yaw": self.angle_yaw.to_dict(),
            },
            "rate": {
                "roll": self.rate_roll.to_dict(),
                "pitch": self.rate_pitch.to_dict(),
                "yaw": self.rate_yaw.to_dict(),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PidConfigModel":
        """从字典创建"""
        model = cls()
        if "angle" in data:
            angle = data["angle"]
            if "roll" in angle:
                model.angle_roll = PidAxisConfig.from_dict(angle["roll"])
            if "pitch" in angle:
                model.angle_pitch = PidAxisConfig.from_dict(angle["pitch"])
            if "yaw" in angle:
                model.angle_yaw = PidAxisConfig.from_dict(angle["yaw"])
        if "rate" in data:
            rate = data["rate"]
            if "roll" in rate:
                model.rate_roll = PidAxisConfig.from_dict(rate["roll"])
            if "pitch" in rate:
                model.rate_pitch = PidAxisConfig.from_dict(rate["pitch"])
            if "yaw" in rate:
                model.rate_yaw = PidAxisConfig.from_dict(rate["yaw"])
        return model

    def to_config_dict(self) -> Dict[str, float]:
        """转换为ConfigService格式的字典"""
        return {
            # PID参数范围
            "pid_p_min": self.kp_min,
            "pid_p_max": self.kp_max,
            "pid_i_min": self.ki_min,
            "pid_i_max": self.ki_max,
            "pid_d_min": self.kd_min,
            "pid_d_max": self.kd_max,
            # 角速度环（内环）
            "rate_roll_p": self.rate_roll.kp,
            "rate_roll_i": self.rate_roll.ki,
            "rate_roll_d": self.rate_roll.kd,
            "rate_pitch_p": self.rate_pitch.kp,
            "rate_pitch_i": self.rate_pitch.ki,
            "rate_pitch_d": self.rate_pitch.kd,
            "rate_yaw_p": self.rate_yaw.kp,
            "rate_yaw_i": self.rate_yaw.ki,
            "rate_yaw_d": self.rate_yaw.kd,
            # 角度环（外环）
            "angle_roll_p": self.angle_roll.kp,
            "angle_roll_i": self.angle_roll.ki,
            "angle_roll_d": self.angle_roll.kd,
            "angle_pitch_p": self.angle_pitch.kp,
            "angle_pitch_i": self.angle_pitch.ki,
            "angle_pitch_d": self.angle_pitch.kd,
            "angle_yaw_p": self.angle_yaw.kp,
            "angle_yaw_i": self.angle_yaw.ki,
            "angle_yaw_d": self.angle_yaw.kd,
        }

    @classmethod
    def from_config_dict(cls, config_dict: Dict[str, float]) -> "PidConfigModel":
        """从ConfigService格式的字典创建"""
        model = cls()

        # 设置PID参数范围
        if "pid_p_min" in config_dict:
            model.kp_min = config_dict["pid_p_min"]
        if "pid_p_max" in config_dict:
            model.kp_max = config_dict["pid_p_max"]
        if "pid_i_min" in config_dict:
            model.ki_min = config_dict["pid_i_min"]
        if "pid_i_max" in config_dict:
            model.ki_max = config_dict["pid_i_max"]
        if "pid_d_min" in config_dict:
            model.kd_min = config_dict["pid_d_min"]
        if "pid_d_max" in config_dict:
            model.kd_max = config_dict["pid_d_max"]

        # 设置角速度环（内环）参数
        if "rate_roll_p" in config_dict:
            model.rate_roll.kp = config_dict["rate_roll_p"]
        if "rate_roll_i" in config_dict:
            model.rate_roll.ki = config_dict["rate_roll_i"]
        if "rate_roll_d" in config_dict:
            model.rate_roll.kd = config_dict["rate_roll_d"]
        if "rate_pitch_p" in config_dict:
            model.rate_pitch.kp = config_dict["rate_pitch_p"]
        if "rate_pitch_i" in config_dict:
            model.rate_pitch.ki = config_dict["rate_pitch_i"]
        if "rate_pitch_d" in config_dict:
            model.rate_pitch.kd = config_dict["rate_pitch_d"]
        if "rate_yaw_p" in config_dict:
            model.rate_yaw.kp = config_dict["rate_yaw_p"]
        if "rate_yaw_i" in config_dict:
            model.rate_yaw.ki = config_dict["rate_yaw_i"]
        if "rate_yaw_d" in config_dict:
            model.rate_yaw.kd = config_dict["rate_yaw_d"]

        # 设置角度环（外环）参数
        if "angle_roll_p" in config_dict:
            model.angle_roll.kp = config_dict["angle_roll_p"]
        if "angle_roll_i" in config_dict:
            model.angle_roll.ki = config_dict["angle_roll_i"]
        if "angle_roll_d" in config_dict:
            model.angle_roll.kd = config_dict["angle_roll_d"]
        if "angle_pitch_p" in config_dict:
            model.angle_pitch.kp = config_dict["angle_pitch_p"]
        if "angle_pitch_i" in config_dict:
            model.angle_pitch.ki = config_dict["angle_pitch_i"]
        if "angle_pitch_d" in config_dict:
            model.angle_pitch.kd = config_dict["angle_pitch_d"]
        if "angle_yaw_p" in config_dict:
            model.angle_yaw.kp = config_dict["angle_yaw_p"]
        if "angle_yaw_i" in config_dict:
            model.angle_yaw.ki = config_dict["angle_yaw_i"]
        if "angle_yaw_d" in config_dict:
            model.angle_yaw.kd = config_dict["angle_yaw_d"]

        return model

    def reset_to_default(self):
        """重置为默认值"""
        self.angle_roll = PidAxisConfig(kp=5.9, ki=2.9, kd=0.0)
        self.angle_pitch = PidAxisConfig(kp=5.9, ki=2.9, kd=0.0)
        self.angle_yaw = PidAxisConfig(kp=6.0, ki=1.0, kd=0.35)
        self.rate_roll = PidAxisConfig(kp=250.0, ki=500.0, kd=2.5)
        self.rate_pitch = PidAxisConfig(kp=250.0, ki=500.0, kd=2.5)
        self.rate_yaw = PidAxisConfig(kp=120.0, ki=16.7, kd=0.0)
