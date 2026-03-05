/**
 * Packet Protocol - 数据包协议
 *
 * 替代CRTP协议，使用固定位宽的数据包格式
 * 数据包格式: PacketID(1) + Length(1) + Payload(0-120) + Checksum(1)
 */

#ifndef __PACKET_CODEC_H__
#define __PACKET_CODEC_H__

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#ifdef __cplusplus
extern "C"
{
#endif

    // ============================================================================
    // 常量定义
    // ============================================================================

#define PACKET_MAX_PAYLOAD_SIZE 120 // 最大payload长度
#define PACKET_HEADER_SIZE 2        // PacketID + Length
#define PACKET_CHECKSUM_SIZE 1      // Checksum
#define PACKET_MAX_SIZE (PACKET_HEADER_SIZE + PACKET_MAX_PAYLOAD_SIZE + PACKET_CHECKSUM_SIZE)

    // ============================================================================
    // 数据包类型定义 (PacketID)
    // ============================================================================

    // 上行数据包 (PC/APP → MCU)
    typedef enum
    {
        PKT_ID_FLIGHT_CONTROL = 0x01, // 飞行控制命令
        PKT_ID_PID_CONFIG = 0x02,     // PID参数配置
        PKT_ID_MOTOR_TEST = 0x03,     // 电机测试
    } PacketID_Uplink;

    // 下行数据包 (MCU → PC/APP)
    typedef enum
    {
        PKT_ID_HIGH_FREQ_DATA = 0x81, // 高频飞行数据 (50Hz)
        PKT_ID_BATTERY_STATUS = 0x82, // 电池状态 (1Hz)
        PKT_ID_PID_RESPONSE = 0x83,   // PID参数响应
    } PacketID_Downlink;

    // ============================================================================
    // 数据包结构体定义
    // ============================================================================

    /**
     * 通用数据包结构
     */
    typedef struct
    {
        uint8_t packet_id;                        // 数据包ID
        uint8_t length;                           // Payload长度
        uint8_t payload[PACKET_MAX_PAYLOAD_SIZE]; // 有效载荷
        uint8_t checksum;                         // 校验和 (自动计算)
    } __attribute__((packed)) PacketFrame_t;

    /**
     * 飞行控制命令包 (0x01) - 14 bytes payload
     */
    typedef struct
    {
        float roll;      // 横滚角度 (度)
        float pitch;     // 俯仰角度 (度)
        float yaw;       // 偏航角度 (度，±180)
        uint16_t thrust; // 推力值 (0-65535)
    } __attribute__((packed)) FlightControlPacket_t;

    /**
     * 高频飞行数据包 (0x81) - 64 bytes payload
     */
    typedef struct
    {
        // 姿态角 (12 bytes)
        float roll;
        float pitch;
        float yaw;

        // 期望角速度 (12 bytes)
        float rollRateDesired;
        float pitchRateDesired;
        float yawRateDesired;

        // 控制输出 (6 bytes)
        int16_t rollControl;
        int16_t pitchControl;
        int16_t yawControl;

        // 电机PWM (8 bytes)
        uint16_t motor1;
        uint16_t motor2;
        uint16_t motor3;
        uint16_t motor4;

        // 陀螺仪数据 (12 bytes) - deg/s
        float gyroX;
        float gyroY;
        float gyroZ;

        // 加速度计数据 (12 bytes) - Gs
        float accX;
        float accY;
        float accZ;

        // 时间戳 (2 bytes)
        uint16_t timestamp;
    } __attribute__((packed)) HighFreqDataPacket_t;

    /**
     * 电池状态包 (0x82) - 8 bytes payload
     */
    typedef struct
    {
        float voltage;       // 电池电压 (V)
        uint16_t voltage_mv; // 电池电压 (mV)
        uint8_t level;       // 电量百分比 (0-100)
        uint8_t state;       // 电池状态
    } __attribute__((packed)) BatteryStatusPacket_t;

    /**
     * PID参数配置包 (0x02) - 72 bytes payload
     * 一次性发送所有6组PID参数（姿态环和速度环）
     */
    typedef struct
    {
        // 姿态环 PID参数
        float roll_angle_kp; // Roll姿态环 - 比例系数
        float roll_angle_ki; // Roll姿态环 - 积分系数
        float roll_angle_kd; // Roll姿态环 - 微分系数

        float pitch_angle_kp; // Pitch姿态环 - 比例系数
        float pitch_angle_ki; // Pitch姿态环 - 积分系数
        float pitch_angle_kd; // Pitch姿态环 - 微分系数

        float yaw_angle_kp; // Yaw姿态环 - 比例系数
        float yaw_angle_ki; // Yaw姿态环 - 积分系数
        float yaw_angle_kd; // Yaw姿态环 - 微分系数

        // 速度环 PID参数
        float roll_rate_kp; // Roll速度环 - 比例系数
        float roll_rate_ki; // Roll速度环 - 积分系数
        float roll_rate_kd; // Roll速度环 - 微分系数

        float pitch_rate_kp; // Pitch速度环 - 比例系数
        float pitch_rate_ki; // Pitch速度环 - 积分系数
        float pitch_rate_kd; // Pitch速度环 - 微分系数

        float yaw_rate_kp; // Yaw速度环 - 比例系数
        float yaw_rate_ki; // Yaw速度环 - 积分系数
        float yaw_rate_kd; // Yaw速度环 - 微分系数
    } __attribute__((packed)) PIDConfigPacket_t;

    /**
     * 电机测试包 (0x03) - 9 bytes payload
     */
    typedef struct
    {
        uint16_t motor1_pwm; // 电机1 PWM占空比 (0-65535)
        uint16_t motor2_pwm; // 电机2 PWM占空比 (0-65535)
        uint16_t motor3_pwm; // 电机3 PWM占空比 (0-65535)
        uint16_t motor4_pwm; // 电机4 PWM占空比 (0-65535)
        uint8_t enable;      // 测试使能: 0=停止, 1=启用测试
    } __attribute__((packed)) MotorTestPacket_t;

    // ============================================================================
    // 函数接口
    // ============================================================================

    /**
     * 计算校验和
     * @param data 数据缓冲区
     * @param len 数据长度
     * @return 校验和 (所有字节累加的低8位)
     */
    uint8_t packet_calculateChecksum(const uint8_t *data, uint16_t len);

    /**
     * 验证数据包校验和
     * @param data 完整数据包 (包含checksum)
     * @param len 数据包总长度
     * @return true=校验通过, false=校验失败
     */
    bool packet_verifyChecksum(const uint8_t *data, uint16_t len);

    /**
     * 打包数据为PacketFrame
     * @param packet 输出的数据包结构
     * @param packet_id 数据包ID
     * @param payload 有效载荷数据
     * @param payload_len 有效载荷长度
     * @return true=成功, false=失败
     */
    bool packet_pack(PacketFrame_t *packet, uint8_t packet_id,
                     const uint8_t *payload, uint8_t payload_len);

    /**
     * 将PacketFrame序列化为字节流 (用于UDP发送)
     * @param packet 数据包结构
     * @param buffer 输出缓冲区
     * @param buffer_size 缓冲区大小
     * @return 实际写入的字节数 (0表示失败)
     */
    uint16_t packet_serialize(const PacketFrame_t *packet, uint8_t *buffer, uint16_t buffer_size);

    /**
     * 从字节流解析PacketFrame (UDP接收后解析)
     * @param buffer 输入缓冲区
     * @param buffer_len 缓冲区长度
     * @param packet 输出的数据包结构
     * @return true=成功, false=失败 (校验和错误或格式错误)
     */
    bool packet_parse(const uint8_t *buffer, uint16_t buffer_len, PacketFrame_t *packet);

    /**
     * 解析飞行控制命令包
     * @param packet 数据包结构
     * @param fc_packet 输出的飞行控制数据
     * @return true=成功, false=失败
     */
    bool packet_parseFlightControl(const PacketFrame_t *packet, FlightControlPacket_t *fc_packet);

    /**
     * 创建高频飞行数据包
     * @param buffer 输出缓冲区
     * @param buffer_size 缓冲区大小
     * @param hf_data 高频数据结构
     * @return 数据包长度 (0表示失败)
     */
    uint16_t packet_createHighFreqData(uint8_t *buffer, uint16_t buffer_size,
                                       const HighFreqDataPacket_t *hf_data);

    /**
     * 创建电池状态包
     * @param buffer 输出缓冲区
     * @param buffer_size 缓冲区大小
     * @param battery 电池状态数据
     * @return 数据包长度 (0表示失败)
     */
    uint16_t packet_createBatteryStatus(uint8_t *buffer, uint16_t buffer_size,
                                        const BatteryStatusPacket_t *battery);

    /**
     * 创建PID参数响应包
     * @param buffer 输出缓冲区
     * @param buffer_size 缓冲区大小
     * @param pid_config PID配置数据
     * @return 数据包长度 (0表示失败)
     */
    uint16_t packet_createPIDResponse(uint8_t *buffer, uint16_t buffer_size,
                                      const PIDConfigPacket_t *pid_config);

    /**
     * 解析PID配置包
     * @param packet 数据包结构
     * @param pid_config 输出的PID配置数据
     * @return true=成功, false=失败
     */
    bool packet_parsePIDConfig(const PacketFrame_t *packet, PIDConfigPacket_t *pid_config);

    /**
     * 解析电机测试包
     * @param packet 数据包结构
     * @param motor_test 输出的电机测试数据
     * @return true=成功, false=失败
     */
    bool packet_parseMotorTest(const PacketFrame_t *packet, MotorTestPacket_t *motor_test);

#ifdef __cplusplus
}
#endif

#endif // __PACKET_CODEC_H__
