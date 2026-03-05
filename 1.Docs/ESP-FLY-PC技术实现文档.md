# ESP-FLY 上位机技术实现文档

## 文档说明

本文档描述 ESP-FLY PC端调试上位机的架构设计、模块划分和技术实现方案。

---

## 1. 系统架构设计

### 1.1 整体架构

系统采用 **MVVM (Model-View-ViewModel) 架构模式**，结合多线程设计实现高性能数据处理和流畅UI交互。通过Qt信号槽机制实现View和ViewModel的自动同步。

```
┌─────────────────────────────────────────────────────────────┐
│                    View层 (视图层)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  主窗口视图  │  │  3D姿态视图  │  │  波形视图    │      │
│  │ MainView     │  │ Attitude3D   │  │ WaveformView │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  控制视图    │  │  状态视图    │  │  电机测试    │      │
│  │ ControlView  │  │ StatusView   │  │ MotorTestView│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  PID视图     │  │  终端视图    │                        │
│  │ PidView      │  │ TerminalView │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕ (信号槽/数据绑定)
┌─────────────────────────────────────────────────────────────┐
│              ViewModel层 (视图模型层)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │DroneViewModel│  │FlightControlVM│ │ConnectionVM  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ PidConfigVM  │  │ MotorTestVM  │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              Model层 (数据模型层)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DroneState   │  │ FlightControl│  │ Connection   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ PidConfig    │  │ MotorTest    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              Service层 (服务层)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │NetworkService│  │ProtocolService│ │ConfigService  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 架构特点

1. **MVVM分离**：View、ViewModel、Model、Service四层职责清晰，完全解耦
2. **数据绑定**：通过Qt信号槽实现双向数据绑定，自动同步
3. **线程分离**：UI主线程 + UDP接收线程 + 控制发送线程，避免阻塞
4. **事件驱动**：采用Qt信号槽机制实现模块间通信

---

## 2. 目录结构

```
ESP-FLY-PC/
├── main.py                          # 主程序入口（Application类）
├── config/config.ini                  # 配置文件
├── requirements.txt                 # Python依赖
│
├── views/                           # View层
│   ├── main_view.py                 # 主窗口视图
│   ├── status_view.py               # 状态显示视图
│   ├── control_view.py              # 控制面板视图
│   ├── pid_view.py                  # PID调参视图
│   ├── motor_test_view.py           # 电机测试视图
│   ├── terminal_view.py             # 终端监控视图
│   ├── waveform_view.py             # 波形显示视图
│   └── attitude_3d_view.py          # 3D姿态显示视图
│
├── viewmodels/                      # ViewModel层
│   ├── drone_view_model.py          # 无人机数据ViewModel
│   ├── connection_view_model.py     # 连接管理ViewModel
│   ├── flight_control_view_model.py # 飞行控制ViewModel
│   ├── pid_config_view_model.py     # PID配置ViewModel
│   └── motor_test_view_model.py     # 电机测试ViewModel
│
├── models/                          # Model层
│   ├── drone_state_model.py         # 无人机状态数据模型
│   ├── connection_state_model.py    # 连接状态数据模型
│   ├── flight_control_model.py      # 飞行控制数据模型
│   ├── pid_config_model.py          # PID配置数据模型
│   └── motor_test_model.py          # 电机测试数据模型
│
├── services/                        # Service层
│   ├── network_service.py           # 网络通信服务（UDP）
│   ├── protocol_service.py          # 协议解析服务
│   └── config_service.py            # 配置管理服务
│
├── common/                          # 公共工具模块
│   └── logger.py                    # 日志管理
│
└── resources/models/                # 3D模型资源（OBJ/MTL）
```

---

## 3. 模块职责说明

### 3.1 View层 (`views/`)

| 视图           | 文件                | 职责                                                              |
| -------------- | ------------------- | ----------------------------------------------------------------- |
| MainView       | main_view.py        | 主窗口，组合所有子View；左侧3D/波形切换，右侧Tab页签              |
| StatusView     | status_view.py      | 连接状态、电池电压、通信统计显示                                  |
| ControlView    | control_view.py     | 目标角度（Roll/Pitch/Yaw）和油门输入，紧急停止按钮                |
| PidView        | pid_view.py         | 角度环PID参数（Roll/Pitch/Yaw × P/I/D = 9个参数），保存/加载/重置 |
| MotorTestView  | motor_test_view.py  | 4个电机独立PWM控制，测试模式启用/禁用                             |
| TerminalView   | terminal_view.py    | 控制台输出、电池状态、PID参数上报显示                             |
| WaveformView   | waveform_view.py    | 实时数据曲线（姿态角、角速度、加速度等），pyqtgraph实现           |
| Attitude3DView | attitude_3d_view.py | 3D姿态显示，加载OBJ模型，实时旋转更新，PyVista/VTK实现            |

所有View通过信号槽与ViewModel通信，不包含业务逻辑。

### 3.2 ViewModel层 (`viewmodels/`)

| ViewModel              | 文件                         | 职责                                                              |
| ---------------------- | ---------------------------- | ----------------------------------------------------------------- |
| DroneViewModel         | drone_view_model.py          | 接收网络数据，通过ProtocolService解析，发射姿态/传感器/电池等信号 |
| ConnectionViewModel    | connection_view_model.py     | 连接/断开管理，网络检查，WiFi信号强度检测，通信统计               |
| FlightControlViewModel | flight_control_view_model.py | 控制指令管理，50Hz周期发送，参数限幅，紧急停止                    |
| PidConfigViewModel     | pid_config_view_model.py     | 角度环PID参数设置/下发/保存/加载，参数校验                        |
| MotorTestViewModel     | motor_test_view_model.py     | 电机PWM设置，测试模式管理，安全检查                               |

每个ViewModel管理对应的Model数据，通过信号发射属性变化通知View更新。

### 3.3 Model层 (`models/`)

| 模型                 | 文件                      | 说明                                                                                                           |
| -------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| DroneStateModel      | drone_state_model.py      | 高频飞行数据（50Hz）：姿态角、PID控制输出、电机PWM、陀螺仪、加速度计；低频数据（1Hz）：电池电压、角度环PID参数 |
| ConnectionStateModel | connection_state_model.py | 连接状态、IP地址、端口、信号强度                                                                               |
| FlightControlModel   | flight_control_model.py   | 目标Roll/Pitch/Yaw、油门值、控制限制参数                                                                       |
| PidConfigModel       | pid_config_model.py       | 角度环PID参数（Roll/Pitch/Yaw × P/I/D = 9个参数）                                                              |
| MotorTestModel       | motor_test_model.py       | 4个电机PWM值、测试使能状态                                                                                     |

所有Model均为纯数据类（dataclass），不包含业务逻辑。

### 3.4 Service层 (`services/`)

| 服务            | 文件                | 职责                                                                          |
| --------------- | ------------------- | ----------------------------------------------------------------------------- |
| NetworkService  | network_service.py  | UDP Socket管理、数据包广播发送、独立线程接收、连接状态管理、通信统计          |
| ProtocolService | protocol_service.py | Simple Packet协议编解码、控制/PID/电机测试包构建、高频数据/电池/PID响应包解析 |
| ConfigService   | config_service.py   | config.ini 配置文件读写、默认配置管理、类型安全访问接口                       |

---

## 4. 通信协议

ESP-FLY-PC使用与MCU端一致的 **Simple Packet Protocol** 进行通信。

协议详细说明请参考：**[ESP-FLY通信协议接口文档](./ESP-FLY通信协议接口文档.md)**

### 4.1 使用的数据包类型

**上行数据包（PC → MCU）：**

| PacketID | 名称         | Payload | 说明                                   |
| -------- | ------------ | ------- | -------------------------------------- |
| 0x01     | 飞行控制命令 | 14B     | Roll/Pitch/Yaw(float) + Thrust(uint16) |
| 0x02     | PID参数配置  | 36B     | 角度环 9个float参数                    |
| 0x03     | 电机测试     | 9B      | 4个电机PWM(uint16) + 使能(uint8)       |

**下行数据包（MCU → PC）：**

| PacketID | 名称         | Payload | 频率 | 说明                              |
| -------- | ------------ | ------- | ---- | --------------------------------- |
| 0x81     | 高频飞行数据 | 52B     | 50Hz | 姿态/PID输出/电机/陀螺仪/加速度计 |
| 0x82     | 电池状态     | 4B      | 1Hz  | 电压(float)                       |
| 0x83     | PID参数响应  | 36B     | 1Hz  | 角度环 9个float参数               |

---

## 5. 线程模型

```
┌─────────────────────────────────────────────────┐
│              主线程 (Qt GUI Thread)              │
│  - UI渲染 / 事件处理                             │
│  - 3D视图更新 / 曲线绘制                         │
│  - 数据解析（通过信号槽接收）                    │
│  - DroneState更新（线程安全）                    │
└─────────────────────────────────────────────────┘
                     ↕ (Qt信号槽)
