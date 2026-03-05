"""
TerminalView - 终端监控面板
显示PID参数、电池信息和MCU调试输出
"""

import time
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor, QFont


class TerminalView(QWidget):
    """
    终端监控面板View
    
    类似控制台的文本显示，用于显示：
    - PID参数上报（1Hz）
    - 电池状态信息（1Hz）
    - MCU调试输出
    """
    
    # 用户操作信号
    clear_requested = pyqtSignal()
    
    def __init__(self, max_lines: int = 100, parent=None):
        super().__init__(parent)
        
        # 消息缓冲区
        self._max_lines = max_lines
        self._message_buffer = deque(maxlen=max_lines)
        
        # 标记是否需要刷新
        self._needs_refresh = False
        
        self._init_ui()
        
        # 定时刷新显示（100ms）
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_display)
        self._refresh_timer.start(100)
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建文本编辑器
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont('Consolas', 10))
        
        # 设置样式 - 黑底绿字
        self._text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #333;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        
        layout.addWidget(self._text_edit)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("清空终端")
        clear_btn.clicked.connect(self._on_clear_clicked)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 显示欢迎信息
        self._append_message("=== ESP-FLY 终端监控窗口 ===")
        self._append_message("等待数据接收...")
        self._append_message("")
    
    def _append_message(self, message: str, with_timestamp: bool = True):
        """
        添加消息到缓冲区
        
        Args:
            message: 要显示的消息
            with_timestamp: 是否添加时间戳
        """
        if with_timestamp:
            timestamp = time.strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {message}"
        else:
            formatted_msg = message
        
        self._message_buffer.append(formatted_msg)
        self._needs_refresh = True
    
    def _on_clear_clicked(self):
        """清空按钮点击"""
        self.clear_terminal()
        self.clear_requested.emit()
    
    def _refresh_display(self):
        """刷新显示（定时调用）"""
        if not self._needs_refresh:
            return
        
        self._needs_refresh = False
        
        # 将缓冲区内容显示到文本编辑器
        self._text_edit.clear()
        for msg in self._message_buffer:
            self._text_edit.append(msg)
        
        # 自动滚动到底部
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._text_edit.setTextCursor(cursor)
    
    # ========== Data Binding Slots ==========
    
    @pyqtSlot(dict, dict)
    def update_pid_params(self, angle_params: dict, rate_params: dict):
        """
        更新PID参数显示（1Hz，来自DroneViewModel）
        
        Args:
            angle_params: 角度环PID参数
                {
                    'roll': {'kp': 3.5, 'ki': 0.0, 'kd': 0.0},
                    'pitch': {'kp': 3.5, 'ki': 0.0, 'kd': 0.0},
                    'yaw': {'kp': 10.0, 'ki': 1.0, 'kd': 0.35}
                }
            rate_params: 角速度环PID参数（同样格式）
        """
        if not angle_params and not rate_params:
            return
        
        # 角度环参数
        if angle_params:
            self._append_message("--- 角度环PID参数 ---")
            for axis in ['roll', 'pitch', 'yaw']:
                if axis in angle_params:
                    values = angle_params[axis]
                    kp = values.get('kp', 0.0)
                    ki = values.get('ki', 0.0)
                    kd = values.get('kd', 0.0)
                    self._append_message(
                        f"  {axis.upper():6s}: kP={kp:8.3f}, kI={ki:8.3f}, kD={kd:8.3f}",
                        with_timestamp=False
                    )
        
        # 角速度环参数
        if rate_params:
            self._append_message("--- 角速度环PID参数 ---")
            for axis in ['roll', 'pitch', 'yaw']:
                if axis in rate_params:
                    values = rate_params[axis]
                    kp = values.get('kp', 0.0)
                    ki = values.get('ki', 0.0)
                    kd = values.get('kd', 0.0)
                    self._append_message(
                        f"  {axis.upper():6s}: kP={kp:8.3f}, kI={ki:8.3f}, kD={kd:8.3f}",
                        with_timestamp=False
                    )
    
    @pyqtSlot(float, int, str)
    def update_battery_info(self, voltage: float, percentage: int, state: str):
        """
        更新电池信息（1Hz）
        
        Args:
            voltage: 电池电压（V）
            percentage: 电量百分比
            state: 电池状态字符串
        """
        # 判断充放电状态
        if state in ['充电中', 'charging']:
            charge_status = "充电中"
        else:
            charge_status = "放电中"
        
        self._append_message(
            f"[电量] 电压: {voltage:.2f}V, 电量: {percentage}%, 状态: {state} ({charge_status})"
        )
    
    @pyqtSlot(str)
    def update_console_text(self, text: str):
        """
        显示MCU调试输出（来自0x86包）
        
        Args:
            text: 控制台文本
        """
        if text:
            # MCU输出可能已包含时间戳，不再添加
            self._message_buffer.append(text)
            self._needs_refresh = True
    
    @pyqtSlot()
    def clear_terminal(self):
        """清空终端"""
        self._message_buffer.clear()
        self._text_edit.clear()
        self._append_message("=== 终端已清空 ===")
    
    @pyqtSlot(str)
    def append_info(self, message: str):
        """
        添加普通信息消息
        
        Args:
            message: 消息内容
        """
        self._append_message(f"[INFO] {message}")
    
    @pyqtSlot(str)
    def append_warning(self, message: str):
        """
        添加警告消息
        
        Args:
            message: 消息内容
        """
        self._append_message(f"[WARN] {message}")
    
    @pyqtSlot(str)
    def append_error(self, message: str):
        """
        添加错误消息
        
        Args:
            message: 消息内容
        """
        self._append_message(f"[ERROR] {message}")
    
    def get_all_messages(self) -> list:
        """获取所有消息"""
        return list(self._message_buffer)
