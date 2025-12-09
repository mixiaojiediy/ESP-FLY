# ESP-FLY 微型四旋翼无人机 DIY 项目

> 🚁 一个基于 ESP32-C3 的开源微型无人机项目，从硬件设计到手机APP全栈开发

![ESP-FLY](../产品图/Snipaste_2025-06-21_11-23-07.jpg)

---

## 📖 项目简介

ESP-FLY 是一个完整的微型四旋翼无人机 DIY 项目，涵盖硬件设计、嵌入式固件开发和手机APP控制三个部分。项目核心飞控算法基于著名开源飞控 [Crazyflie](https://github.com/bitcraze/crazyflie-firmware)，并针对 ESP32-C3 平台进行了优化适配。

### ✨ 项目亮点

- 🔧 **全开源** - 硬件设计、固件代码、APP源码全部开源
- 📱 **手机控制** - 通过WiFi直连，手机APP实时遥控
- 🎮 **双摇杆操控** - 仿真实遥控器的操控体验
- ⚡ **快速响应** - 1000Hz飞控主循环，低延迟通信
- 🛡️ **安全机制** - 电池低压保护、信号丢失保护、紧急停止

---

## 🔩 一、硬件部分

### 核心组件

| 组件 | 型号/规格 | 说明 |
|------|-----------|------|
| 主控芯片 | **Seeed XIAO ESP32-C3** | 小巧、低功耗、集成WiFi |
| 姿态传感器 | **MPU6050** | 六轴IMU（加速度计+陀螺仪） |
| 电机 | **715/720 有刷空心杯电机** ×4 | 微型无人机专用 |
| 电调 | **AO3401A P-MOS** | 直接PWM驱动有刷电机 |
| 电池 | **1S 锂电池 300-400mAh** | 轻量化电源 |
| 机架 | **3D打印 PLA** | 自行设计的X型机架 |

### 引脚定义

```
GPIO 6  → I2C SCL (MPU6050)
GPIO 7  → I2C SDA (MPU6050)
GPIO 20 → MPU6050 中断
GPIO 3  → 电池电压 ADC
GPIO 5  → 电机1 (前左)
GPIO 4  → 电机2 (前右)
GPIO 10 → 电机3 (后左)
GPIO 21 → 电机4 (后右)
```

### 电机布局（X型）

```
      ↑ 机头方向
    M1       M2
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

### 硬件资源

- 📄 原理图（立创EDA设计）
- 📄 PCB Gerber 文件
- 📄 交互式BOM
- 📄 3D打印机架模型（.3mf）
- 📄 MCU STEP 模型

---

## 💻 二、嵌入式固件

### 技术栈

- **开发框架**: ESP-IDF v4.4
- **编程语言**: C
- **操作系统**: FreeRTOS
- **通信协议**: CRTP (Crazyflie Real-Time Protocol)

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Application)                      │
│   Commander │ Stabilizer │ System │ Communication           │
├─────────────────────────────────────────────────────────────┤
│                    核心模块层 (Core Modules)                   │
│   Controller │ Estimator │ Sensors │ CRTP Protocol          │
├─────────────────────────────────────────────────────────────┤
│                    硬件抽象层 (HAL)                            │
│   Motors │ MPU6050 │ Power Management │ WiFi/UDP            │
├─────────────────────────────────────────────────────────────┤
│                    ESP32-C3 硬件平台                          │
│           GPIO/PWM │ I2C │ ADC │ WiFi                       │
└─────────────────────────────────────────────────────────────┘
```

### 核心功能模块

#### 🎯 飞行控制
- **姿态解算**: 互补滤波 / 扩展卡尔曼滤波 (EKF)
- **PID控制器**: 级联PID（角度环 + 角速度环）
- **控制频率**: 1000Hz 主循环

#### 📡 通信系统
- **WiFi模式**: AP热点模式
- **默认SSID**: `ESP-DRONE_XXXXXXXXXXXX`
- **默认密码**: `12345678`
- **通信协议**: UDP + CRTP
- **默认IP**: `192.168.43.42`
- **UDP端口**: `2390`

#### 🔋 电源管理
- 实时电池电压监测
- 多级低压保护
- 充电状态检测

#### 🛡️ 安全机制
- 解锁条件检查（姿态角度 < 15°）
- 信号丢失自动停机（1秒超时）
- 姿态角度限制（±45°）
- 紧急停止功能

### FreeRTOS 任务

| 任务名 | 优先级 | 功能 |
|--------|--------|------|
| STABILIZER | 5 | 飞行稳定控制（核心） |
| SENSORS | 4 | 传感器数据采集 |
| UDP_TX/RX | 3 | WiFi UDP 收发 |
| SYSTEM | 2 | 系统管理 |
| CRTP | 2 | 通信协议处理 |
| PWRMGNT | 0 | 电源管理 |

### 编译与烧录

```bash
# 设置 ESP-IDF 环境
. $HOME/esp/esp-idf/export.sh

# 配置目标芯片
idf.py set-target esp32c3

# 编译
idf.py build

# 烧录
idf.py -p COM3 flash

# 监控串口
idf.py -p COM3 monitor
```

---

## 📱 三、Android APP

### 技术栈

- **开发语言**: Kotlin
- **UI框架**: Jetpack Compose
- **架构模式**: MVVM
- **主题风格**: Material Design 3
- **最低SDK**: Android 8.0 (API 26)

### 功能特性

#### 🎮 双摇杆控制
- **左摇杆**: 油门控制（上半区域有效，松手回中）
- **右摇杆**: 姿态控制（Roll/Pitch，支持全向）

#### 📊 实时状态显示
- 连接状态指示
- 电池电量百分比
- 电池电压实时显示
- 飞行姿态数据（Roll/Pitch/Yaw）
- 油门百分比

#### 🛠️ 辅助功能
- 控制台日志实时显示
- 紧急停止按钮
- 设置界面
- 全屏沉浸式模式

### 界面预览

```
┌────────────────────────────────────────────────────────┐
│  T:0%  R:0°  P:0°  Y:0°     [WiFi] [🔋85% 3.95V] [⚙️] │
├────────────────────────────────────────────────────────┤
│                                                        │
│   ┌─────┐         ┌──────────┐         ┌─────┐       │
│   │     │         │  控制台   │         │     │       │
│   │ 油门 │         │ > 已连接  │         │ 姿态 │       │
│   │     │         │ > 解锁成功│         │     │       │
│   └─────┘         │ > ...    │         └─────┘       │
│                   └──────────┘                        │
│                  [🚨 紧急停止 ]                        │
└────────────────────────────────────────────────────────┘
```

### 通信协议

**控制指令（10字节）**:
```
cmd_type(1) + throttle(2) + roll(2) + pitch(2) + yaw(2) + checksum(1)
```

**状态回传（11字节）**:
```
roll(2) + pitch(2) + yaw(2) + battery(2) + status(1) + checksum(1)
```

---

## 🚀 快速开始

### 1️⃣ 硬件准备
1. 按照原理图焊接PCB
2. 3D打印机架并组装
3. 连接电机和电池

### 2️⃣ 固件烧录
1. 安装 ESP-IDF v4.4
2. 克隆项目代码
3. 编译并烧录固件

### 3️⃣ APP安装
1. 编译 Android APP 或安装预编译APK
2. 手机连接无人机WiFi热点
3. 打开APP开始飞行！

---

## 📂 项目结构

```
250616_ESP_FLY/
├── 1.3D_Model/              # 3D打印模型
├── 2.Docs/                  # 项目文档
├── 3.Firmware/
│   └── ESP-FLY/             # 主固件项目 (ESP-IDF)
│       ├── components/      # 组件模块
│       │   ├── core/        # Crazyflie核心飞控
│       │   ├── drivers/     # 硬件驱动
│       │   ├── config/      # 配置文件
│       │   ├── platform/    # 平台适配
│       │   └── lib/         # DSP数学库
│       └── main/            # 主程序入口
├── 4.Hardware/              # 硬件设计文件
│   ├── Schematic            # 原理图
│   ├── InteractiveBOM       # 交互式BOM
│   └── Datasheet/           # 元器件手册
├── 5.Software/
│   ├── ESP-FLY-APP/         # Android APP (Kotlin)
│   └── ESP-FLY-PY/          # Python控制工具
└── 6.Video/                 # 演示视频
```

---

## 📜 开源协议

- **固件**: GPL-3.0 (继承自 Crazyflie)
- **APP**: MIT License

### 致谢

- [Bitcraze Crazyflie](https://www.bitcraze.io/) - 核心飞控算法
- [乐鑫 ESP-IDF](https://docs.espressif.com/projects/esp-idf/) - 开发框架
- [Seeed Studio](https://www.seeedstudio.com/) - XIAO ESP32-C3

---

## 🤝 联系与贡献

欢迎 Star ⭐、Fork 🍴 和提交 PR！

如有问题或建议，请提交 Issue。

---

**Happy Flying! 🚁✨**

