/**
 * ESP-Drone 配置接收模块实现
 */

#include <string.h>
#include <stdio.h>
#include "config_receiver.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "pid.h"
#include "console.h"

#define DEBUG_MODULE "CONFIG_RX"
#include "debug_cf.h"

// 引用attitude_pid_controller.c中的全局PID对象
extern PidObject pidRollRate;
extern PidObject pidPitchRate;
extern PidObject pidYawRate;
extern PidObject pidRoll;
extern PidObject pidPitch;
extern PidObject pidYaw;

static bool isInit = false;

/**
 * 初始化配置接收模块
 */
void configReceiverInit(void)
{
    if (isInit) {
        return;
    }
    
    DEBUG_PRINT_LOCAL("配置接收模块初始化完成");
    isInit = true;
}

/**
 * 打印配置信息
 */
void configReceiverPrint(ConfigPacket *config)
{
    if (config == NULL) {
        return;
    }
    
    DEBUG_PRINT_LOCAL("========================================");
    DEBUG_PRINT_LOCAL("收到APP配置信息:");
    DEBUG_PRINT_LOCAL("命令类型: 0x%02X", config->cmd_type);
    DEBUG_PRINT_LOCAL("数据长度: %d", config->data_len);
    
    switch (config->cmd_type) {
        case CONFIG_CMD_WIFI_SSID: {
            char ssid[33] = {0};
            memcpy(ssid, config->data, config->data_len > 32 ? 32 : config->data_len);
            DEBUG_PRINT_LOCAL("配置类型: WiFi SSID");
            DEBUG_PRINT_LOCAL("SSID: %s", ssid);
            break;
        }
        
        case CONFIG_CMD_WIFI_PASSWORD: {
            char password[65] = {0};
            memcpy(password, config->data, config->data_len > 64 ? 64 : config->data_len);
            DEBUG_PRINT_LOCAL("配置类型: WiFi 密码");
            DEBUG_PRINT_LOCAL("密码: %s", password);
            break;
        }
        
        case CONFIG_CMD_FLIGHT_PARAMS: {
            if (config->data_len >= sizeof(FlightConfig)) {
                FlightConfig *fc = (FlightConfig *)config->data;
                DEBUG_PRINT_LOCAL("配置类型: 飞行参数");
                DEBUG_PRINT_LOCAL("最大速度: %.2f m/s", fc->max_speed);
                DEBUG_PRINT_LOCAL("最大高度: %.2f m", fc->max_altitude);
                DEBUG_PRINT_LOCAL("飞行模式: %d", fc->flight_mode);
            }
            break;
        }
        
        case CONFIG_CMD_PID_PARAMS: {
            if (config->data_len >= sizeof(PIDConfig)) {
                PIDConfig *pid = (PIDConfig *)config->data;
                const char *axis_names[] = {"Roll", "Pitch", "Yaw"};
                const char *loop_names[] = {"姿态环", "角速度环"};
                DEBUG_PRINT_LOCAL("配置类型: PID参数");
                DEBUG_PRINT_LOCAL("控制环: %s", loop_names[pid->isRateLoop ? 1 : 0]);
                DEBUG_PRINT_LOCAL("控制轴: %s", axis_names[pid->axis]);
                DEBUG_PRINT_LOCAL("Kp: %.4f", pid->kp);
                DEBUG_PRINT_LOCAL("Ki: %.4f", pid->ki);
                DEBUG_PRINT_LOCAL("Kd: %.4f", pid->kd);
                
                // 应用PID参数
                configReceiverApplyPID(pid);
            }
            break;
        }
        
        case CONFIG_CMD_PID_QUERY: {
            DEBUG_PRINT_LOCAL("配置类型: PID参数查询");
            // 发送当前PID参数给APP
            configReceiverSendAllPID();
            break;
        }
        
        case CONFIG_CMD_DEVICE_NAME: {
            char name[63] = {0};
            memcpy(name, config->data, config->data_len > 62 ? 62 : config->data_len);
            DEBUG_PRINT_LOCAL("配置类型: 设备名称");
            DEBUG_PRINT_LOCAL("设备名称: %s", name);
            break;
        }
        
        case CONFIG_CMD_GENERAL_CONFIG: {
            DEBUG_PRINT_LOCAL("配置类型: 通用配置");
            DEBUG_PRINT_LOCAL("配置数据 (Hex):");
            for (int i = 0; i < config->data_len; i++) {
                if (i % 16 == 0) {
                    printf("\n  ");
                }
                printf("%02X ", config->data[i]);
            }
            printf("\n");
            break;
        }
        
        case CONFIG_CMD_TEST: {
            char test_msg[63] = {0};
            memcpy(test_msg, config->data, config->data_len > 62 ? 62 : config->data_len);
            DEBUG_PRINT_LOCAL("配置类型: 测试命令");
            DEBUG_PRINT_LOCAL("测试消息: %s", test_msg);
            break;
        }
        
        default:
            DEBUG_PRINT_LOCAL("配置类型: 未知 (0x%02X)", config->cmd_type);
            DEBUG_PRINT_LOCAL("原始数据 (Hex):");
            for (int i = 0; i < config->data_len && i < 62; i++) {
                if (i % 16 == 0) {
                    printf("\n  ");
                }
                printf("%02X ", config->data[i]);
            }
            printf("\n");
            break;
    }
    
    DEBUG_PRINT_LOCAL("========================================");
}

