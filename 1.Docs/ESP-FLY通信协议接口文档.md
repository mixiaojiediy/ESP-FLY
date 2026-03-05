# ESP-FLY 通信协议接口文档

## 1. 网络配置

| 参数            | 值                 |
| --------------- | ------------------ |
| 设备IP          | `192.168.43.42`    |
| UDP广播发送端口 | `2399`             |
| UDP单播接收端口 | `2390`             |
| 通信模式        | UDP                |
| SSID            | `ESP-DRONE_XXXXXX` | (XXXXXX采用MAC地址后六位) |
| 密码            | `12345678`         |

## 2. 通用包格式

```
+----------+---------+-------------------+----------+
| PacketID | Length  |      Payload      | Checksum |
|  1 byte  | 1 byte  |   0~120 bytes     |  1 byte  |
+----------+---------+-------------------+----------+
```

- **Checksum** = (PacketID + Length + 所有Payload字节) 累加取低8位
- **字节序**: 小端序（Little-Endian）

## 3. PacketID 定义

### 上行（PC/APP → MCU）

| PacketID | 名称     | Payload |
| -------- | -------- | ------- |
| `0x01`   | 飞行控制 | 14B     |
| `0x02`   | PID配置  | 36B     |
| `0x03`   | 电机测试 | 9B      |

### 下行（MCU → PC/APP）

| PacketID | 名称     | Payload | 频率 |
| -------- | -------- | ------- | ---- |
| `0x81`   | 高频数据 | 52B     | 50Hz |
| `0x82`   | 电池状态 | 4B      | 1Hz  |
| `0x83`   | PID响应  | 36B     | 1Hz  |

## 4. Payload 详细定义

### 4.1 飞行控制（0x01） 14 bytes

| 偏移 | 字段   | 类型   | 大小 | 范围               |
| ---- | ------ | ------ | ---- | ------------------ |
| 0    | Roll   | float  | 4B   | -30.0 ~ +30.0 度   |
| 4    | Pitch  | float  | 4B   | -30.0 ~ +30.0 度   |
| 8    | Yaw    | float  | 4B   | -180.0 ~ +180.0 度 |
| 12   | Thrust | uint16 | 2B   | 0 ~ 65535          |

### 4.2 PID配置（0x02） 36 bytes

单级PID控制，仅角度环，3轴 × 3参数 = 9个float。

| 偏移 | 字段           | 类型  | 大小 |
| ---- | -------------- | ----- | ---- |
| 0    | roll_angle_kp  | float | 4B   |
| 4    | roll_angle_ki  | float | 4B   |
| 8    | roll_angle_kd  | float | 4B   |
| 12   | pitch_angle_kp | float | 4B   |
| 16   | pitch_angle_ki | float | 4B   |
| 20   | pitch_angle_kd | float | 4B   |
| 24   | yaw_angle_kp   | float | 4B   |
| 28   | yaw_angle_ki   | float | 4B   |
| 32   | yaw_angle_kd   | float | 4B   |

### 4.3 电机测试（0x03） 9 bytes

| 偏移 | 字段       | 类型   | 大小 |
| ---- | ---------- | ------ | ---- |
| 0    | motor1_pwm | uint16 | 2B   |
| 2    | motor2_pwm | uint16 | 2B   |
| 4    | motor3_pwm | uint16 | 2B   |
| 6    | motor4_pwm | uint16 | 2B   |
| 8    | enable     | uint8  | 1B   |

enable: 0=停止, 1=启用测试

### 4.4 高频飞行数据（0x81） 52 bytes

| 偏移 | 字段         | 类型   | 大小 |
| ---- | ------------ | ------ | ---- |
| 0    | roll         | float  | 4B   |
| 4    | pitch        | float  | 4B   |
| 8    | yaw          | float  | 4B   |
| 12   | rollControl  | int16  | 2B   |
| 14   | pitchControl | int16  | 2B   |
| 16   | yawControl   | int16  | 2B   |
| 18   | motor1       | uint16 | 2B   |
| 20   | motor2       | uint16 | 2B   |
| 22   | motor3       | uint16 | 2B   |
| 24   | motor4       | uint16 | 2B   |
| 26   | gyroX        | float  | 4B   |
| 30   | gyroY        | float  | 4B   |
| 34   | gyroZ        | float  | 4B   |
| 38   | accX         | float  | 4B   |
| 42   | accY         | float  | 4B   |
| 46   | accZ         | float  | 4B   |
| 50   | timestamp    | uint16 | 2B   |

### 4.5 电池状态（0x82） 4 bytes

| 偏移 | 字段    | 类型  | 大小 |
| ---- | ------- | ----- | ---- |
| 0    | voltage | float | 4B   |

单位：伏特（V）

### 4.6 PID响应（0x83） 36 bytes

| 偏移 | 字段           | 类型  | 大小 |
| ---- | -------------- | ----- | ---- |
| 0    | roll_angle_kp  | float | 4B   |
| 4    | roll_angle_ki  | float | 4B   |
| 8    | roll_angle_kd  | float | 4B   |
| 12   | pitch_angle_kp | float | 4B   |
| 16   | pitch_angle_ki | float | 4B   |
| 20   | pitch_angle_kd | float | 4B   |
| 24   | yaw_angle_kp   | float | 4B   |
| 28   | yaw_angle_ki   | float | 4B   |
| 32   | yaw_angle_kd   | float | 4B   |
