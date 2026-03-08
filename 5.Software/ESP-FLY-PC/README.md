# ESP-FLY 上位机调试系统

基于PyQt6开发的ESP-FLY无人机调试上位机软件，采用**MVVM架构**，提供实时数据可视化、飞行控制、PID参数调整等功能。

## 功能特性

### 核心功能

- **实时3D姿态显示** - 基于PyVista的3D模型实时姿态可视化
- **实时波形图表** - 基于pyqtgraph的高性能19通道数据曲线显示
- **飞行控制** - 姿态角和油门实时控制（50Hz发送频率）
- **电机测试** - 独立电机油门测试功能
- **PID参数调整** - 内环/外环PID参数在线调整
- **终端监控** - PID参数上报、电池状态、MCU调试输出显示
- **状态监控** - 电池、传感器、通信状态实时监控

### MVVM架构特点

- **Model层** - 纯数据类，无业务逻辑
- **View层** - 纯UI组件，通过信号与ViewModel通信
- **ViewModel层** - 业务逻辑、数据转换、命令处理
- **Service层** - 网络通信、协议解析、配置管理
- **数据绑定** - 基于Qt信号槽机制的响应式UI更新

## 项目结构

```
ESP-FLY-PC/
├── main.py                     # 主程序入口（MVVM绑定）
├── config.ini                  # 配置文件
├── requirements.txt            # Python依赖
│
├── models/                     # Model层 - 纯数据模型
│   ├── drone_state_model.py    # 无人机状态模型
│   ├── flight_control_model.py # 飞行控制模型
│   ├── pid_config_model.py     # PID配置模型
│   ├── connection_state_model.py # 连接状态模型
│   └── motor_test_model.py     # 电机测试模型
│
├── viewmodels/                 # ViewModel层 - 业务逻辑
│   ├── drone_view_model.py     # 核心ViewModel（数据接收处理）
│   ├── flight_control_view_model.py # 飞行控制ViewModel
│   ├── connection_view_model.py # 连接管理ViewModel
│   ├── pid_config_view_model.py # PID配置ViewModel
│   └── motor_test_view_model.py # 电机测试ViewModel
│
├── views/                      # View层 - 纯UI组件
│   ├── main_view.py            # 主窗口
│   ├── status_view.py          # 状态显示面板
│   ├── control_view.py         # 控制面板
│   ├── pid_view.py             # PID调参面板
│   ├── motor_test_view.py      # 电机测试面板
│   ├── terminal_view.py        # 终端监控面板
│   ├── waveform_view.py        # 波形显示面板
│   └── attitude_3d_view.py     # 3D姿态显示
│
├── services/                   # Service层 - 基础服务
│   ├── network_service.py      # UDP网络通信
│   ├── protocol_service.py     # 协议解析/构建
│   └── config_service.py       # 配置管理
│
├── common/                     # 公共组件
│   └── logger.py               # 日志工具
│
└── resources/                  # 资源文件
    └── models/                 # 3D模型文件
```

## 安装说明

### 环境要求

- Python >= 3.10
- Windows / Linux / macOS

### 安装依赖

```bash
# 克隆或下载项目
cd ESP-FLY-PC

# 安装依赖包
pip install -r requirements.txt
```

### 依赖包说明

- **PyQt6** - GUI框架
- **pyqtgraph** - 实时曲线图表
- **pyvista** - 3D可视化（可选）
- **pyvistaqt** - PyVista的Qt集成（可选）
- **numpy** - 数值计算

## 使用说明

### 启动程序

```bash
python main.py
```

### 连接无人机

1. 连接到ESP-FLY无人机的WiFi热点
   - SSID: ESP-DRONE_XXXXXX
   - 密码: 12345678

2. 点击界面上的"连接无人机"按钮

3. 连接成功后，可以看到实时数据更新

### 功能使用

#### 飞行控制

- 在"飞行控制"标签页中：
  - 调整横滚角（Roll）、俯仰角（Pitch）、偏航角（Yaw）
  - 调整油门值
  - 点击"重置"恢复默认值
  - 点击"紧急停止"立即停止所有电机

#### 状态监控

- 在"状态信息"标签页中查看：
  - 连接状态
  - 电池电压和电量
  - 通信统计信息
  - WiFi信号强度

#### 电机测试

- 在"电机测试"标签页中：
  - **警告：测试前务必移除螺旋桨！**
  - 独立调整4个电机的PWM值
  - 批量设置所有电机PWM
  - 点击"停止所有电机"紧急停止

#### PID调参

- 在"PID调参"标签页中：
  - 分别调整角度环（外环）和角速度环（内环）的PID参数
  - 支持Roll、Pitch、Yaw三个轴的独立调整
  - 点击"保存配置"保存参数到文件
  - 点击"发送到飞控"下发参数

#### 终端监控

- 在"终端监控"标签页中查看：
  - PID参数上报（1Hz）
  - 电池状态上报（1Hz）
  - MCU调试输出

#### 波形显示

- 左侧波形面板，6个页签：
  - 姿态角（Roll/Pitch/Yaw）
  - 电机PWM（Motor 1-4）
  - 角度PID输出（期望角速度）
  - 角速度PID输出（控制量）
  - 陀螺仪数据（Gyro X/Y/Z）
  - 加速度计数据（Acc X/Y/Z）

## 配置说明

配置文件：`config.ini`

```ini
[network]
drone_ip = 192.168.43.42
port = 2390

[control]
max_angle = 30.0
max_yaw = 180.0
max_thrust = 65535
send_rate = 50

[pid]
# 默认PID参数...
```

## 通信协议

采用简单数据包格式，通过UDP传输：

```
+----------+----------+-------------------+----------+
|  PacketID|  Length  |      Payload      | Checksum |
|  1 byte  |  1 byte  |   0-120 bytes     |  1 byte  |
+----------+----------+-------------------+----------+
```

### 数据频率

- **高频数据（0x81）**: 50Hz - 姿态、陀螺仪、加速度、PID输出、电机PWM
- **低频数据（0x82）**: 1Hz - 电池状态
- **PID配置响应（0x83）**: 1Hz - PID参数上报
- **控制命令发送**: 50Hz

详细协议说明请参考：[ESP-FLY通信协议接口文档](../../2.Docs/ESP-FLY-DOC/ESP-FLY通信协议接口文档.md)

## MVVM数据流

```
ESP32 → NetworkService → ProtocolService → DroneViewModel → View自动更新
                                              ↓
                                         Property Changed Signal
                                              ↓
                                    View.update_xxx() Slot

View用户操作 → Signal → ViewModel Command → Service → NetworkService → ESP32
```

## 更新日志

### v2.0.0 (2026-01-18)

- 完全重构为MVVM架构
- 高频数据改为50Hz
- 新增波形显示19通道数据
- 新增终端监控面板
- 优化3D姿态显示
- 代码模块化，职责清晰

### v1.0.0 (2024)

- 基础PyQt6界面
- UDP通信功能
- 基本飞行控制

## 许可证

MIT License

---

**© 2026 ESP-FLY Team. All rights reserved.**