┌─────────────────────────────────────────────────┐
│            UDP接收线程 (Receive Thread)          │
│  - 阻塞式接收UDP数据                             │
│  - 发射data_received信号到主线程                 │
└─────────────────────────────────────────────────┘
                     ↕ (Qt信号槽)
┌─────────────────────────────────────────────────┐
│           控制发送线程 (Send Thread)             │
│  - 50Hz周期发送控制命令                          │
│  - 调用NetworkService.send_packet               │
└─────────────────────────────────────────────────┘
```

**线程间通信**采用Qt信号槽机制（线程安全），UDP接收线程只负责接收和发射信号，所有DroneStateModel的更新都在主线程中进行，无需额外的读写锁。

---

## 6. 数据流设计

### 6.1 控制数据流（PC → MCU，50Hz）

```
用户在ControlView操作 → 信号 → FlightControlViewModel处理（限幅）
    → ProtocolService打包（0x01）
    → NetworkService广播发送 → ESP32
```

### 6.2 遥测数据流（MCU → PC）

```
ESP32广播 → NetworkService接收线程 → 信号 → DroneViewModel
    → ProtocolService解析 → 更新DroneStateModel
    → 发射信号 → View自动更新：
        ├─ 0x81(50Hz) → Attitude3DView(3D旋转) + WaveformView(曲线)
        ├─ 0x82(1Hz)  → StatusView(电池电压)
        └─ 0x83(1Hz)  → TerminalView(PID参数显示)
