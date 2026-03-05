#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "data_sender.h"
#include "packet_codec.h"
#include "wifi_esp32.h"
#include "stabilizer_types.h"
#include "controller_pid.h"
#include "motors.h"
#include "pm_esplane.h"
#include "stm32_legacy.h"
#include "pid.h"

#define DEBUG_MODULE "DATA_SEND"
#include "debug_cf.h"

// 引用 stabilizer.c 中的全局变量
extern sensorData_t sensorData;
extern state_t state;
extern control_t control;

static bool isInit = false;

/**
 * 发送PID参数响应包 (1Hz)
 * 一次性发送所有6组PID参数（姿态环和速度环）
 */
static void sendPIDInfo(void)
{
    static uint8_t sendBuffer[128];

    // 引用attitude_pid_controller.c中的全局PID对象
    extern PidObject pidRollRate;
    extern PidObject pidPitchRate;
    extern PidObject pidYawRate;
    extern PidObject pidRoll;
    extern PidObject pidPitch;
    extern PidObject pidYaw;

    PIDConfigPacket_t pid_data = {0};

    // 填充姿态环 PID参数
    pid_data.roll_angle_kp = pidRoll.kp;
    pid_data.roll_angle_ki = pidRoll.ki;
    pid_data.roll_angle_kd = pidRoll.kd;

    pid_data.pitch_angle_kp = pidPitch.kp;
    pid_data.pitch_angle_ki = pidPitch.ki;
    pid_data.pitch_angle_kd = pidPitch.kd;

    pid_data.yaw_angle_kp = pidYaw.kp;
    pid_data.yaw_angle_ki = pidYaw.ki;
    pid_data.yaw_angle_kd = pidYaw.kd;

    // 填充速度环 PID参数
    pid_data.roll_rate_kp = pidRollRate.kp;
    pid_data.roll_rate_ki = pidRollRate.ki;
    pid_data.roll_rate_kd = pidRollRate.kd;

    pid_data.pitch_rate_kp = pidPitchRate.kp;
    pid_data.pitch_rate_ki = pidPitchRate.ki;
    pid_data.pitch_rate_kd = pidPitchRate.kd;

    pid_data.yaw_rate_kp = pidYawRate.kp;
    pid_data.yaw_rate_ki = pidYawRate.ki;
    pid_data.yaw_rate_kd = pidYawRate.kd;

    // 创建并发送PID响应包
    uint16_t packet_len = packet_createPIDResponse(sendBuffer, sizeof(sendBuffer), &pid_data);

    if (packet_len > 0)
    {
        wifiSendData(packet_len, sendBuffer);
    }
}

/**
 * 高频数据传输任务 (50Hz)
 * 负责发送姿态、控制、电机和传感器数据
 */
void dataSenderHighFreqTask(void *param)
{
    TickType_t lastWakeTime = xTaskGetTickCount();
    const TickType_t interval = M2T(20); // 50Hz 发送频率 (20ms周期)

    uint8_t sendBuffer[PACKET_MAX_SIZE];
    HighFreqDataPacket_t hf_data;

    DEBUG_PRINT("High Frequency Data Transfer Task started\n");

    while (1)
    {
        vTaskDelayUntil(&lastWakeTime, interval);

        if (!isInit)
            continue;

        // 1. 采集姿态数据 (由姿态估计器计算)
        hf_data.roll = state.attitude.roll;
        hf_data.pitch = state.attitude.pitch;
        hf_data.yaw = state.attitude.yaw;

        // 2. 采集期望角速度 (第一级PID输出：角度环的输出)
        controllerPidGetRateDesired(&hf_data.rollRateDesired,
                                    &hf_data.pitchRateDesired,
                                    &hf_data.yawRateDesired);

        // 3. 采集控制输出 (第二级PID输出：角速度环的输出)
        hf_data.rollControl = control.roll;
        hf_data.pitchControl = control.pitch;
        hf_data.yawControl = control.yaw;

        // 4. 采集电机PWM输出 (0-65535)
        hf_data.motor1 = (uint16_t)motorsGetRatio(0);
        hf_data.motor2 = (uint16_t)motorsGetRatio(1);
        hf_data.motor3 = (uint16_t)motorsGetRatio(2);
        hf_data.motor4 = (uint16_t)motorsGetRatio(3);

        // 5. 采集传感器原始数据 (1KHz采集到的陀螺仪和加速度计数据)
        hf_data.gyroX = sensorData.gyro.x;
        hf_data.gyroY = sensorData.gyro.y;
        hf_data.gyroZ = sensorData.gyro.z;
        hf_data.accX = sensorData.acc.x;
        hf_data.accY = sensorData.acc.y;
        hf_data.accZ = sensorData.acc.z;

        // 6. 时间戳 (毫秒低16位)
        hf_data.timestamp = (uint16_t)(xTaskGetTickCount() & 0xFFFF);

        // 7. 使用协议打包并发送
        uint16_t packet_len = packet_createHighFreqData(sendBuffer, sizeof(sendBuffer), &hf_data);
        if (packet_len > 0)
        {
            wifiSendData(packet_len, sendBuffer);
        }
    }
}

/**
 * 低频数据传输任务 (1Hz)
 * 负责发送 PID 参数和电池状态
 */
void dataSenderLowFreqTask(void *param)
{
    TickType_t lastWakeTime = xTaskGetTickCount();
    const TickType_t interval = M2T(1000); // 1Hz 发送频率 (1000ms周期)

    uint8_t sendBuffer[PACKET_MAX_SIZE];

    DEBUG_PRINT("Low Frequency Data Transfer Task started\n");

    while (1)
    {
        vTaskDelayUntil(&lastWakeTime, interval);

        if (!isInit)
            continue;

        // 发送 PID 参数
        sendPIDInfo();

        // 发送电池状态
        BatteryStatusPacket_t battery_data = {
            .voltage = pmGetBatteryVoltage(),
            .voltage_mv = (uint16_t)(pmGetBatteryVoltage() * 1000),
            .level = pmGetBatteryLevel(),
            .state = (uint8_t)pmGetState()};
        uint16_t batt_len = packet_createBatteryStatus(sendBuffer, sizeof(sendBuffer), &battery_data);
        if (batt_len > 0)
        {
            wifiSendData(batt_len, sendBuffer);
        }
    }
}

void dataSenderInit(void)
{
    if (isInit)
        return;

    // 创建高频数据传输任务 (50Hz)
    xTaskCreate(dataSenderHighFreqTask, "DATA_SEND_HF", 4096, NULL, 3, NULL);

    // 创建低频数据传输任务 (1Hz)
    xTaskCreate(dataSenderLowFreqTask, "DATA_SEND_LF", 4096, NULL, 3, NULL);

    isInit = true;
    DEBUG_PRINT("Data Sender module initialized\n");
}
