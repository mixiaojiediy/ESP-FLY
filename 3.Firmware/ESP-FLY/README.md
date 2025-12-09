# ESP-FLY 无人机固件

基于 ESP32-C3 的小型四旋翼无人机飞控固件

## 📋 项目概述

ESP-FLY 是一个基于乐鑫 ESP32-C3 芯片开发的小型无人机飞控解决方案。本项目核心代码源自 Bitcraze 开源的 [Crazyflie](https://github.com/bitcraze/crazyflie-firmware) 飞控固件，并针对 ESP32-C3 平台进行了适配和优化。

### 核心特性

- ✈️ **自稳定飞行模式** - 基于 IMU 的姿态自稳定控制
- 📡 **Wi-Fi 遥控** - 通过 Wi-Fi AP 模式进行无线遥控
- 📱 **APP 控制** - 支持手机 APP 或 cfclient 上位机控制
- ⚡ **实时操作系统** - 基于 FreeRTOS 的多任务架构
- 🔋 **电源管理** - 电池电压监测与低电量保护

### 开发环境要求

- **ESP-IDF**: [release/v4.4](https://docs.espressif.com/projects/esp-idf/en/release-v4.4/esp32s2/get-started/index.html) 分支
- **目标芯片**: ESP32-C3

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           应用层 (Application)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Commander  │  │  Stabilizer │  │   System    │  │    Comm     │     │
│  │  (指令管理)  │  │  (飞控稳定)  │  │  (系统管理)  │  │  (通信管理)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
┌─────────┼────────────────┼────────────────┼────────────────┼────────────┐
│         │           核心模块层 (Core Modules)              │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐     │
│  │ Controller  │  │  Estimator  │  │   Sensors   │  │    CRTP     │     │
│  │  (控制器)   │  │ (状态估计器) │  │  (传感器)   │  │  (通信协议)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
┌─────────┼────────────────┼────────────────┼────────────────┼────────────┐
│         │              硬件抽象层 (HAL)                     │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐     │
│  │   Motors    │  │    IMU      │  │     PM      │  │  Wi-Fi/UDP  │     │
│  │  (电机驱动)  │  │ (MPU6050)   │  │  (电源管理)  │  │  (网络通信)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────────┼────────────┘
          │                │                │                │
┌─────────▼────────────────▼────────────────▼────────────────▼────────────┐
│                        ESP32-C3 硬件平台                                 │
│       [GPIO/PWM]        [I2C]           [ADC]           [Wi-Fi]         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 项目目录结构

```
ESP-FLY/
├── main/                          # 主程序入口
│   ├── main.c                     # app_main() 入口函数
│   ├── Kconfig.projbuild          # 项目配置菜单
│   └── CMakeLists.txt             # 编译配置
│
├── components/                    # 组件模块
│   │
│   ├── core/crazyflie/           # 🎯 核心飞控模块 (来自 Crazyflie)
│   │   ├── hal/                   # 硬件抽象层
│   │   │   ├── interface/         # HAL 接口定义 (.h)
│   │   │   └── src/               # HAL 实现 (.c)
│   │   │       ├── sensors_mpu6050_*.c  # IMU 传感器驱动
│   │   │       ├── pm_esplane.c   # 电源管理
│   │   │       ├── ledseq.c       # LED 序列控制
│   │   │       └── wifilink.c     # Wi-Fi 链路层
│   │   │
│   │   ├── modules/               # 功能模块层
│   │   │   ├── interface/         # 模块接口定义 (.h)
│   │   │   └── src/               # 模块实现 (.c)
│   │   │       ├── system.c       # 系统管理
│   │   │       ├── stabilizer.c   # 飞行稳定器
│   │   │       ├── commander.c    # 指令管理器
│   │   │       ├── controller*.c  # PID/Mellinger 控制器
│   │   │       ├── estimator*.c   # 状态估计器
│   │   │       ├── crtp*.c        # CRTP 通信协议
│   │   │       ├── param.c        # 参数系统
│   │   │       └── log.c          # 日志系统
│   │   │
│   │   └── utils/                 # 工具函数
│   │       ├── interface/         # 工具接口 (.h)
│   │       └── src/               # 工具实现 (.c)
│   │
│   ├── drivers/                   # 🔧 驱动程序
│   │   ├── general/
│   │   │   ├── adc/               # ADC 驱动 (电池电压检测)
│   │   │   ├── motors/            # 电机 PWM 驱动
│   │   │   └── wifi/              # Wi-Fi 驱动 (AP 模式)
│   │   ├── i2c_bus/               # I2C 总线驱动
│   │   └── i2c_devices/
│   │       └── mpu6050/           # MPU6050 IMU 驱动
│   │
│   ├── config/                    # ⚙️ 配置文件
│   │   └── include/config.h       # 全局配置 (任务优先级/栈大小等)
│   │
│   ├── platform/                  # 🖥️ 平台适配层
│   │   ├── platform.c             # 平台初始化
│   │   └── platform_esp32.c       # ESP32 特定实现
│   │
│   └── lib/dsp_lib/              # 📐 DSP 数学库
│       ├── BasicMathFunctions/    # 基础数学运算
│       ├── FilteringFunctions/    # 滤波器函数
│       ├── MatrixFunctions/       # 矩阵运算
│       └── TransformFunctions/    # 变换函数 (FFT等)
│
├── sdkconfig.defaults.esp32c3    # ESP32-C3 默认配置
└── README.md                      # 本文档
```

---

## 🔄 系统数据流

### 主控制循环数据流

```
                         ┌──────────────────────────────────┐
                         │         用户控制指令              │
                         │    (APP / cfclient / 遥控器)      │
                         └────────────────┬─────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Wi-Fi 模块 (wifi_esp32.c)                                              │
│  ┌─────────────┐    UDP Port: 2390    ┌─────────────────┐              │
│  │ UDP 接收任务 │ ◀────────────────── │   手机 APP       │              │
│  │ (RX Task)   │                      │   (客户端)       │              │
│  └──────┬──────┘                      └─────────────────┘              │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ UDPPacket (CRTP格式)
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CRTP 协议层 (crtp.c)                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  解析数据包，分发到对应端口:                                       │   │
│  │  - Port 3: Commander (飞行控制指令)                               │   │
│  │  - Port 5: Log (日志数据)                                        │   │
│  │  - Port 2: Param (参数配置)                                      │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ setpoint_t
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Commander 模块 (commander.c)                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  管理设定点 (setpoint):                                           │   │
│  │  - 目标姿态 (roll, pitch, yaw)                                   │   │
│  │  - 目标推力 (thrust)                                             │   │
│  │  - 超时保护 (Watchdog)                                           │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ setpoint_t
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Stabilizer 稳定器 (stabilizer.c) - 主控制循环 @ 1000Hz                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │   ┌───────────┐      ┌───────────┐      ┌───────────────┐       │   │
│  │   │  Sensors  │ ──▶  │ Estimator │ ──▶  │  Controller   │       │   │
│  │   │ 传感器读取 │      │ 状态估计   │      │  姿态控制器    │       │   │
│  │   └───────────┘      └───────────┘      └───────┬───────┘       │   │
│  │         ▲                   │                    │               │   │
│  │         │                   │                    ▼               │   │
│  │   sensorData_t         state_t              control_t           │   │
│  │   (加速度/陀螺仪)      (姿态/位置)          (roll/pitch/yaw/thrust)│   │
│  │                                                   │               │   │
│  └───────────────────────────────────────────────────┼───────────────┘   │
└──────────────────────────────────────────────────────┼───────────────────┘
                                                       │ control_t
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Power Distribution 功率分配 (power_distribution_stock.c)               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  将控制量转换为四个电机的 PWM 值:                                   │   │
│  │  M1 = thrust + pitch + roll - yaw                               │   │
│  │  M2 = thrust + pitch - roll + yaw                               │   │
│  │  M3 = thrust - pitch - roll - yaw                               │   │
│  │  M4 = thrust - pitch + roll + yaw                               │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ motorPower[4]
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Motors 电机驱动 (motors.c)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  LEDC PWM 输出:                                                   │   │
│  │  - 频率: 15kHz                                                   │   │
│  │  - 分辨率: 10-bit (0-1023)                                       │   │
│  │  - 电池电压补偿 (可选)                                            │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ PWM Signal
          ▼
    ┌───────────────────────────────────────────┐
    │           四路有刷电机 (M1-M4)              │
    │    [Motor1]  [Motor2]  [Motor3]  [Motor4] │
    └───────────────────────────────────────────┘
```

---

## 🧩 核心模块详解

### 1. System 系统模块 (`system.c`)

**功能**: 系统启动管理和任务协调

```c
// 系统启动流程
void systemLaunch(void)  // 创建 systemTask
    │
    └─▶ systemTask()
         ├── wifiInit()           // Wi-Fi AP 初始化
         ├── systemInit()         // 系统子模块初始化
         │    ├── wifilinkInit()  // Wi-Fi 链路层
         │    ├── crtpInit()      // CRTP 协议
         │    ├── consoleInit()   // 控制台
         │    ├── pmInit()        // 电源管理
         │    └── adcInit()       // ADC
         ├── commInit()           // 通信模块
         ├── commanderInit()      // 指令管理器
         ├── stabilizerInit()     // 飞行稳定器
         └── soundInit()          // 声音提示
```

**关键接口**:
| 函数                | 描述             |
| ------------------- | ---------------- |
| `systemLaunch()`    | 启动系统任务     |
| `systemWaitStart()` | 等待系统启动完成 |
| `systemCanFly()`    | 检查是否允许飞行 |
| `systemIsArmed()`   | 检查是否已解锁   |

---

### 2. Stabilizer 稳定器模块 (`stabilizer.c`)

**功能**: 核心飞行控制循环，协调传感器、估计器和控制器

**运行频率**: 1000Hz (由传感器数据就绪信号触发)

```c
// 主控制循环
void stabilizerTask(void* param) {
    while(1) {
        sensorsWaitDataReady();           // 等待传感器数据
        
        stateEstimator(&state, ...);      // 状态估计
        commanderGetSetpoint(&setpoint);  // 获取控制指令
        controller(&control, ...);        // 计算控制量
        
        if (systemIsArmed())
            powerDistribution(&control);   // 分配电机功率
        else
            powerStop();                   // 停止电机
    }
}
```

**数据结构**:
```c
// 传感器数据
typedef struct {
    Axis3f acc;     // 加速度 (g)
    Axis3f gyro;    // 角速度 (deg/s)
    Axis3f mag;     // 磁力计 (可选)
    baro_t baro;    // 气压计 (可选)
} sensorData_t;

// 状态估计
typedef struct {
    attitude_t attitude;      // 姿态角 (roll, pitch, yaw)
    quaternion_t attitudeQuaternion;  // 姿态四元数
    point_t position;         // 位置 (x, y, z)
    velocity_t velocity;      // 速度
    acc_t acc;               // 加速度
} state_t;

// 控制输出
typedef struct {
    float roll;    // 横滚控制量
    float pitch;   // 俯仰控制量
    float yaw;     // 偏航控制量
    float thrust;  // 推力
} control_t;
```

---

### 3. Sensors 传感器模块 (`sensors_mpu6050_hm5883L_ms5611.c`)

**功能**: MPU6050 IMU 数据采集和处理

**采样频率**: 1000Hz

```
传感器数据处理流程:
┌────────────────┐
│   MPU6050      │
│  (I2C 设备)    │
└───────┬────────┘
        │ 中断触发 (GPIO20)
        ▼
┌────────────────┐
│  sensorsTask   │ ◀── ISR 唤醒
│  (传感器任务)   │
└───────┬────────┘
        │
        ▼
┌────────────────────────────────────────────────────┐
│ 数据处理流程:                                        │
│ 1. I2C 读取原始数据 (14 bytes)                       │
│ 2. 解析加速度和陀螺仪数据                             │
│ 3. 陀螺仪偏置校准 (启动时自动)                        │
│ 4. 低通滤波 (LPF: Gyro 80Hz, Acc 30Hz)              │
│ 5. 加速度对齐校准                                    │
│ 6. 数据入队 (Queue)                                 │
└───────┬────────────────────────────────────────────┘
        │
        ▼
┌────────────────┐
│  sensorsDataReady  │ ◀── 信号量通知 Stabilizer
└────────────────┘
```

**关键配置**:
| 参数       | 值        | 描述       |
| ---------- | --------- | ---------- |
| I2C_SDA    | GPIO7     | I2C 数据线 |
| I2C_SCL    | GPIO6     | I2C 时钟线 |
| MPU_INT    | GPIO20    | 中断引脚   |
| 陀螺仪量程 | ±2000 °/s | 角速度范围 |
| 加速度量程 | ±16 g     | 加速度范围 |

---

### 4. Controller 控制器模块 (`controller_pid.c`)

**功能**: PID 姿态控制器

**控制架构**: 级联 PID (角度环 + 角速度环)

```
                   期望姿态
                      │
                      ▼
            ┌──────────────────┐
            │   角度 PID 环     │
            │  (Attitude PID)  │
            └────────┬─────────┘
                     │ 期望角速度
                     ▼
            ┌──────────────────┐     实际角速度
            │  角速度 PID 环    │ ◀───────────
            │   (Rate PID)     │     (陀螺仪)
            └────────┬─────────┘
                     │
                     ▼
               控制输出量
        (roll_torque, pitch_torque, yaw_torque)
```

**PID 参数** (可通过 cfclient 调整):
```c
// 角速度环 PID
PID_RATE_ROLL_KP, PID_RATE_ROLL_KI, PID_RATE_ROLL_KD
PID_RATE_PITCH_KP, PID_RATE_PITCH_KI, PID_RATE_PITCH_KD
PID_RATE_YAW_KP, PID_RATE_YAW_KI, PID_RATE_YAW_KD

// 角度环 PID
PID_ROLL_KP, PID_ROLL_KI, PID_ROLL_KD
PID_PITCH_KP, PID_PITCH_KI, PID_PITCH_KD
PID_YAW_KP, PID_YAW_KI, PID_YAW_KD
```

---

### 5. Estimator 状态估计器 (`estimator_complementary.c` / `estimator_kalman.c`)

**功能**: 融合传感器数据，估计飞行器状态

**支持的估计器**:
| 估计器        | 描述           | 资源占用 |
| ------------- | -------------- | -------- |
| Complementary | 互补滤波器     | 低       |
| Kalman (EKF)  | 扩展卡尔曼滤波 | 高       |

**互补滤波原理**:
```
加速度计 ──┐
(低频稳定) │    ┌─────────────┐
          ├───▶│ 互补滤波器   │───▶ 姿态估计
          │    │ α·acc + (1-α)·gyro │
陀螺仪 ───┘    └─────────────┘
(高频响应)
```

---

### 6. CRTP 通信协议 (`crtp.c`)

**功能**: Crazyflie Real-Time Protocol - 实时通信协议

**协议结构**:
```
┌─────────────────────────────────────────────────────────┐
│                    CRTP 数据包格式                       │
├──────────┬─────────┬────────────────────────────────────┤
│ Header   │ Size    │ Data (0-30 bytes)                  │
│ (1 byte) │ (1 byte)│                                    │
├──────────┴─────────┴────────────────────────────────────┤
│ Header: [Port(4bit)][Link(2bit)][Channel(2bit)]        │
└─────────────────────────────────────────────────────────┘
```

**端口分配**:
| Port | 名称      | 功能         |
| ---- | --------- | ------------ |
| 0    | Console   | 控制台输出   |
| 2    | Param     | 参数读写     |
| 3    | Commander | 飞行控制指令 |
| 5    | Log       | 日志数据     |
| 7    | Platform  | 平台服务     |

---

### 7. Wi-Fi 通信模块 (`wifi_esp32.c`)

**功能**: Wi-Fi AP 模式和 UDP 数据传输

**配置**:
| 参数     | 默认值                             |
| -------- | ---------------------------------- |
| SSID     | `ESP-DRONE_XXXXXXXXXXXX` (MAC地址) |
| 密码     | `12345678`                         |
| IP 地址  | `192.168.43.42`                    |
| UDP 端口 | `2390`                             |

**任务架构**:
```
┌────────────────────────────────────────────────────────┐
│                   Wi-Fi 模块任务                        │
│                                                        │
│  ┌──────────────┐       ┌──────────────┐              │
│  │ UDP_RX_Task  │       │ UDP_TX_Task  │              │
│  │ (接收任务)    │       │ (发送任务)    │              │
│  │ - 接收 UDP   │       │ - 发送 UDP   │              │
│  │ - 校验解析   │       │ - 加校验和   │              │
│  │ - 入队 CRTP  │       │ - 出队发送   │              │
│  └──────┬───────┘       └───────┬──────┘              │
│         │                       │                      │
│         ▼                       ▲                      │
│   ┌──────────┐            ┌──────────┐                │
│   │ udpDataRx │            │ udpDataTx │                │
│   │  (Queue)  │            │  (Queue)  │                │
│   └──────────┘            └──────────┘                │
└────────────────────────────────────────────────────────┘
```

---

### 8. Motors 电机驱动 (`motors.c`)

**功能**: PWM 电机控制

**配置**:
| 参数       | 值                  |
| ---------- | ------------------- |
| PWM 频率   | 15 kHz              |
| PWM 分辨率 | 10-bit (0-1023)     |
| 定时器     | LEDC_TIMER_0        |
| 速度模式   | LEDC_LOW_SPEED_MODE |

**GPIO 映射** (默认):
| 电机 | GPIO   |
| ---- | ------ |
| M1   | GPIO5  |
| M2   | GPIO4  |
| M3   | GPIO10 |
| M4   | GPIO21 |

**X 型布局**:
```
        前方
         ▲
    M2       M1
      ╲     ╱
       ╲   ╱
        ╲ ╱
         ●  (机身中心)
        ╱ ╲
       ╱   ╲
      ╱     ╲
    M3       M4

旋转方向: M1/M3 顺时针, M2/M4 逆时针
```

---

### 9. Power Management 电源管理 (`pm_esplane.c`)

**功能**: 电池电压监测和状态管理

**状态机**:
```
┌─────────────┐         ┌─────────────┐
│   battery   │ ──────▶ │  lowPower   │
│  (电池供电)  │ 电压过低  │ (低电量警告) │
└──────┬──────┘         └──────┬──────┘
       │                       │
 充电器接入                     │ 继续下降
       │                       ▼
       ▼                ┌─────────────┐
┌─────────────┐         │  shutdown   │
│  charging   │         │  (关机保护)  │
│  (充电中)    │         └─────────────┘
└──────┬──────┘
       │ 充满
       ▼
┌─────────────┐
│   charged   │
│  (已充满)    │
└─────────────┘
```

**电池电压阈值**:
| 状态   | 电压 (单芯锂电) |
| ------ | --------------- |
| 满电   | > 4.10V         |
| 正常   | 3.7V - 4.10V    |
| 低电量 | < 3.4V          |
| 临界   | < 3.0V          |

---

## ⚙️ 配置系统

### Kconfig 配置项

通过 `idf.py menuconfig` 进入 "ESPDrone Config" 菜单:

```
ESPDrone Config
├── app set
│   ├── Enable legacy ESPlane1.0 APP
│   ├── Enable position hold mode
│   └── Enable 'setCommandermode' to transform command
│
├── calibration angle
│   ├── PITCH_CALIB deg*100     (默认: 0)
│   └── ROLL_CALIB deg*100      (默认: 0)
│
├── system
│   └── base stack size         (默认: 1024)
│
├── sensors config
│   ├── I2C0_PIN_SDA            (默认: GPIO7)
│   ├── I2C0_PIN_SCL            (默认: GPIO6)
│   ├── MPU_PIN_INT             (默认: GPIO20)
│   └── ADC1_PIN                (默认: GPIO3)
│
└── motors config
    ├── Motor type              (715/720 有刷电机)
    ├── MOTOR01_PIN             (默认: GPIO5)
    ├── MOTOR02_PIN             (默认: GPIO4)
    ├── MOTOR03_PIN             (默认: GPIO10)
    └── MOTOR04_PIN             (默认: GPIO21)
```

---

## 🔧 FreeRTOS 任务列表

| 任务名     | 优先级 | 栈大小 | 功能           |
| ---------- | ------ | ------ | -------------- |
| SYSTEM     | 2      | 6KB    | 系统管理       |
| STABILIZER | 5      | 5KB    | 飞行稳定控制   |
| SENSORS    | 4      | 5KB    | 传感器数据采集 |
| CRTP-TX    | 2      | 2KB    | CRTP 发送      |
| CRTP-RX    | 2      | 6KB    | CRTP 接收      |
| UDP_TX     | 3      | 2KB    | UDP 发送       |
| UDP_RX     | 3      | 4KB    | UDP 接收       |
| PWRMGNT    | 0      | 4KB    | 电源管理       |
| LOG        | 1      | 3KB    | 日志记录       |
| PARAM      | 2      | 2KB    | 参数管理       |

---

## 📡 通信接口

### 与上位机通信

**支持的客户端**:
- [ESP-Drone iOS APP](https://github.com/EspressifApps/ESP-Drone-iOS)
- [ESP-Drone Android APP](https://github.com/EspressifApps/ESP-Drone-Android)
- [cfclient](https://github.com/bitcraze/crazyflie-clients-python) (Crazyflie PC 客户端)

**连接步骤**:
1. 上电启动，等待 Wi-Fi 初始化完成
2. 手机/PC 连接到 `ESP-DRONE_XXXX` 热点
3. 密码: `12345678`
4. 打开 APP 或 cfclient 开始控制

---

## 🚀 编译和烧录

```bash
# 设置 ESP-IDF 环境
. $HOME/esp/esp-idf/export.sh

# 配置目标芯片
idf.py set-target esp32c3

# 配置项目 (可选)
idf.py menuconfig

# 编译
idf.py build

# 烧录
idf.py -p COM3 flash

# 监控串口输出
idf.py -p COM3 monitor
```

---

## 📜 开源协议

本项目使用 **GPL-3.0** 开源协议

### 第三方代码

| 组件           | 许可证  | 来源                                                                                 | Commit ID           |
| -------------- | ------- | ------------------------------------------------------------------------------------ | ------------------- |
| core/crazyflie | GPL-3.0 | [Crazyflie](https://github.com/bitcraze/crazyflie-firmware)                          | tag_2021_01 b448553 |
| lib/dsp_lib    | -       | [esp32-lin](https://github.com/whyengineer/esp32-lin/tree/master/components/dsp_lib) | 6fa39f4c            |

---

## 🙏 致谢

1. 感谢 **Bitcraze** 开源组织提供优秀的 [Crazyflie](https://www.bitcraze.io/) 无人机飞控代码
2. 感谢 **乐鑫科技** 提供 ESP32 芯片和 [ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/) 开发框架
3. 感谢 **WhyEngineer** 提供的 [DSP 移植库](https://github.com/whyengineer/esp32-lin/tree/master/components/dsp_lib)