```

### 6.3 PID参数下发流程

```
用户在PidView修改参数 → PidConfigViewModel
    → ProtocolService打包（0x02，36B，角度环9参数）
    → NetworkService发送 → ESP32应用新参数
    → ESP32回传PID响应（0x83） → TerminalView确认
```

### 6.4 电机测试流程

```
用户在MotorTestView设置PWM → MotorTestViewModel
    → ProtocolService打包（0x03，9B）
    → NetworkService发送 → ESP32驱动电机
```

---

## 7. Application类（入口）

Application类是整个应用的入口，负责：

1. **创建Services**：ConfigService → ProtocolService → NetworkService
2. **创建ViewModels**：DroneVM、ConnectionVM、FlightControlVM、PidConfigVM、MotorTestVM
3. **创建MainView**：组合所有子View
4. **建立数据绑定**：通过信号槽连接 Service ↔ ViewModel ↔ View

所有模块的依赖关系在Application中统一管理，实现依赖注入。

---

## 8. UI布局

```
┌──────────────────────────────────────────────────────────────────┐
│ [连接] [断开]                        ESP-FLY 上位机调试系统 v1.0 │
├─────────────────────────────┬────────────────────────────────────┤
│                             │  [状态] [控制] [电机测试] [PID] [终端] │
│                             ├────────────────────────────────────┤
│    3D姿态视图               │                                    │
│    (PyVista/VTK)            │    Tab页内容区                     │
│                             │    - 状态：连接/电池/通信统计      │
│    或                       │    - 控制：Roll/Pitch/Yaw/Thrust   │
│                             │    - 电机测试：4路PWM独立控制      │
│    波形视图                 │    - PID：角度环参数设置            │
│    (pyqtgraph)              │    - 终端：控制台输出               │
│                             │                                    │
├─────────────────────────────┴────────────────────────────────────┤
│ 状态栏：连接状态 | 电池电压 | 收发包数                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. 依赖库

| 库            | 用途                |
| ------------- | ------------------- |
| PyQt6         | GUI框架、信号槽机制 |
| PyVista / VTK | 3D姿态可视化        |
| pyqtgraph     | 实时曲线绘制        |
| NumPy         | 数据处理            |
| PyInstaller   | 打包为可执行文件    |

---

## 10. 错误处理策略

| 错误类型       | 处理策略                         |
| -------------- | -------------------------------- |
| 连接失败       | 提示检查WiFi网络，提供重连按钮   |
| 接收超时       | 标记连接断开，显示警告           |
| 发送失败       | 记录日志，尝试重发（最多3次）    |
| 数据包损坏     | 校验和不通过则丢弃，记录丢包统计 |
| 3D模型加载失败 | 使用默认几何体替代               |
| 配置加载失败   | 使用默认配置                     |

---

**文档版本**: v3.0  
**更新日期**: 2026-02-09  
**作者**: ESP-FLY Team