/**
 * 处理接收到的配置数据
 */
bool configReceiverProcess(uint8_t *data, uint32_t len)
{
    if (data == NULL || len < 2) {
        return false;
    }
    
    // 检查是否是配置命令包 (第一个字节为0xAA表示配置命令)
    if (data[0] != 0xAA) {
        return false;  // 不是配置命令，不处理
    }
    
    // 解析配置包 (注意：校验和已经在wifi_esp32.c中去掉了)
    ConfigPacket config;
    config.cmd_type = data[1];
    config.data_len = len - 2;  // 只减去头部的2个字节(0xAA和CMD_TYPE)
    
    if (config.data_len > 62) {
        config.data_len = 62;  // 限制数据长度
    }
    
    memcpy(config.data, data + 2, config.data_len);
    
    // 打印配置信息
    configReceiverPrint(&config);
    
    return true;
}

/**
 * 应用PID参数到飞控
 */
void configReceiverApplyPID(PIDConfig *pid)
{
    if (pid == NULL) {
        return;
    }
    
    PidObject *targetPid = NULL;
    const char *axis_names[] = {"Roll", "Pitch", "Yaw"};
    const char *loop_names[] = {"Attitude", "Rate"};
    
    // 根据轴和环类型选择目标PID对象
    if (pid->isRateLoop) {
        // 角速度环
        switch (pid->axis) {
            case 0: targetPid = &pidRollRate; break;
            case 1: targetPid = &pidPitchRate; break;
            case 2: targetPid = &pidYawRate; break;
            default: return;
        }
    } else {
        // 姿态环
        switch (pid->axis) {
            case 0: targetPid = &pidRoll; break;
            case 1: targetPid = &pidPitch; break;
            case 2: targetPid = &pidYaw; break;
            default: return;
        }
    }
    
    // 应用PID参数
    if (targetPid != NULL) {
        pidSetKp(targetPid, pid->kp);
        pidSetKi(targetPid, pid->ki);
        pidSetKd(targetPid, pid->kd);
        
        DEBUG_PRINT_LOCAL("已应用PID参数: %s %s Kp=%.4f Ki=%.4f Kd=%.4f",
            loop_names[pid->isRateLoop ? 1 : 0],
            axis_names[pid->axis],
            pid->kp, pid->ki, pid->kd);
            
        // 通过控制台发送确认消息
        consolePrintf("PID SET: %s %s P=%.2f I=%.2f D=%.2f\n",
            loop_names[pid->isRateLoop ? 1 : 0],
            axis_names[pid->axis],
            pid->kp, pid->ki, pid->kd);
    }
}

/**
 * 发送单个PID参数到APP
 */
static void sendPIDParams(const char *name, float kp, float ki, float kd)
{
    consolePrintf("PID %s: P=%.4f I=%.4f D=%.4f\n", name, kp, ki, kd);
}

/**
 * 发送所有PID参数给APP
 */
void configReceiverSendAllPID(void)
{
    DEBUG_PRINT_LOCAL("发送所有PID参数到APP...");
    
    consolePrintf("========== PID Parameters ==========\n");
    
    // 发送姿态环参数
    consolePrintf("[Attitude Loop]\n");
    sendPIDParams("Roll_Att", pidRoll.kp, pidRoll.ki, pidRoll.kd);
    sendPIDParams("Pitch_Att", pidPitch.kp, pidPitch.ki, pidPitch.kd);
    sendPIDParams("Yaw_Att", pidYaw.kp, pidYaw.ki, pidYaw.kd);
    
    // 发送角速度环参数
    consolePrintf("[Rate Loop]\n");
    sendPIDParams("Roll_Rate", pidRollRate.kp, pidRollRate.ki, pidRollRate.kd);
    sendPIDParams("Pitch_Rate", pidPitchRate.kp, pidPitchRate.ki, pidPitchRate.kd);
    sendPIDParams("Yaw_Rate", pidYawRate.kp, pidYawRate.ki, pidYawRate.kd);
    
    consolePrintf("=====================================\n");
    
    DEBUG_PRINT_LOCAL("PID参数发送完成");
}

