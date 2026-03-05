"""
MotorTestModel - 电机测试模型
存储电机测试相关参数
"""

from dataclasses import dataclass


@dataclass
class MotorTestModel:
    """
    电机测试模型

    用于生成电机测试命令（0x03）发送给ESP32
    """

    # 电机PWM值（0-65535）
    motor1_pwm: int = 0
    motor2_pwm: int = 0
    motor3_pwm: int = 0
    motor4_pwm: int = 0

    # PWM限制
    max_pwm: int = 65535
    min_pwm: int = 0

    def set_motor_pwm(self, motor_id: int, pwm: int):
        """
        设置单个电机PWM

        Args:
            motor_id: 电机ID（1-4）
            pwm: PWM值（0-65535）
        """
        pwm = max(self.min_pwm, min(pwm, self.max_pwm))
        if motor_id == 1:
            self.motor1_pwm = pwm
        elif motor_id == 2:
            self.motor2_pwm = pwm
        elif motor_id == 3:
            self.motor3_pwm = pwm
        elif motor_id == 4:
            self.motor4_pwm = pwm

    def stop_all_motors(self):
        """停止所有电机"""
        self.motor1_pwm = 0
        self.motor2_pwm = 0
        self.motor3_pwm = 0
        self.motor4_pwm = 0

    def has_any_motor_active(self) -> bool:
        """判断是否有任意电机PWM>0"""
        return (
            self.motor1_pwm > 0
            or self.motor2_pwm > 0
            or self.motor3_pwm > 0
            or self.motor4_pwm > 0
        )

    def get_motor_pwm(self, motor_id: int) -> int:
        """获取指定电机的PWM值"""
        if motor_id == 1:
            return self.motor1_pwm
        elif motor_id == 2:
            return self.motor2_pwm
        elif motor_id == 3:
            return self.motor3_pwm
        elif motor_id == 4:
            return self.motor4_pwm
        return 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "motor1": self.motor1_pwm,
            "motor2": self.motor2_pwm,
            "motor3": self.motor3_pwm,
            "motor4": self.motor4_pwm,
        }
