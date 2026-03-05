/**
 * ESP-Drone 配置接收模块实现
 */

#include <string.h>
#include <stdio.h>
#include "config_receiver.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "pid.h"
#include <stdio.h> // printf

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
    if (isInit)
    {
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
    if (config == NULL)
    {
        return;
    }

    DEBUG_PRINT_LOCAL("========================================");
    DEBUG_PRINT_LOCAL("收到APP配置信息:");
    DEBUG_PRINT_LOCAL("命令类型: 0x%02X", config->cmd_type);
    DEBUG_PRINT_LOCAL("数据长度: %d", config->data_len);

    switch (config->cmd_type)
    {
    case CONFIG_CMD_PID_PARAMS:
    {
        if (config->data_len >= sizeof(PIDConfig))
        {
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

    case CONFIG_CMD_TEST:
    {
        char test_msg[63] = {0};
        memcpy(test_msg, config->data, config->data_len > 62 ? 62 : config->data_len);
        DEBUG_PRINT_LOCAL("配置类型: 测试命令");
        DEBUG_PRINT_LOCAL("测试消息: %s", test_msg);
        break;
    }

    default:
        DEBUG_PRINT_LOCAL("配置类型: 未知 (0x%02X)", config->cmd_type);
        DEBUG_PRINT_LOCAL("原始数据 (Hex):");
        for (int i = 0; i < config->data_len && i < 62; i++)
        {
            if (i % 16 == 0)
            {
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
    if (data == NULL || len < 2)
    {
        return false;
    }

    // 检查是否是配置命令包 (第一个字节为0xAA表示配置命令)
    if (data[0] != 0xAA)
    {
        return false; // 不是配置命令，不处理
    }

    // 解析配置包
    ConfigPacket config;
    config.cmd_type = data[1];
    config.data_len = len - 2; // 只减去头部的2个字节(0xAA和CMD_TYPE)

    if (config.data_len > 62)
    {
        config.data_len = 62; // 限制数据长度
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
    if (pid == NULL)
    {
        return;
    }

    PidObject *targetPid = NULL;
    const char *axis_names[] = {"Roll", "Pitch", "Yaw"};
    const char *loop_names[] = {"Attitude", "Rate"};

    // 根据轴和环类型选择目标PID对象
    if (pid->isRateLoop)
    {
        // 角速度环
        switch (pid->axis)
        {
        case 0:
            targetPid = &pidRollRate;
            break;
        case 1:
            targetPid = &pidPitchRate;
            break;
        case 2:
            targetPid = &pidYawRate;
            break;
        default:
            return;
        }
    }
    else
    {
        // 姿态环
        switch (pid->axis)
        {
        case 0:
            targetPid = &pidRoll;
            break;
        case 1:
            targetPid = &pidPitch;
            break;
        case 2:
            targetPid = &pidYaw;
            break;
        default:
            return;
        }
    }

    // 应用PID参数
    if (targetPid != NULL)
    {
        pidSetKp(targetPid, pid->kp);
        pidSetKi(targetPid, pid->ki);
        pidSetKd(targetPid, pid->kd);

        DEBUG_PRINT_LOCAL("已应用PID参数: %s %s Kp=%.4f Ki=%.4f Kd=%.4f",
                          loop_names[pid->isRateLoop ? 1 : 0],
                          axis_names[pid->axis],
                          pid->kp, pid->ki, pid->kd);
    }
}