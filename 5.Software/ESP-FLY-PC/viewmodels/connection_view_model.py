"""
ConnectionViewModel - 连接管理ViewModel
管理与ESP32的连接状态
"""

import socket
import subprocess
import re
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from models.connection_state_model import ConnectionStateModel
from services.network_service import NetworkService


class ConnectionViewModel(QObject):
    """
    连接管理ViewModel

    职责：
    - 管理ConnectionStateModel数据
    - 处理连接/断开操作
    - 监控连接状态和通信统计
    - 发射属性变化信号供View绑定
    """

    # Property Changed信号
    is_connected_changed = pyqtSignal(bool)
    local_ip_changed = pyqtSignal(str)
    signal_strength_changed = pyqtSignal(int)

    # 统计信号
    sent_packets_changed = pyqtSignal(int)
    recv_packets_changed = pyqtSignal(int)
    stats_changed = pyqtSignal(int, int)  # sent, recv

    # 事件信号
    connection_error = pyqtSignal(str)

    def __init__(self, network_service: NetworkService):
        super().__init__()

        # Model
        self._model = ConnectionStateModel()

        # Service
        self._network_service = network_service

        # 连接NetworkService信号
        self._network_service.connected.connect(self._on_connected)
        self._network_service.disconnected.connect(self._on_disconnected)
        self._network_service.error_occurred.connect(self._on_error)

        # WiFi信号强度刷新定时器（2秒间隔）
        self._signal_refresh_timer = QTimer()
        self._signal_refresh_timer.timeout.connect(self.refresh_signal_command)

    # ========== Properties ==========

    @property
    def is_connected(self) -> bool:
        return self._model.is_connected

    @property
    def drone_ip(self) -> str:
        return self._model.drone_ip

    @property
    def port(self) -> int:
        return self._model.port

    @property
    def local_ip(self) -> str:
        return self._model.local_ip

    @property
    def signal_strength(self) -> int:
        return self._model.signal_strength

    @property
    def sent_packets(self) -> int:
        return self._network_service.sent_packets

    @property
    def recv_packets(self) -> int:
        return self._network_service.recv_packets

    # ========== Commands ==========

    @pyqtSlot()
    def connect_command(self) -> bool:
        """连接命令"""
        if self._model.is_connected:
            return True

        # 检查网络
        network_ok, local_ip = self._check_network()
        if not network_ok:
            self.connection_error.emit(
                f"网络检查失败\n当前IP: {local_ip}\n请先连接到ESP32的WiFi热点"
            )
            # 网络检查失败，直接返回，不继续连接
            return False

        # 连接
        success = self._network_service.connect()
        return success

    @pyqtSlot()
    def disconnect_command(self):
        """断开连接命令"""
        if not self._model.is_connected:
            return

        self._network_service.disconnect()

    @pyqtSlot()
    def refresh_signal_command(self):
        """刷新信号强度命令"""
        rssi = self._get_wifi_signal_strength()
        if self._model.signal_strength != rssi:
            self._model.signal_strength = rssi
            self.signal_strength_changed.emit(rssi)

    @pyqtSlot()
    def refresh_stats_command(self):
        """刷新统计信息命令"""
        sent = self._network_service.sent_packets
        recv = self._network_service.recv_packets
        self.sent_packets_changed.emit(sent)
        self.recv_packets_changed.emit(recv)
        self.stats_changed.emit(sent, recv)

    @pyqtSlot(int, int)
    def on_stats_updated(self, sent_count: int, recv_count: int):
        """处理NetworkService统计更新"""
        self.sent_packets_changed.emit(sent_count)
        self.recv_packets_changed.emit(recv_count)
        self.stats_changed.emit(sent_count, recv_count)

    # ========== Private Event Handlers ==========

    def _on_connected(self):
        """连接成功"""
        self._model.is_connected = True
        self._model.local_ip = self._network_service.local_ip

        self.is_connected_changed.emit(True)
        self.local_ip_changed.emit(self._model.local_ip)

        # 启动WiFi信号强度刷新定时器（2秒间隔）
        self._signal_refresh_timer.start(2000)
        # 立即刷新一次信号强度
        self.refresh_signal_command()

    def _on_disconnected(self):
        """断开连接"""
        # 停止WiFi信号强度刷新定时器
        self._signal_refresh_timer.stop()

        self._model.is_connected = False
        self._model.reset()

        self.is_connected_changed.emit(False)

    def _on_error(self, error_msg: str):
        """错误处理"""
        self.connection_error.emit(error_msg)

    # ========== Private Methods ==========

    def _check_network(self) -> tuple:
        """检查网络连接状态"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            try:
                s.connect(("192.168.43.42", 80))
                local_ip = s.getsockname()[0]
            except:
                local_ip = socket.gethostbyname(socket.gethostname())
            finally:
                s.close()

            # 检查是否在正确的网段
            if local_ip.startswith("192.168.43."):
                return True, local_ip
            else:
                return False, local_ip
        except Exception:
            return False, "未知"

    def _get_wifi_signal_strength(self) -> int:
        """获取ESP-DRONE WiFi信号强度（RSSI）"""
        try:
            # ========== 修复：隐藏命令行窗口 ==========
            # 在Windows上使用CREATE_NO_WINDOW标志防止terminal闪现
            import sys
            startupinfo = None
            creation_flags = 0
            
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=Bssid"],
                capture_output=True,
                text=False,
                timeout=3,
                startupinfo=startupinfo,
                creationflags=creation_flags,
            )

            if result.returncode == 0:
                try:
                    import locale

                    encoding = locale.getpreferredencoding()
                    output = result.stdout.decode(encoding, errors="ignore")
                except:
                    output = result.stdout.decode("utf-8", errors="ignore")

                lines = output.split("\n")
                found_esp_drone = False

                for i, line in enumerate(lines):
                    ssid_match = re.search(
                        r"SSID\s+\d+\s*:\s*(.+)", line, re.IGNORECASE
                    )
                    if ssid_match:
                        ssid = ssid_match.group(1).strip()
                        if ssid.startswith("ESP-DRONE"):
                            found_esp_drone = True
                            for j in range(i + 1, min(i + 15, len(lines))):
                                next_line = lines[j]
                                if next_line.strip() and ":" in next_line:
                                    percent_match = re.search(r":\s*(\d+)%", next_line)
                                    if percent_match:
                                        percentage = int(percent_match.group(1))
                                        rssi = int(-30 - (100 - percentage) * 0.6)
                                        return rssi
                            break
        except Exception:
            pass

        return 0
