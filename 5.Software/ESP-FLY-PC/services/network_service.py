"""
NetworkService - 网络通信服务
负责UDP通信的连接、发送、接收
"""

import socket
import threading
import time
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal


class NetworkService(QObject):
    """
    网络通信服务
    
    职责：
    - UDP Socket管理
    - 数据包发送
    - 数据包接收（独立线程）
    - 连接状态管理
    
    信号：
    - data_received: 接收到数据时发射
    - connected: 连接成功时发射
    - disconnected: 断开连接时发射
    - error_occurred: 发生错误时发射
    - stats_updated: 统计信息更新时发射
    """
    
    # 信号定义
    data_received = pyqtSignal(bytes)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    stats_updated = pyqtSignal(int, int)  # sent_count, recv_count
    
    # 默认配置
    DEFAULT_DRONE_IP = "192.168.43.42"
    DEFAULT_LOCAL_PORT = 2399   # 本地监听端口（接收设备广播）
    DEFAULT_DEVICE_PORT = 2390  # 设备端口（发送命令）
    DEFAULT_PORT = 2390         # 保留兼容性
    BUFFER_SIZE = 128
    RECV_TIMEOUT = 0.1  # 接收超时（秒）
    
    def __init__(self, drone_ip: str = None, port: int = None, config_service=None):
        super().__init__()
        
        self._drone_ip = drone_ip or self.DEFAULT_DRONE_IP
        
        # ConfigService（可选）
        self._config_service = config_service
        
        # 读取新配置，如果没有则使用旧的 port 参数（兼容性）
        if config_service:
            self._local_port = config_service.get_int("network", "local_port", self.DEFAULT_LOCAL_PORT)
            self._device_port = config_service.get_int("network", "device_port", self.DEFAULT_DEVICE_PORT)
        else:
            self._local_port = self.DEFAULT_LOCAL_PORT
            self._device_port = port or self.DEFAULT_DEVICE_PORT
        
        # 保留旧的 _port 变量用于发送（向后兼容）
        self._port = self._device_port
        
        # Socket
        self._socket: Optional[socket.socket] = None
        
        # 状态
        self._is_connected = False
        self._is_running = False
        self._local_ip = ""
        
        # 线程
        self._recv_thread: Optional[threading.Thread] = None
        
        # 统计
        self._sent_packets = 0
        self._recv_packets = 0
        self._send_errors = 0
        self._recv_errors = 0
        self._last_recv_time = 0.0
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def local_ip(self) -> str:
        return self._local_ip
    
    @property
    def drone_ip(self) -> str:
        return self._drone_ip
    
    @property
    def port(self) -> int:
        return self._port
    
    @property
    def sent_packets(self) -> int:
        return self._sent_packets
    
    @property
    def recv_packets(self) -> int:
        return self._recv_packets
    
    @property
    def last_recv_time(self) -> float:
        return self._last_recv_time
    
    def connect(self) -> bool:
        """
        连接到无人机
        
        Returns:
            bool: 连接是否成功
        """
        if self._is_connected:
            return True
        
        try:
            # 创建UDP Socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.RECV_TIMEOUT)
            
            # 设置socket选项
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 获取本机IP
            self._local_ip = self._get_local_ip()
            
            # 绑定本地端口用于接收广播数据
            if self._local_ip:
                bind_addr = (self._local_ip, self._local_port)
            else:
                bind_addr = ("", self._local_port)
            
            self._socket.bind(bind_addr)
            print(f"[NetworkService] 绑定到本地端口 {self._local_port} 接收数据")
            print(f"[NetworkService] 将发送命令到设备 {self._drone_ip}:{self._device_port}")
            
            # 启动接收线程
            self._is_running = True
            self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._recv_thread.start()
            
            # 标记为已连接
            self._is_connected = True
            self._last_recv_time = 0.0
            
            # 等待网络栈准备就绪
            time.sleep(0.3)
            
            self.connected.emit()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """断开连接"""
        if not self._is_connected and not self._is_running:
            return
        
        # 停止接收线程
        self._is_running = False
        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=1.0)
        
        # 关闭Socket
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        
        self._is_connected = False
        self._last_recv_time = 0.0
        
        self.disconnected.emit()
    
    def send_packet(self, data: bytes) -> bool:
        """
        发送数据包
        
        Args:
            data: 要发送的字节数据
            
        Returns:
            bool: 是否发送成功
        """
        if not self._is_connected or not self._socket:
            return False
        
        try:
            sent_bytes = self._socket.sendto(data, (self._drone_ip, self._device_port))
            if sent_bytes > 0:
                self._sent_packets += 1
                # 发射统计更新信号
                self.stats_updated.emit(self._sent_packets, self._recv_packets)
                return True
            else:
                self._send_errors += 1
                return False
        except Exception as e:
            self._send_errors += 1
            self.error_occurred.emit(f"发送失败: {e}")
            return False
    
    def _receive_loop(self):
        """接收循环（在独立线程中运行）"""
        while self._is_running:
            try:
                data, addr = self._socket.recvfrom(self.BUFFER_SIZE)
                
                if data:
                    # 只接收来自目标设备IP的数据包
                    if addr[0] != self._drone_ip:
                        continue
                    
                    # 打印原始数据包（如果配置启用）
                    if self._config_service:
                        debug_config = self._config_service.get_debug_config()
                        if debug_config.get('print_rx_raw_packets', False):
                            hex_str = ' '.join(f'{b:02x}' for b in data)
                            print(f'[RAW] len={len(data)}: {hex_str}')
                    
                    self._last_recv_time = time.time()
                    self._recv_packets += 1
                    
                    # 发射数据接收信号
                    self.data_received.emit(data)
                    # 发射统计更新信号
                    self.stats_updated.emit(self._sent_packets, self._recv_packets)
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self._is_running:
                    self._recv_errors += 1
                    self.error_occurred.emit(f"接收错误: {e}")
                break
    
    def _get_local_ip(self) -> str:
        """获取192.168.43.x网段的本机IP"""
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get("addr")
                        if ip and ip.startswith("192.168.43."):
                            return ip
        except ImportError:
            # netifaces不可用，尝试连接获取
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                temp_socket.connect((self._drone_ip, self._port))
                local_ip = temp_socket.getsockname()[0]
                temp_socket.close()
                if local_ip.startswith("192.168.43."):
                    return local_ip
            except:
                pass
        except Exception:
            pass
        
        return ""
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'sent_packets': self._sent_packets,
            'recv_packets': self._recv_packets,
            'send_errors': self._send_errors,
            'recv_errors': self._recv_errors,
            'last_recv_time': self._last_recv_time,
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self._sent_packets = 0
        self._recv_packets = 0
        self._send_errors = 0
        self._recv_errors = 0
    
    def __del__(self):
        """析构函数"""
        self.disconnect()
