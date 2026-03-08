"""
ESP-FLY-PC 主入口文件
MVVM架构 - 连接ViewModels和Views的数据绑定
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# PyInstaller启动画面支持
try:
    import pyi_splash

    HAS_SPLASH = True
except ImportError:
    HAS_SPLASH = False

# Services
from services.network_service import NetworkService
from services.protocol_service import ProtocolService
from services.config_service import ConfigService

# ViewModels
from viewmodels.drone_view_model import DroneViewModel
from viewmodels.flight_control_view_model import FlightControlViewModel
from viewmodels.connection_view_model import ConnectionViewModel
from viewmodels.pid_config_view_model import PidConfigViewModel
from viewmodels.motor_test_view_model import MotorTestViewModel

# Views
from views.main_view import MainView


class Application:
    """
    ESP-FLY-PC 应用程序类

    职责：
    - 创建和管理Services
    - 创建和管理ViewModels
    - 创建MainView
    - 建立ViewModel和View之间的数据绑定
    """

    def __init__(self):
        # ========== 创建Services ==========
        self.config_service = ConfigService()
        self.protocol_service = ProtocolService()
        self.network_service = NetworkService(
            drone_ip=self.config_service.get_string(
                "network", "drone_ip", "192.168.43.42"
            ),
            port=self.config_service.get_int("network", "port", 2390),
            config_service=self.config_service,
        )

        # ========== 创建ViewModels ==========
        self.drone_vm = DroneViewModel(
            protocol_service=self.protocol_service,
            config_service=self.config_service,
        )
        self.connection_vm = ConnectionViewModel(self.network_service)
        self.flight_control_vm = FlightControlViewModel(
            self.network_service, self.protocol_service
        )
        self.pid_config_vm = PidConfigViewModel(
            self.network_service, self.protocol_service, self.config_service
        )
        self.motor_test_vm = MotorTestViewModel(
            self.network_service, self.protocol_service
        )

        # ========== 创建MainView ==========
        self.main_view = MainView()

        # ========== 建立数据绑定 ==========
        self._setup_service_bindings()
        self._setup_drone_vm_bindings()
        self._setup_connection_vm_bindings()
        self._setup_flight_control_vm_bindings()
        self._setup_pid_config_vm_bindings()
        self._setup_motor_test_vm_bindings()

    def _setup_service_bindings(self):
        """建立Service层绑定"""
        # NetworkService → DroneViewModel（数据接收）
        self.network_service.data_received.connect(self.drone_vm.on_data_received)

        # NetworkService统计 → ConnectionViewModel
        self.network_service.stats_updated.connect(self.connection_vm.on_stats_updated)

    def _setup_drone_vm_bindings(self):
        """建立DroneViewModel绑定"""
        # ========== 姿态数据 → 3D视图 ==========
        self.drone_vm.attitude_changed.connect(
            self.main_view.attitude_3d_view.update_attitude
        )

        # ========== 高频数据 → 波形视图 ==========
        self.drone_vm.high_freq_data_changed.connect(
            self.main_view.waveform_view.update_waveform_data
        )

        # ========== 电池数据 → 状态视图 ==========
        self.drone_vm.battery_voltage_changed.connect(
            self.main_view.status_view.update_battery_voltage
        )
        self.drone_vm.battery_percentage_changed.connect(
            self.main_view.status_view.update_battery_percentage
        )

        # ========== 电池状态 → 终端视图 ==========
        self.drone_vm.battery_status_reported.connect(
            self.main_view.terminal_view.update_battery_info
        )

        # ========== PID配置上报 → 终端视图 ==========
        self.drone_vm.pid_config_reported.connect(
            self.main_view.terminal_view.update_pid_params
        )

        # ========== 控制台输出 → 终端视图 ==========
        self.drone_vm.console_text_received.connect(
            self.main_view.terminal_view.update_console_text
        )

        # ========== 统计信息 → 状态视图 ==========
        self.drone_vm.packet_count_changed.connect(
            self.main_view.status_view.update_recv_count
        )

    def _setup_connection_vm_bindings(self):
        """建立ConnectionViewModel绑定"""
        # ========== View → ViewModel（用户操作）==========
        self.main_view.connect_requested.connect(self.connection_vm.connect_command)
        self.main_view.disconnect_requested.connect(
            self.connection_vm.disconnect_command
        )

        # ========== ViewModel → View（状态更新）==========
        self.connection_vm.is_connected_changed.connect(
            self.main_view.update_connection_buttons
        )
        self.connection_vm.is_connected_changed.connect(
            self.main_view.status_view.update_connection_status
        )
        self.connection_vm.signal_strength_changed.connect(
            self.main_view.status_view.update_signal_strength
        )
        self.connection_vm.sent_packets_changed.connect(
            self.main_view.status_view.update_sent_count
        )

        # ========== 连接成功时清除波形数据 ==========
        self.connection_vm.is_connected_changed.connect(
            lambda connected: (
                self.main_view.waveform_view.clear_all_waveforms()
                if connected
                else None
            )
        )

        # ========== 错误处理 ==========
        self.connection_vm.connection_error.connect(self.main_view.show_error_message)

    def _setup_flight_control_vm_bindings(self):
        """建立FlightControlViewModel绑定"""
        # ========== View → ViewModel（用户操作）==========
        control_view = self.main_view.control_view

        control_view.roll_value_changed.connect(
            lambda v: setattr(self.flight_control_vm, "target_roll", v)
        )
        control_view.pitch_value_changed.connect(
            lambda v: setattr(self.flight_control_vm, "target_pitch", v)
        )
        control_view.yaw_value_changed.connect(
            lambda v: setattr(self.flight_control_vm, "target_yaw", v)
        )
        control_view.thrust_value_changed.connect(
            lambda v: setattr(self.flight_control_vm, "thrust", v)
        )
        control_view.reset_requested.connect(
            self.flight_control_vm.reset_control_command
        )

        # ========== ViewModel → View（状态更新）==========
        self.flight_control_vm.target_roll_changed.connect(control_view.update_roll)
        self.flight_control_vm.target_pitch_changed.connect(control_view.update_pitch)
        self.flight_control_vm.target_yaw_changed.connect(control_view.update_yaw)
        self.flight_control_vm.thrust_changed.connect(control_view.update_thrust)

        # 在连接断开时停止发送
        self.connection_vm.is_connected_changed.connect(
            lambda connected: (
                self.flight_control_vm.disable_control_command()
                if not connected
                else None
            )
        )

    def _setup_pid_config_vm_bindings(self):
        """建立PidConfigViewModel绑定"""
        pid_view = self.main_view.pid_view

        # ========== View → ViewModel（用户操作）==========
        pid_view.pid_changed.connect(self.pid_config_vm.set_pid_command)
        pid_view.send_all_requested.connect(self.pid_config_vm.send_config_command)
        pid_view.save_requested.connect(self.pid_config_vm.save_config_command)
        pid_view.reset_requested.connect(self.pid_config_vm.reset_to_default_command)

        # ========== ViewModel → View（状态更新）==========
        # 输入范围
        self.pid_config_vm.pid_range_changed.connect(pid_view.update_pid_range)
        # 角度环
        self.pid_config_vm.angle_roll_changed.connect(pid_view.update_angle_roll)
        self.pid_config_vm.angle_pitch_changed.connect(pid_view.update_angle_pitch)
        self.pid_config_vm.angle_yaw_changed.connect(pid_view.update_angle_yaw)
        # 角速度环
        self.pid_config_vm.rate_roll_changed.connect(pid_view.update_rate_roll)
        self.pid_config_vm.rate_pitch_changed.connect(pid_view.update_rate_pitch)
        self.pid_config_vm.rate_yaw_changed.connect(pid_view.update_rate_yaw)

        # 数据绑定建立后，初始化UI显示（符合MVVM模式：View绑定后从ViewModel获取初始值）
        self.pid_config_vm.initialize_ui()

    def _setup_motor_test_vm_bindings(self):
        """建立MotorTestViewModel绑定"""
        motor_view = self.main_view.motor_test_view

        # ========== View → ViewModel（用户操作）==========
        motor_view.motor_pwm_changed.connect(self.motor_test_vm.set_motor_pwm_command)
        motor_view.reset_requested.connect(self.motor_test_vm.reset_command)

        # ========== ViewModel → View（状态更新）==========
        self.motor_test_vm.motor1_pwm_changed.connect(motor_view.update_motor1_pwm)
        self.motor_test_vm.motor2_pwm_changed.connect(motor_view.update_motor2_pwm)
        self.motor_test_vm.motor3_pwm_changed.connect(motor_view.update_motor3_pwm)
        self.motor_test_vm.motor4_pwm_changed.connect(motor_view.update_motor4_pwm)

    def run(self):
        """运行应用程序"""
        self.main_view.show()

        # 显示启动信息
        self.main_view.terminal_view.append_info("ESP-FLY-PC v2.0 启动")
        self.main_view.terminal_view.append_info("MVVM架构版本")
        self.main_view.terminal_view.append_info(
            f"目标设备: {self.network_service._drone_ip}:{self.network_service._port}"
        )

    def cleanup(self):
        """清理资源"""
        # 停止控制发送
        self.flight_control_vm.disable_control_command()

        # 断开连接
        if self.connection_vm.is_connected:
            self.connection_vm.disconnect_command()


def update_splash(message):
    """更新启动画面文本"""
    if HAS_SPLASH:
        try:
            pyi_splash.update_text(message)
        except:
            pass
    print(f"[启动] {message}")


def close_splash():
    """关闭启动画面"""
    if HAS_SPLASH:
        try:
            pyi_splash.close()
        except:
            pass


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 更新启动画面（使用英文避免乱码）
    update_splash("Initializing...")

    app = QApplication(sys.argv)
    app.setApplicationName("ESP-FLY-PC")
    app.setApplicationVersion("2.0")
    app.processEvents()

    # 提前加载PyVista/VTK
    update_splash("Loading 3D libraries...")
    app.processEvents()
    try:
        import pyvista as pv
        from pyvistaqt import QtInteractor
        import vtk

        print("[启动] PyVista/VTK库加载成功")
    except ImportError as e:
        print(f"[警告] PyVista导入失败: {e}")
    except Exception as e:
        print(f"[警告] PyVista加载失败: {e}")
    app.processEvents()

    # 创建应用程序实例
    update_splash("Initializing application...")
    app.processEvents()
    application = Application()
    app.processEvents()

    # 显示主窗口
    update_splash("Starting main window...")
    app.processEvents()
    application.run()
    app.processEvents()

    # 关闭启动画面
    close_splash()

    # 运行事件循环
    exit_code = app.exec()

    # 清理
    application.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
