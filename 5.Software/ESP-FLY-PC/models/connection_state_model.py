"""
ConnectionStateModel - 连接状态模型
存储与ESP32的连接状态信息
"""

from dataclasses import dataclass, field
import time


@dataclass
class ConnectionStateModel:
    """
    连接状态模型
    
    存储UDP连接状态和通信统计信息
    """
    
    # 连接状态
    is_connected: bool = False
    
    # 网络配置
    drone_ip: str = "192.168.43.42"
    port: int = 2390
    local_ip: str = ""
    
    # 通信统计
    sent_packets: int = 0
    recv_packets: int = 0
    send_errors: int = 0
    recv_errors: int = 0
    
    # 信号强度（RSSI，dBm）
    signal_strength: int = 0
    
    # 时间戳
    last_recv_time: float = 0.0
    connect_time: float = 0.0
    
    # 超时设置（秒）
    connection_timeout: float = 10.0
    
    def is_alive(self) -> bool:
        """检查连接是否存活"""
        if not self.is_connected:
            return False
        if self.last_recv_time == 0:
            return True  # 刚连接，还未收到数据
        return (time.time() - self.last_recv_time) < self.connection_timeout
    
    def get_connection_duration(self) -> float:
        """获取连接持续时间（秒）"""
        if not self.is_connected or self.connect_time == 0:
            return 0.0
        return time.time() - self.connect_time
    
    def reset_stats(self):
        """重置统计信息"""
        self.sent_packets = 0
        self.recv_packets = 0
        self.send_errors = 0
        self.recv_errors = 0
    
    def reset(self):
        """重置所有状态"""
        self.is_connected = False
        self.local_ip = ""
        self.reset_stats()
        self.signal_strength = 0
        self.last_recv_time = 0.0
        self.connect_time = 0.0
