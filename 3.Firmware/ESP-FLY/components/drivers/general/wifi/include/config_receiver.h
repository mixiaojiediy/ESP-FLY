/**
 * ESP-Drone 配置接收模块
 *
 * 此模块用于接收APP通过WiFi下发的配置信息
 */

#ifndef CONFIG_RECEIVER_H_
#define CONFIG_RECEIVER_H_

#include <stdint.h>
#include <stdbool.h>

// 配置命令类型定义
#define CONFIG_CMD_WIFI_SSID 0x01      // WiFi SSID配置
#define CONFIG_CMD_WIFI_PASSWORD 0x02  // WiFi 密码配置
#define CONFIG_CMD_FLIGHT_PARAMS 0x03  // 飞行参数配置
#define CONFIG_CMD_PID_PARAMS 0x04     // PID参数配置
#define CONFIG_CMD_DEVICE_NAME 0x05    // 设备名称配置
#define CONFIG_CMD_GENERAL_CONFIG 0x06 // 通用配置
#define CONFIG_CMD_TEST 0xFF           // 测试命令

// 配置数据包结构
typedef struct
{
    uint8_t cmd_type; // 命令类型
    uint8_t data_len; // 数据长度
    uint8_t data[62]; // 配置数据（最大62字节）
} __attribute__((packed)) ConfigPacket;

// WiFi配置结构
typedef struct
{
    char ssid[32];
    char password[64];
    uint8_t channel;
} WiFiConfig;

// 飞行参数配置
typedef struct
{
    float max_speed;     // 最大速度
    float max_altitude;  // 最大高度
    uint8_t flight_mode; // 飞行模式
} FlightConfig;

// PID参数配置 (与APP发送格式一致)
typedef struct
{
    uint8_t axis;      // 控制轴 (0:Roll, 1:Pitch, 2:Yaw)
    float kp;          // 比例系数
    float ki;          // 积分系数
    float kd;          // 微分系数
    uint8_t isRateLoop; // 1=角速度环, 0=姿态环
} __attribute__((packed)) PIDConfig;

// 配置命令响应类型
#define CONFIG_CMD_PID_QUERY 0x84    // PID参数查询(0x04 | 0x80)

/**
 * 初始化配置接收模块
 */
void configReceiverInit(void);

/**
 * 处理接收到的配置数据
 * @param data 接收到的数据
 * @param len 数据长度
 * @return true:成功处理，false:处理失败
 */
bool configReceiverProcess(uint8_t *data, uint32_t len);

/**
 * 打印配置信息
 * @param config 配置数据包指针
 */
void configReceiverPrint(ConfigPacket *config);

/**
 * 应用PID参数到飞控
 * @param pid PID参数配置
 */
void configReceiverApplyPID(PIDConfig *pid);

/**
 * 发送所有PID参数给APP
 */
void configReceiverSendAllPID(void);

#endif // CONFIG_RECEIVER_H_
