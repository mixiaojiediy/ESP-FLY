/**
 * Command Receiver - 飞行控制命令处理
 */

#include <stdbool.h>
#include <string.h>
#include <math.h>

#include "command_receiver.h"
#include "commander.h"

#define DEBUG_MODULE "CMD_RX"
#include "debug_cf.h"

#define MIN_THRUST 1000
#define MAX_THRUST 60000

static bool isInit = false;
// thrustLocked机制已移除，实现简单直接的控制流程

/**
 * Stabilization modes for Roll, Pitch, Yaw.
 */
typedef enum
{
    RATE = 0,
    ANGLE = 1,
} RPYType;

static RPYType stabilizationModeRoll = ANGLE;  // Current stabilization type of roll (rate or angle)
static RPYType stabilizationModePitch = ANGLE; // Current stabilization type of pitch (rate or angle)
static RPYType stabilizationModeYaw = ANGLE;   // Current stabilization type of yaw (rate or angle)

/**
 * 将飞行控制数据转换为setpoint
 * 简化版本：直接处理油门值，只检查最小值和最大值
 */
static void decodeFlightControl(setpoint_t *setpoint, const FlightControlPacket_t *fc_packet)
{
    // 直接处理油门值，只进行最小值和最大值限制
    uint16_t rawThrust = fc_packet->thrust;

    if (rawThrust < MIN_THRUST)
    {
        setpoint->thrust = 0;
    }
    else
    {
        setpoint->thrust = fminf(rawThrust, MAX_THRUST);
    }

    setpoint->mode.z = modeDisable;
    setpoint->mode.x = modeDisable;
    setpoint->mode.y = modeDisable;

    // Roll
    if (stabilizationModeRoll == RATE)
    {
        setpoint->mode.roll = modeVelocity;
        setpoint->attitudeRate.roll = fc_packet->roll;
        setpoint->attitude.roll = 0;
    }
    else
    {
        setpoint->mode.roll = modeAbs;
        setpoint->attitudeRate.roll = 0;
        setpoint->attitude.roll = fc_packet->roll;
    }

    // Pitch
    if (stabilizationModePitch == RATE)
    {
        setpoint->mode.pitch = modeVelocity;
        setpoint->attitudeRate.pitch = fc_packet->pitch;
        setpoint->attitude.pitch = 0;
    }
    else
    {
        setpoint->mode.pitch = modeAbs;
        setpoint->attitudeRate.pitch = 0;
        setpoint->attitude.pitch = fc_packet->pitch;
    }

    // Yaw
    if (stabilizationModeYaw == RATE)
    {
        // legacy rate input is inverted
        setpoint->attitudeRate.yaw = -fc_packet->yaw;
        setpoint->mode.yaw = modeVelocity;
    }
    else
    {
        setpoint->mode.yaw = modeAbs;
        setpoint->attitudeRate.yaw = 0;
        setpoint->attitude.yaw = fc_packet->yaw;
    }

    setpoint->velocity.x = 0;
    setpoint->velocity.y = 0;
}

void commandReceiverInit(void)
{
    if (isInit)
    {
        return;
    }

    isInit = true;
    DEBUG_PRINT("Command Receiver initialized\n");
}

bool commandReceiverTest(void)
{
    return isInit;
}

void commandReceiverHandleFlightControl(const FlightControlPacket_t *fc_packet)
{
    setpoint_t setpoint;

    if (fc_packet == NULL)
    {
        return;
    }

    memset(&setpoint, 0, sizeof(setpoint_t));
    decodeFlightControl(&setpoint, fc_packet);
    // 简化版本：直接设置setpoint，不使用priority参数
    commanderSetSetpoint(&setpoint, 1);
}
