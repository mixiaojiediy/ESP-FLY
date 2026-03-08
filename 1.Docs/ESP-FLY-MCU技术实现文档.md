# ESP-FLY-MCU 项目结构文档

## 📋 目录

- [项目概述](#项目概述)
- [目录结构详解](#目录结构详解)
- [核心模块功能说明](#核心模块功能说明)
- [系统数据流详解](#系统数据流详解)
- [FreeRTOS 任务架构](#freertos-任务架构)
- [配置系统](#配置系统)
- [关键数据结构](#关键数据结构)

---

## 项目概述

ESP-FLY-MCU 是一个基于 ESP32 芯片的小型四旋翼无人机飞控固件项目。项目核心代码源自 Bitcraze 开源的 Crazyflie 飞控固件，并针对 ESP32 平台进行了适配和优化。

### 核心特性

- ✈️ **自稳定飞行模式** - 基于 IMU 的姿态自稳定控制
- 📡 **Wi-Fi 遥控** - 通过 Wi-Fi AP 模式进行无线遥控
- 📱 **APP 控制** - 支持手机 APP 或 cfclient 上位机控制
- ⚡ **实时操作系统** - 基于 FreeRTOS 的多任务架构
- 🔋 **电源管理** - 电池电压监测与低电量保护

### 技术栈

- **硬件平台**: ESP32
- **开发框架**: ESP-IDF v4.4
- **操作系统**: FreeRTOS
- **传感器**: MPU6050 (IMU)
- **通信协议**: Simple Packet Protocol (自定义简单数据包协议)
- **传输层**: Wi-Fi UDP

---

## 目录结构详解

```
ESP-FLY-MCU/
│
├── main/                          # 📍 主程序入口目录
│   ├── main.c                     # app_main() 入口函数，系统启动入口
│   ├── CMakeLists.txt             # 主程序编译配置
│   ├── Kconfig.projbuild          # 项目配置菜单定义
│   └── linker_fragment.lf         # 链接器片段配置
│
├── components/                    # 🧩 组件模块目录
│   │
│   ├── config/                    # ⚙️ 全局配置文件
│   │   ├── CMakeLists.txt
│   │   └── include/
│   │       └── config.h           # 全局配置：任务优先级、栈大小、系统参数
│   │
│   ├── protocol/                  # 📡 通信协议模块
│   │   ├── include/
│   │   │   ├── packet_codec.h         # 数据包编解码器
│   │   │   ├── command_receiver.h     # 飞行控制命令接收
│   │   │   ├── config_receiver.h      # 配置命令接收
│   │   │   ├── data_sender.h          # 数据发送接口
│   │   │   └── protocol_dispatcher.h  # 协议分发器
│   │   ├── packet_codec.c             # 协议打包与解析实现
│   │   ├── command_receiver.c         # 飞行控制命令处理
│   │   ├── config_receiver.c          # 配置命令处理（PID参数等）
│   │   ├── data_sender.c              # 高频/低频数据发送任务
│   │   ├── protocol_dispatcher.c      # 协议分发与路由
│   │   └── CMakeLists.txt
│   │
│   ├── core/                      # 🎯 核心飞控模块（来自 Crazyflie）
│   │   └── crazyflie/
│   │       │
│   │       ├── hal/               # 硬件抽象层 (Hardware Abstraction Layer)
│   │       │   ├── interface/     # HAL 接口定义（头文件）
│   │       │   │   ├── sensors.h          # 传感器接口
│   │       │   │   ├── motors.h           # 电机驱动接口
│   │       │   │   ├── pm.h               # 电源管理接口
│   │       │   │   ├── wifilink.h         # Wi-Fi 链路接口
│   │       │   │   └── ...                # 其他 HAL 接口
│   │       │   │
│   │       │   └── src/           # HAL 实现（源文件）
│   │       │       ├── sensors_mpu6050.c   # MPU6050 IMU 传感器驱动实现
│   │       │       ├── sensors.c          # 传感器抽象层
│   │       │       ├── pm_esplane.c       # ESP32 电源管理实现
│   │       │       ├── wifilink.c         # Wi-Fi 链路层实现
│   │       │       ├── usec_time.c        # 微秒级时间戳
│   │       │       └── freeRTOSdebug.c    # FreeRTOS 调试工具
│   │       │
│   │       ├── modules/           # 功能模块层
│   │       │   ├── interface/    # 模块接口定义（头文件，55个文件）
│   │       │   │   ├── stabilizer.h      # 稳定器接口
│   │       │   │   ├── stabilizer_types.h # 稳定器数据类型
│   │       │   │   ├── controller.h      # 控制器接口
│   │       │   │   ├── controller_pid.h  # PID 控制器接口
│   │       │   │   ├── estimator.h       # 状态估计器接口
│   │       │   │   ├── estimator_complementary.h # 互补滤波器接口
│   │       │   │   ├── estimator_kalman.h # 卡尔曼滤波器接口
│   │       │   │   ├── commander.h       # 指令管理器接口
│   │       │   │   ├── crtp.h            # CRTP 协议接口
│   │       │   │   ├── param.h           # 参数系统接口
│   │       │   │   ├── log.h             # 日志系统接口
│   │       │   │   ├── system.h          # 系统管理接口
│   │       │   │   ├── math3d.h          # 3D 数学库（向量、矩阵、四元数）
│   │       │   │   ├── sensfusion6.h     # 传感器融合算法
│   │       │   │   ├── pid.h             # PID 控制器工具
│   │       │   │   └── ...               # 其他模块接口
│   │       │   │
│   │       │   └── src/          # 模块实现（源文件，55个文件）
│   │       │       ├── stabilizer.c      # 飞行稳定器主循环（1000Hz）
│   │       │       ├── controller_pid.c  # PID 姿态控制器
│   │       │       ├── controller_mellinger.c # Mellinger 控制器
│   │       │       ├── controller_indi.c  # INDI 控制器
│   │       │       ├── estimator_complementary.c # 互补滤波器状态估计
│   │       │       ├── estimator_kalman.c # 卡尔曼滤波器状态估计
│   │       │       ├── commander.c       # 指令管理器（设定点管理）
│   │       │       ├── crtp_commander.c  # CRTP 指令处理
│   │       │       ├── crtp.c            # CRTP 协议实现
│   │       │       ├── power_distribution_stock.c # 功率分配（控制量→电机PWM）
│   │       │       ├── system.c          # 系统管理（任务启动、初始化）
│   │       │       ├── param.c            # 参数系统（运行时参数配置）
│   │       │       ├── log.c             # 日志系统（数据记录）
│   │       │       ├── comm.c             # 通信管理
│   │       │       ├── console.c          # 控制台输出
│   │       │       ├── sensfusion6.c     # 传感器融合实现
│   │       │       ├── pid.c             # PID 控制器实现
│   │       │       └── ...                # 其他模块实现
│   │       │
│   │       └── utils/            # 工具函数库
│   │           ├── interface/    # 工具接口（头文件，28个文件）
│   │           │   ├── cf_math.h         # Crazyflie 数学库
│   │           │   └── ...               # 其他工具接口
│   │           │
│   │           └── src/          # 工具实现（源文件，27个文件）
│   │               └── ...               # 其他工具实现
│   │
│   ├── drivers/                   # 🔧 驱动程序层
│   │   │
│   │   ├── general/               # 通用驱动
│   │   │   ├── adc/               # ADC 驱动（电池电压检测）
│   │   │   │   ├── adc_esp32.c
│   │   │   │   └── include/
│   │   │   │       └── adc.h
│   │   │   │
│   │   │   ├── motors/            # 电机 PWM 驱动
│   │   │   │   ├── motors.c              # 电机驱动实现
│   │   │   │   ├── motors_def_cf2.c      # Crazyflie 2.0 电机定义
│   │   │   │   └── include/
│   │   │   │       └── motors.h
│   │   │   │
│   │   │   ├── status_led/        # 状态 LED 驱动
│   │   │   │   ├── status_led.c
│   │   │   │   └── include/
│   │   │   │       └── status_led.h
│   │   │   │
│   │   │   └── wifi/              # Wi-Fi 驱动（AP 模式 + UDP）
│   │   │       ├── wifi_esp32.c          # Wi-Fi 和 UDP 实现
│   │   │       ├── config_receiver.c      # 配置接收器
│   │   │       └── include/
│   │   │           ├── wifi_esp32.h
│   │   │           └── config_receiver.h
│   │   │
│   │   ├── i2c_bus/               # I2C 总线驱动
│   │   │   ├── i2c_drv.c          # I2C 驱动实现
│   │   │   ├── i2cdev_esp32.c    # ESP32 I2C 设备抽象
│   │   │   └── include/
│   │   │       ├── i2c_drv.h
│   │   │       └── i2cdev.h
│   │   │
│   │   └── i2c_devices/           # I2C 设备驱动
│   │       └── mpu6050/           # MPU6050 IMU 驱动
│   │           ├── mpu6050.c      # MPU6050 驱动实现
│   │           └── include/
│   │               └── mpu6050.h
│   │
│   ├── platform/                  # 🖥️ 平台适配层
│   │   ├── platform.c             # 平台抽象接口
│   │   ├── platform_esp32.c      # ESP32 平台实现
│   │   ├── platform_cf2.c         # Crazyflie 2.0 平台实现（参考）
│   │   ├── platform.h             # 平台接口定义
│   │   └── stm32_legacy.h         # STM32 遗留代码兼容层
│   │
│   └── lib/                       # 📚 第三方库
│       └── dsp_lib/               # DSP 数学库（ARM CMSIS DSP 移植）
│           ├── BasicMathFunctions/    # 基础数学运算（加减乘除）
│           ├── FilteringFunctions/    # 滤波器函数（IIR、FIR）
│           ├── MatrixFunctions/       # 矩阵运算
│           ├── TransformFunctions/    # 变换函数（FFT、DCT）
│           ├── ComplexMathFunctions/  # 复数数学
│           ├── ControllerFunctions/   # 控制器函数（PID）
│           ├── FastMathFunctions/    # 快速数学（sin/cos）
│           ├── StatisticsFunctions/  # 统计函数
│           └── include/               # DSP 库头文件
│
├── managed_components/            # 📦 ESP-IDF 组件管理器管理的组件
│   └── espressif__led_strip/     # LED 灯带组件（如使用）
│
├── build/                         # 🔨 编译输出目录（自动生成）
│   ├── ESPDrone.elf              # 最终可执行文件
│   ├── ESPDrone.bin               # 二进制固件文件
│   └── ...                        # 其他编译中间文件
│
├── CMakeLists.txt                 # 项目根 CMake 配置
├── sdkconfig                      # ESP-IDF 配置文件（自动生成）
├── sdkconfig.defaults             # 默认配置
├── sdkconfig.defaults.esp32       # ESP32 特定默认配置
├── dependencies.lock              # 组件依赖锁定文件
├── README.md                      # 项目说明文档
└── LICENSE                        # 开源协议（GPL-3.0）
```

---

## 核心模块功能说明

### 1. System 系统模块 (`system.c`)

**功能**: 系统启动管理和任务协调

**主要职责**:
- 系统初始化流程管理
- 各模块启动顺序控制
- 系统状态管理（解锁/锁定、飞行许可）

**关键函数**:
```c
void systemLaunch(void)           // 启动系统任务
void systemWaitStart(void)        // 等待系统启动完成
bool systemCanFly(void)           // 检查是否允许飞行
bool systemIsArmed(void)          // 检查是否已解锁
```

**启动流程**:
```
app_main()
  └─▶ platformInit()              // 平台初始化
  └─▶ systemLaunch()               // 启动系统任务
      └─▶ systemTask()
          ├── wifiInit()           // Wi-Fi AP 初始化
          ├── telemetrySenderInit() // 遥测发送初始化
          ├── dataTransferInit()    // 数据传输任务初始化
          ├── systemInit()         // 核心子系统初始化
          │    ├── workerInit()    // 辅助工作任务
          │    ├── adcInit()       // ADC 初始化
          │    └── pmInit()        // 电源管理初始化
          ├── commInit()           // 通信管理初始化
          ├── commanderInit()      // 指令管理器初始化
          └── stabilizerInit()     // 飞行稳定器初始化
```

---

### 2. Stabilizer 稳定器模块 (`stabilizer.c`)

**功能**: 核心飞行控制循环，协调传感器、估计器和控制器

**运行频率**: 1000Hz（由传感器数据就绪信号触发）

**主循环流程**:
```c
void stabilizerTask(void* param) {
    while(1) {
        sensorsWaitDataReady();              // 等待传感器数据（阻塞）
        
        // 状态估计
        stateEstimator(&state, &sensorData, &control, tick);
        
        // 获取控制指令
        commanderGetSetpoint(&setpoint, &state);
        
        // 姿态控制器计算
        controller(&control, &setpoint, &sensorData, &state, tick);
        
        // 功率分配（控制量 → 电机PWM）
        if (systemIsArmed() && !emergencyStop) {
            powerDistribution(&control);
        } else {
            powerStop();
        }
        
        tick++;
    }
}
```

**关键数据结构**:
- `sensorData_t`: 传感器原始数据（加速度、陀螺仪）
- `state_t`: 估计状态（姿态、位置、速度）
- `setpoint_t`: 控制设定点（目标姿态、推力）
- `control_t`: 控制输出（roll/pitch/yaw/thrust）

---

### 3. Sensors 传感器模块 (`sensors_mpu6050.c`)

**功能**: MPU6050 IMU 数据采集和处理

**采样频率**: 1000Hz（由 MPU6050 中断触发）

**数据处理流程**:
```
MPU6050 (I2C设备)
  │ 中断触发 (GPIO20)
  ▼
sensorsTask (传感器任务)
  │
  ├─▶ I2C 读取原始数据 (14 bytes)
  ├─▶ 解析加速度和陀螺仪数据
  ├─▶ 陀螺仪偏置校准（启动时自动）
  ├─▶ 低通滤波
  │   ├─ 陀螺仪: 80Hz LPF
  │   └─ 加速度计: 30Hz LPF
  ├─▶ 加速度对齐校准
  ├─▶ 数据入队 (Queue)
  └─▶ 发送信号量通知 Stabilizer
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

**控制架构**: 级联 PID（角度环 + 角速度环）

```
期望姿态 (setpoint.attitude)
  │
  ▼
┌──────────────────┐
│   角度 PID 环     │  ← 实际姿态 (state.attitude)
│  (Attitude PID)  │
└────────┬─────────┘
         │ 期望角速度
         ▼
┌──────────────────┐     实际角速度
│  角速度 PID 环    │ ◀─────────── (sensorData.gyro)
│   (Rate PID)     │
└────────┬─────────┘
         │
         ▼
    控制输出量
(roll_torque, pitch_torque, yaw_torque)
```

**PID 参数**（可通过 cfclient 调整）:
- **角速度环**: `PID_RATE_ROLL_KP/KI/KD`, `PID_RATE_PITCH_KP/KI/KD`, `PID_RATE_YAW_KP/KI/KD`
- **角度环**: `PID_ROLL_KP/KI/KD`, `PID_PITCH_KP/KI/KD`, `PID_YAW_KP/KI/KD`

---

### 5. Estimator 状态估计器

**功能**: 融合传感器数据，估计飞行器状态

**支持的估计器**:

| 估计器        | 文件                        | 描述           | 资源占用 |
| ------------- | --------------------------- | -------------- | -------- |
| Complementary | `estimator_complementary.c` | 互补滤波器     | 低       |
| Kalman (EKF)  | `estimator_kalman.c`        | 扩展卡尔曼滤波 | 高       |

**互补滤波原理**:
```
加速度计 ──┐
(低频稳定) │    ┌─────────────┐
          ├───▶│ 互补滤波器   │───▶ 姿态估计
          │    │ α·acc +      │
陀螺仪 ───┘    │ (1-α)·gyro   │
(高频响应)    └─────────────┘
```

---

### 6. Commander 指令管理器 (`commander.c`)

**功能**: 管理控制设定点（setpoint），处理超时保护

**主要职责**:
- 接收并管理来自 CRTP 的控制指令
- 设定点优先级管理
- Watchdog 超时保护（无指令时自动停止）

**关键函数**:
```c
void commanderSetSetpoint(setpoint_t *setpoint, int priority)
void commanderGetSetpoint(setpoint_t *setpoint, state_t *state)
```

**设定点结构**:
```c
typedef struct setpoint_s {
    attitude_t attitude;      // 目标姿态（roll, pitch, yaw）
    float thrust;             // 目标推力
    point_t position;         // 目标位置（可选）
    velocity_t velocity;      // 目标速度（可选）
    // ... 模式标志
} setpoint_t;
```

---

### 7. Power Distribution 功率分配 (`power_distribution_stock.c`)

**功能**: 将控制量转换为四个电机的 PWM 值

**X 型布局电机分配公式**:
```
M1 = thrust + pitch + roll - yaw
M2 = thrust + pitch - roll + yaw
M3 = thrust - pitch - roll - yaw
M4 = thrust - pitch + roll + yaw
```

**电机布局**:
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

### 8. Simple Packet 通信协议 (`simple_packet.c`)

**功能**: 自定义轻量级通信协议，替代原有的 CRTP 协议

**数据包结构**:
```
┌──────────────────────────────────────────────────────────┐
│                  Simple Packet 数据包格式                 │
├──────────────┬────────────┬──────────────────┬───────────┤
│ PacketID     │ Length     │ Payload          │ Checksum  │
│ (1 byte)     │ (1 byte)   │ (0-120 bytes)    │ (1 byte)  │
└──────────────┴────────────┴──────────────────┴───────────┘
```

**核心模块说明**:
- **`data_sender.c`**: 独立的数据发送任务，包含高频任务（50Hz）发送姿态、PID输出、电机PWM、传感器原始数据，低频任务（1Hz）发送电池状态和PID参数响应。
- **`command_receiver.c`**: 解析来自上位机的飞行控制命令包（0x01），转换为飞控内部的设定点。
- **`config_receiver.c`**: 处理配置命令（PID参数配置等）。
- **`packet_codec.c`**: 提供数据包的打包、解析、序列化和校验功能。
- **`protocol_dispatcher.c`**: 协议分发器，接收UDP数据包并根据PacketID分发到对应的处理模块。

---

### 9. Wi-Fi 通信模块 (`wifi_esp32.c`)

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

### 10. Motors 电机驱动 (`motors.c`)

**功能**: PWM 电机控制

**配置**:
| 参数       | 值                  |
| ---------- | ------------------- |
| PWM 频率   | 15 kHz              |
| PWM 分辨率 | 10-bit (0-1023)     |
| 定时器     | LEDC_TIMER_0        |
| 速度模式   | LEDC_LOW_SPEED_MODE |

**GPIO 映射**（默认）:
| 电机 | GPIO   |
| ---- | ------ |
| M1   | GPIO5  |
| M2   | GPIO4  |
| M3   | GPIO10 |
| M4   | GPIO21 |

---

### 11. Power Management 电源管理 (`pm_esplane.c`)

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
| 状态   | 电压（单芯锂电） |
| ------ | ---------------- |
| 满电   | > 4.10V          |
| 正常   | 3.7V - 4.10V     |
| 低电量 | < 3.4V           |
| 临界   | < 3.0V           |

---

## 系统数据流详解

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
│  │ UDP_RX_Task │ ◀────────────────── │   手机 APP       │              │
│  │ (RX Task)   │                      │   (客户端)       │              │
│  └──────┬──────┘                      └─────────────────┘              │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ UDPPacket (CRTP格式 + 校验和)
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Wi-Fi Link 层 (wifilink.c)                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  1. 校验和验证                                                    │   │
│  │  2. 提取 CRTP 数据包                                             │   │
│  │  3. 入队到 CRTP 接收队列                                          │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ CRTPPacket
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
          │ setpoint_t (通过 commanderSetSetpoint)
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Commander 模块 (commander.c)                                            │
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
│  Stabilizer 稳定器 (stabilizer.c) - 主控制循环 @ 1000Hz                  │
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
│  Power Distribution 功率分配 (power_distribution_stock.c)                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  将控制量转换为四个电机的 PWM 值:                                   │   │
│  │  M1 = thrust + pitch + roll - yaw                               │   │
│  │  M2 = thrust + pitch - roll + yaw                               │   │
│  │  M3 = thrust - pitch - roll - yaw                               │   │
│  │  M4 = thrust - pitch + roll + yaw                               │   │
│  └──────┬──────────────────────────────────────────────────────────┘   │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ motorPower[4] (uint16_t, 0-65535)
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Motors 电机驱动 (motors.c)                                              │
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

### 传感器数据流

```
MPU6050 (I2C设备)
  │
  │ I2C 中断 (GPIO20)
  ▼
┌─────────────────────────────────────────────────────────┐
│  Sensors Task (sensors_mpu6050.c)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. I2C 读取原始数据 (14 bytes)                    │   │
│  │     - 加速度: 6 bytes (X, Y, Z, 16-bit)          │   │
│  │     - 陀螺仪: 6 bytes (X, Y, Z, 16-bit)          │   │
│  │     - 温度: 2 bytes                               │   │
│  │                                                    │   │
│  │  2. 数据解析和单位转换                              │   │
│  │     - 加速度: raw → g (重力加速度)                │   │
│  │     - 陀螺仪: raw → deg/s (度/秒)                 │   │
│  │                                                    │   │
│  │  3. 陀螺仪偏置校准 (启动时)                         │   │
│  │                                                    │   │
│  │  4. 低通滤波                                       │   │
│  │     - 陀螺仪: 80Hz LPF                            │   │
│  │     - 加速度计: 30Hz LPF                          │   │
│  │                                                    │   │
│  │  5. 加速度对齐校准                                 │   │
│  │                                                    │   │
│  │  6. 数据入队 (sensorDataQueue)                    │   │
│  │                                                    │   │
│  │  7. 发送信号量 (sensorsDataReady)                 │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │ sensorData_t
          ▼
┌─────────────────────────────────────────────────────────┐
│  Stabilizer Task                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  sensorsWaitDataReady()  // 等待信号量            │   │
│  │  sensorsAcquire(&sensorData, tick)              │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │ sensorData_t
          ▼
┌─────────────────────────────────────────────────────────┐
│  Estimator (estimator_complementary.c / estimator_kalman.c)│
│  ┌─────────────────────────────────────────────────┐   │
│  │  状态估计:                                         │   │
│  │  - 融合加速度计和陀螺仪数据                        │   │
│  │  - 计算姿态角 (roll, pitch, yaw)                 │   │
│  │  - 计算姿态四元数                                 │   │
│  │  - 估计位置和速度 (如果使用卡尔曼滤波)              │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │ state_t
          ▼
┌─────────────────────────────────────────────────────────┐
│  Controller (controller_pid.c)                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  使用 state_t 和 setpoint_t 计算控制量           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 日志数据流（上行）

```
┌─────────────────────────────────────────────────────────┐
│  各模块产生日志数据                                        │
│  - Stabilizer: 姿态、控制量                              │
│  - Sensors: 传感器原始数据                                │
│  - Estimator: 估计状态                                    │
│  - Power: 电池电压、电流                                  │
└─────────┬─────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│  Log 模块 (log.c)                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 日志变量注册 (log.c)                          │   │
│  │  - 数据打包                                       │   │
│  │  - 入队到 CRTP 发送队列                           │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │ CRTPPacket (Port 5)
          ▼
┌─────────────────────────────────────────────────────────┐
│  CRTP TX Task (crtp.c)                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 出队 CRTP 数据包                              │   │
│  │  - 添加 CRTP 头部                                 │   │
│  │  - 入队到 Wi-Fi 发送队列                          │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │ UDPPacket
          ▼
┌─────────────────────────────────────────────────────────┐
│  UDP TX Task (wifi_esp32.c)                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  - 添加校验和                                    │   │
│  │  - UDP 发送到客户端                               │   │
│  └──────┬────────────────────────────────────────────┘   │
└─────────┼─────────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────┐
    │   手机 APP      │
    │   (客户端)      │
    └─────────────────┘
```

---

## FreeRTOS 任务架构

### 任务列表

| 任务名         | 优先级 | 栈大小 | 功能                     | 文件                |
| -------------- | ------ | ------ | ------------------------ | ------------------- |
| **STABILIZER** | 5      | 5KB    | 飞行稳定控制（1000Hz）   | `stabilizer.c`      |
| **SENSORS**    | 4      | 5KB    | 传感器数据采集（1000Hz） | `sensors_mpu6050.c` |
| **DATA_XFER**  | 3      | 4KB    | 数据采集与定时传输(50Hz) | `data_transfer.c`   |
| **SYSTEM**     | 2      | 6KB    | 系统管理、初始化         | `system.c`          |
| **UDP_TX**     | 3      | 2KB    | UDP 发送                 | `wifi_esp32.c`      |
| **UDP_RX**     | 3      | 4KB    | UDP 接收                 | `wifi_esp32.c`      |
| **PWRMGNT**    | 0      | 4KB    | 电源管理                 | `pm_esplane.c`      |
| **LOG**        | 1      | 3KB    | 日志记录                 | `log.c`             |
| **PARAM**      | 2      | 2KB    | 参数管理                 | `param.c`           |
| **ADC**        | 3      | 1KB    | ADC 采样（电池电压）     | `adc_esp32.c`       |

### 任务优先级说明

- **优先级 5**: 最高优先级，用于实时性要求最高的任务（Stabilizer）
- **优先级 4**: 高优先级，用于传感器数据采集（Sensors）
- **优先级 3**: 中高优先级，用于通信、ADC 和数据传输任务
- **优先级 2**: 中等优先级，用于系统管理
- **优先级 1**: 低优先级，用于日志和参数
- **优先级 0**: 最低优先级，用于电源管理

### 任务间通信

**队列 (Queue)**:
- `udpDataRx`: UDP 接收队列（UDP_RX → Simple Commander）
- `setpointQueue`: 设定点队列（Simple Commander → Commander）

**信号量 (Semaphore)**:
- `sensorsDataReady`: 传感器数据就绪信号量（SENSORS → STABILIZER）

**全局变量 (Shared Variables)**:
- `sensorData`, `state`, `control`: 由 Data Transfer 任务读取并上报遥测数据。

**信号量 (Semaphore)**:
- `sensorsDataReady`: 传感器数据就绪信号量（SENSORS → STABILIZER）
**互斥锁 (Mutex)**:
- 用于保护共享资源（如参数、日志变量）

---

## 通信协议

ESP-FLY系统采用基于UDP的自定义Simple Packet协议进行通信。

协议详细说明请参考：**[ESP-FLY通信协议接口文档](./ESP-FLY通信协议接口文档.md)**

### 协议概述

- **协议类型**: Simple Packet Protocol（轻量级数据包协议）
- **传输层**: Wi-Fi UDP
- **设备IP**: 192.168.43.42
- **端口**: 2390
- **数据包格式**: PacketID (1B) + Length (1B) + Payload (0-120B) + Checksum (1B)

### 协议模块

本项目中与通信协议相关的核心模块：

- **`packet_codec.c/h`**: 数据包的打包、解析与编解码
- **`command_receiver.c/h`**: 接收并处理飞行控制命令（0x01）
- **`config_receiver.c/h`**: 接收并处理配置命令（PID参数等）
- **`data_sender.c/h`**: 定时采集并发送高频飞行数据（50Hz）和低频数据（1Hz）
- **`protocol_dispatcher.c/h`**: 协议分发器，根据PacketID路由数据包

---

## 配置系统

### Kconfig 配置项

通过 `idf.py menuconfig` 进入 **"ESPDrone Config"** 菜单:

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

### 运行时参数系统

可以通过上位机或 APP 动态调整参数：

**PID 参数**:
- `pid_attitude.pitch_kp`, `pid_attitude.pitch_ki`, `pid_attitude.pitch_kd`
- `pid_attitude.roll_kp`, `pid_attitude.roll_ki`, `pid_attitude.roll_kd`
- `pid_attitude.yaw_kp`, `pid_attitude.yaw_ki`, `pid_attitude.yaw_kd`
- `pid_rate.pitch_kp`, `pid_rate.pitch_ki`, `pid_rate.pitch_kd`
- `pid_rate.roll_kp`, `pid_rate.roll_ki`, `pid_rate.roll_kd`
- `pid_rate.yaw_kp`, `pid_rate.yaw_ki`, `pid_rate.yaw_kd`

**传感器参数**:
- `imu_sensors.gyro_cutoff`
- `imu_sensors.acc_cutoff`

**系统参数**:
- `system.arm`
- `system.canFly`

---

## 关键数据结构

### sensorData_t（传感器数据）

```c
typedef struct sensorData_s {
    Axis3f acc;               // 加速度 (Gs)
    Axis3f gyro;              // 角速度 (deg/s)
    Axis3f mag;               // 磁力计 (gauss，可选)
    baro_t baro;             // 气压计 (可选)
    uint64_t interruptTimestamp; // 中断时间戳
} sensorData_t;
```

### state_t（估计状态）

```c
typedef struct state_s {
    attitude_t attitude;              // 姿态角 (deg)
    quaternion_t attitudeQuaternion;  // 姿态四元数
    point_t position;                // 位置 (m)
    velocity_t velocity;              // 速度 (m/s)
    acc_t acc;                       // 加速度 (Gs)
} state_t;
```

### setpoint_t（控制设定点）

```c
typedef struct setpoint_s {
    uint32_t timestamp;
    attitude_t attitude;      // 目标姿态 (deg)
    attitude_t attitudeRate;  // 目标角速度 (deg/s)
    quaternion_t attitudeQuaternion; // 目标姿态四元数
    float thrust;             // 目标推力 (0.0 ~ 1.0)
    point_t position;         // 目标位置 (m)
    velocity_t velocity;       // 目标速度 (m/s)
    acc_t acceleration;       // 目标加速度 (m/s^2)
    // 模式标志
    struct {
        stab_mode_t x, y, z;
        stab_mode_t roll, pitch, yaw, quat;
    } mode;
} setpoint_t;
```

### control_t（控制输出）

```c
typedef struct control_s {
    int16_t roll;    // 横滚控制量
    int16_t pitch;   // 俯仰控制量
    int16_t yaw;     // 偏航控制量
    float thrust;    // 推力 (0.0 ~ 1.0)
} control_t;
```

---

## 编译和烧录

### 开发环境设置

```bash
# 1. 设置 ESP-IDF 环境
. $HOME/esp/esp-idf/export.sh

# 2. 进入项目目录
cd ESP-FLY-MCU

# 3. 配置目标芯片
idf.py set-target esp32

# 4. 配置项目（可选）
idf.py menuconfig

# 5. 编译
idf.py build

# 6. 烧录
idf.py -p COM3 flash

# 7. 监控串口输出
idf.py -p COM3 monitor
```

### 常用命令

```bash
# 清理编译文件
idf.py fullclean

# 查看项目大小
idf.py size

# 查看组件依赖
idf.py show_efuse_table
```

---

## 调试和日志

### 串口调试

- **波特率**: 115200
- **调试模块**: 通过 `DEBUG_MODULE` 宏定义
- **调试级别**: `DEBUG_PRINT`, `DEBUG_PRINT_LOCAL`, `DEBUG_PRINTI`

### 遥测日志 (WiFi)

系统不再使用 CRTP Log 订阅机制，而是通过 `data_transfer` 任务主动推送高频遥测数据包 (`PKT_ID_HIGH_FREQ_DATA`)。上位机解析该包即可获得：
- 姿态角 (Roll/Pitch/Yaw)
- 传感器原始数据 (Acc/Gyro)
- 控制量与 PID 期望值
- 电机 PWM 状态
- 电池电量与状态 (1Hz)

---

## 参考资料

- [ESP-IDF 文档](https://docs.espressif.com/projects/esp-idf/en/release-v4.4/esp32/)
- [Crazyflie 固件](https://github.com/bitcraze/crazyflie-firmware)
- [Crazyflie 客户端](https://github.com/bitcraze/crazyflie-clients-python)

---

## 版本历史

- **V5_1**: 当前版本
  - 基于 ESP-IDF v5.4
  - 支持 Wi-Fi AP 模式
  - 支持手机 APP 控制

---

**文档版本**: 1.0  
**最后更新**: 2026年
