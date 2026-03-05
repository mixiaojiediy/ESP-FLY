"""
WaveformView - 波形显示面板
显示19条独立的实时曲线，分6个页签显示
"""

import time
from collections import deque
from functools import partial
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot
import pyqtgraph as pg
import numpy as np
import logging

# ========== 性能日志配置（已禁用） ==========
# 如需启用日志，取消下面的注释
# logging.basicConfig(
#     level=logging.WARNING,  # 只记录警告和错误
#     format='[%(asctime)s.%(msecs)03d] %(levelname)s - %(message)s',
#     datefmt='%H:%M:%S',
#     handlers=[
#         logging.StreamHandler()  # 只输出到控制台，不生成文件
#     ]
# )
# logger = logging.getLogger(__name__)

# 创建一个空的logger，不输出任何日志
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.CRITICAL + 1)  # 禁用所有级别的日志


class WaveformView(QWidget):
    """
    波形显示面板View
    
    显示19条独立曲线：
    - 姿态角：roll, pitch, yaw
    - 电机PWM：motor1-4
    - 角度PID输出：roll_rate_desired, pitch_rate_desired, yaw_rate_desired
    - 角速度PID输出：roll_control, pitch_control, yaw_control
    - 陀螺仪：gyro_x, gyro_y, gyro_z
    - 加速度计：acc_x, acc_y, acc_z
    """
    
    # 用户操作信号
    clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ========== 性能优化：刷新控制 ==========
        # 降低刷新频率，避免打包后卡顿
        self._last_refresh_time = 0
        self._refresh_interval = 1.0 / 20.0  # 20fps（从30fps降低到20fps）
        
        # 性能监控
        self._refresh_count = 0
        self._total_refresh_time = 0
        self._max_refresh_time = 0
        
        logger.info("=== WaveformView 初始化 ===")
        logger.info(f"刷新间隔: {self._refresh_interval*1000:.1f}ms (20fps)")
        
        # 时间戳处理（处理2字节时间戳溢出）
        self._last_raw_timestamp = None
        self._timestamp_offset = 0.0
        self._base_timestamp = None  # 基准时间戳，用于实现从0开始显示
        
        # X轴同步缩放控制
        self._sync_lock = False  # 同步锁，防止递归触发
        self._tab_groups = {}  # 页签分组字典，记录每个页签包含的图表列表
        
        # 曲线字典
        self._curves = {}
        
        self._init_ui()
        
        # 启动定时刷新（性能优化：降低刷新频率）
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_all_curves)
        self._refresh_timer.start(50)  # 20fps（50ms），从30fps降低到20fps
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建页签控件
        self._tab_widget = QTabWidget()
        
        # 页签1: 姿态角 (Attitude) - 3条曲线
        tab1_widget, tab1_layout = self._create_tab_container()
        self._curves["roll"] = self._create_plot(
            "Roll - 横滚角 (度)", "red", tab1_layout
        )
        self._curves["pitch"] = self._create_plot(
            "Pitch - 俯仰角 (度)", "green", tab1_layout
        )
        self._curves["yaw"] = self._create_plot(
            "Yaw - 偏航角 (度)", "blue", tab1_layout
        )
        tab1_layout.addStretch()
        self._tab_widget.addTab(tab1_widget, "姿态角")
        tab1_plots = ["roll", "pitch", "yaw"]
        self._tab_groups["姿态角"] = tab1_plots
        self._setup_x_axis_sync(tab1_plots)
        
        # 页签2: 电机PWM (Motor PWM) - 4条曲线
        tab2_widget, tab2_layout = self._create_tab_container()
        self._curves["motor1"] = self._create_plot("Motor 1 PWM", "cyan", tab2_layout)
        self._curves["motor2"] = self._create_plot("Motor 2 PWM", "magenta", tab2_layout)
        self._curves["motor3"] = self._create_plot("Motor 3 PWM", "yellow", tab2_layout)
        self._curves["motor4"] = self._create_plot("Motor 4 PWM", "white", tab2_layout)
        tab2_layout.addStretch()
        self._tab_widget.addTab(tab2_widget, "电机PWM")
        tab2_plots = ["motor1", "motor2", "motor3", "motor4"]
        self._tab_groups["电机PWM"] = tab2_plots
        self._setup_x_axis_sync(tab2_plots)
        
        # 页签3: 角度PID输出 (Attitude PID) - 3条曲线
        tab3_widget, tab3_layout = self._create_tab_container()
        self._curves["roll_rate_desired"] = self._create_plot(
            "Roll Rate Desired (度/秒)", "red", tab3_layout
        )
        self._curves["pitch_rate_desired"] = self._create_plot(
            "Pitch Rate Desired (度/秒)", "green", tab3_layout
        )
        self._curves["yaw_rate_desired"] = self._create_plot(
            "Yaw Rate Desired (度/秒)", "blue", tab3_layout
        )
        tab3_layout.addStretch()
        self._tab_widget.addTab(tab3_widget, "角度PID输出")
        tab3_plots = ["roll_rate_desired", "pitch_rate_desired", "yaw_rate_desired"]
        self._tab_groups["角度PID输出"] = tab3_plots
        self._setup_x_axis_sync(tab3_plots)
        
        # 页签4: 角速度PID输出 (Rate PID) - 3条曲线
        tab4_widget, tab4_layout = self._create_tab_container()
        self._curves["roll_control"] = self._create_plot(
            "Roll Control", "red", tab4_layout
        )
        self._curves["pitch_control"] = self._create_plot(
            "Pitch Control", "green", tab4_layout
        )
        self._curves["yaw_control"] = self._create_plot(
            "Yaw Control", "blue", tab4_layout
        )
        tab4_layout.addStretch()
        self._tab_widget.addTab(tab4_widget, "角速度PID输出")
        tab4_plots = ["roll_control", "pitch_control", "yaw_control"]
        self._tab_groups["角速度PID输出"] = tab4_plots
        self._setup_x_axis_sync(tab4_plots)
        
        # 页签5: 陀螺仪数据 (Gyroscope) - 3条曲线
        tab5_widget, tab5_layout = self._create_tab_container()
        self._curves["gyro_x"] = self._create_plot("Gyro X (度/秒)", "red", tab5_layout)
        self._curves["gyro_y"] = self._create_plot("Gyro Y (度/秒)", "green", tab5_layout)
        self._curves["gyro_z"] = self._create_plot("Gyro Z (度/秒)", "blue", tab5_layout)
        tab5_layout.addStretch()
        self._tab_widget.addTab(tab5_widget, "陀螺仪")
        tab5_plots = ["gyro_x", "gyro_y", "gyro_z"]
        self._tab_groups["陀螺仪"] = tab5_plots
        self._setup_x_axis_sync(tab5_plots)
        
        # 页签6: 加速度计数据 (Accelerometer) - 3条曲线
        tab6_widget, tab6_layout = self._create_tab_container()
        self._curves["acc_x"] = self._create_plot("Acc X (m/s²)", "red", tab6_layout)
        self._curves["acc_y"] = self._create_plot("Acc Y (m/s²)", "green", tab6_layout)
        self._curves["acc_z"] = self._create_plot("Acc Z (m/s²)", "blue", tab6_layout)
        tab6_layout.addStretch()
        self._tab_widget.addTab(tab6_widget, "加速度计")
        tab6_plots = ["acc_x", "acc_y", "acc_z"]
        self._tab_groups["加速度计"] = tab6_plots
        self._setup_x_axis_sync(tab6_plots)
        
        layout.addWidget(self._tab_widget)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("清空波形")
        clear_btn.clicked.connect(self._on_clear_clicked)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _create_tab_container(self) -> tuple:
        """
        创建页签的容器widget和布局
        
        Returns:
            tuple: (QWidget容器, QVBoxLayout布局)
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        return widget, layout
    
    def _create_plot(self, title: str, color: str, layout: QVBoxLayout) -> dict:
        """
        创建单条曲线图表
        
        Args:
            title: 图表标题
            color: 曲线颜色
            layout: 要添加到的布局
        
        Returns:
            dict: {'widget': PlotWidget, 'curve': PlotDataItem, 'buffer': deque}
        """
        # 创建PlotWidget
        plot_widget = pg.PlotWidget()
        plot_widget.setTitle(title, color="w", size="12pt")
        plot_widget.setLabel("bottom", "时间", units="s", color="w")
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.setMinimumHeight(150)
        
        # 设置背景色
        plot_widget.setBackground("#1a1a1a")
        
        # 启用自动缩放
        plot_widget.enableAutoRange(axis="x", enable=True)
        plot_widget.enableAutoRange(axis="y", enable=True)
        plot_widget.setAutoVisible(y=True)
        
        # 禁用Y轴鼠标缩放/拖动，确保Y轴始终处于自动缩放状态
        plot_widget.setMouseEnabled(x=True, y=False)
        
        # 创建曲线
        curve = plot_widget.plot(pen=pg.mkPen(color, width=2))
        
        # 数据缓冲区（30000个点，50Hz下约10分钟）
        data_buffer = deque(maxlen=30000)
        
        # 添加到布局
        layout.addWidget(plot_widget)
        
        return {"widget": plot_widget, "curve": curve, "buffer": data_buffer}
    
    def _setup_x_axis_sync(self, tab_plots: list):
        """
        为同一页签的图表设置X轴同步缩放
        
        Args:
            tab_plots: 同一页签的图表key列表
        """
        for source_key in tab_plots:
            plot_widget = self._curves[source_key]["widget"]
            vb = plot_widget.getViewBox()
            
            # 连接范围变化信号
            vb.sigRangeChanged.connect(
                partial(self._on_x_range_changed, source_key, tab_plots)
            )
    
    def _on_x_range_changed(self, source_key: str, tab_plots: list):
        """
        X轴范围变化回调函数
        
        Args:
            source_key: 触发变化的图表key
            tab_plots: 同一页签的图表key列表
        """
        # 使用同步锁避免递归触发
        if self._sync_lock:
            return
        
        self._sync_lock = True
        try:
            # 获取源图表的X轴范围
            source_vb = self._curves[source_key]["widget"].getViewBox()
            x_range = source_vb.viewRange()[0]
            
            # 同步到同组其他图表
            for key in tab_plots:
                if key != source_key and key in self._curves:
                    target_vb = self._curves[key]["widget"].getViewBox()
                    target_vb.setXRange(x_range[0], x_range[1], padding=0)
        finally:
            self._sync_lock = False
    
    def _process_timestamp(self, raw_ts: int) -> float:
        """
        处理uint16时间戳溢出
        
        Args:
            raw_ts: 原始时间戳（uint16，单位ms）
        
        Returns:
            float: 连续相对时间（秒，从0开始）
        """
        if raw_ts is None:
            # 如果没有时间戳，使用本地时间
            if self._base_timestamp is None:
                self._base_timestamp = time.time()
            return time.time() - self._base_timestamp
        
        # 处理uint16时间戳溢出（65535 -> 0）
        if self._last_raw_timestamp is not None:
            if raw_ts < self._last_raw_timestamp - 32768:  # 发生向上溢出
                self._timestamp_offset += 65536.0
            elif raw_ts > self._last_raw_timestamp + 32768:  # 发生向下溢出（较罕见）
                self._timestamp_offset -= 65536.0
        
        self._last_raw_timestamp = raw_ts
        absolute_timestamp = (raw_ts + self._timestamp_offset) / 1000.0
        
        # 如果是首次接收数据，记录基准时间戳
        if self._base_timestamp is None:
            self._base_timestamp = absolute_timestamp
        
        # 返回相对时间，从0开始
        return absolute_timestamp - self._base_timestamp
    
    def _on_clear_clicked(self):
        """清空按钮点击"""
        self.clear_all_waveforms()
        self.clear_requested.emit()
    
    def _refresh_all_curves(self):
        """刷新所有曲线显示（20fps，性能优化）"""
        start_time = time.perf_counter()
        
        curves_updated = 0
        total_points = 0
        sampled_curves = 0
        
        for curve_name, curve_data in self._curves.items():
            buffer = curve_data["buffer"]
            if len(buffer) > 0:
                buffer_len = len(buffer)
                total_points += buffer_len
                
                # ========== 性能优化：数据降采样 ==========
                # 如果数据点过多，进行降采样以提升性能
                if buffer_len > 2000:  # 降低阈值（从5000改为2000），更早触发降采样
                    # 每隔2个点取1个（降采样50%）
                    buffer_list = list(buffer)
                    sampled_data = buffer_list[::2]
                    times, values = zip(*sampled_data)
                    sampled_curves += 1
                else:
                    times, values = zip(*buffer)
                
                # 使用numpy数组提高大数据量下的性能
                times_array = np.array(times, dtype=np.float64)
                values_array = np.array(values, dtype=np.float64)
                curve_data["curve"].setData(times_array, values_array)
                curves_updated += 1
                
                # 确保X轴跟随最新数据（实现自动推移）
                plot_widget = curve_data["widget"]
                vb = plot_widget.getViewBox()
                
                # 强制Y轴自动缩放
                vb.enableAutoRange(axis="y", enable=True)
                
                # 获取当前视图范围
                x_range = vb.viewRange()[0]
                latest_x = times[-1]
                
                # 如果最新点到达或超过了当前视图的右边界，自动推移范围
                if latest_x >= x_range[1]:
                    width = x_range[1] - x_range[0]
                    if width > 0:
                        vb.setXRange(latest_x - width, latest_x, padding=0)
        
        # 性能统计
        elapsed = (time.perf_counter() - start_time) * 1000  # 转换为毫秒
        self._refresh_count += 1
        self._total_refresh_time += elapsed
        if elapsed > self._max_refresh_time:
            self._max_refresh_time = elapsed
        
        # 每100次刷新打印一次性能统计
        if self._refresh_count % 100 == 0:
            avg_time = self._total_refresh_time / self._refresh_count
            logger.info(
                f"[波形刷新] 次数:{self._refresh_count} | "
                f"本次:{elapsed:.2f}ms | 平均:{avg_time:.2f}ms | "
                f"最大:{self._max_refresh_time:.2f}ms | "
                f"曲线数:{curves_updated} | 总点数:{total_points} | "
                f"降采样:{sampled_curves}条"
            )
        
        # 警告：如果刷新耗时超过阈值
        if elapsed > 30:  # 超过30ms（约30fps）
            logger.warning(
                f"[波形刷新慢] 耗时:{elapsed:.2f}ms | "
                f"曲线数:{curves_updated} | 总点数:{total_points}"
            )
    
    # ========== Data Binding Slots ==========
    
    @pyqtSlot(dict)
    def update_waveform_data(self, high_freq_data: dict):
        """
        更新所有波形数据（50Hz批量更新）
        
        Args:
            high_freq_data: 高频数据字典，包含所有19个字段:
                - roll, pitch, yaw
                - gyro_x, gyro_y, gyro_z
                - acc_x, acc_y, acc_z
                - roll_rate_desired, pitch_rate_desired, yaw_rate_desired
                - roll_control, pitch_control, yaw_control
                - motor1, motor2, motor3, motor4
                - timestamp
        """
        if not high_freq_data:
            logger.warning("[数据更新] 收到空数据")
            return
        
        # 处理时间戳
        raw_ts = high_freq_data.get("timestamp")
        timestamp = self._process_timestamp(raw_ts)
        
        # 更新每条曲线的缓冲区
        updated_curves = 0
        for key in self._curves.keys():
            if key in high_freq_data:
                value = high_freq_data[key]
                self._curves[key]["buffer"].append((timestamp, value))
                updated_curves += 1
        
        # 每500次数据更新打印一次日志
        if hasattr(self, '_data_update_count'):
            self._data_update_count += 1
        else:
            self._data_update_count = 1
        
        if self._data_update_count % 500 == 0:
            logger.info(f"[数据更新] 已接收 {self._data_update_count} 次数据包，更新了 {updated_curves} 条曲线")
    
    @pyqtSlot()
    def clear_all_waveforms(self):
        """清空所有波形数据，重置时间戳"""
        self._last_raw_timestamp = None
        self._timestamp_offset = 0.0
        self._base_timestamp = None
        
        for curve_data in self._curves.values():
            curve_data["buffer"].clear()
            curve_data["curve"].setData([], [])
            
            # 重置视图范围
            plot_widget = curve_data["widget"]
            vb = plot_widget.getViewBox()
            vb.enableAutoRange(axis="x", enable=True)
            vb.enableAutoRange(axis="y", enable=True)
            vb.setXRange(0, 10, padding=0)
            vb.autoRange()
    
    @pyqtSlot(str, float, float)
    def update_single_curve(self, curve_name: str, timestamp: float, value: float):
        """
        更新单条曲线数据
        
        Args:
            curve_name: 曲线名称
            timestamp: 时间戳（秒）
            value: 数值
        """
        if curve_name in self._curves:
            self._curves[curve_name]["buffer"].append((timestamp, value))
