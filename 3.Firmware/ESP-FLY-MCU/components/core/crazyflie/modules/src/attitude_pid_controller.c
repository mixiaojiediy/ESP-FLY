#include <stdbool.h>

#include "FreeRTOS.h"

#include "attitude_controller.h"
#include "pid.h"
#include <stdio.h> // printf

#define DEBUG_MODULE "ATT_PID"
#include "debug_cf.h"

#define ATTITUDE_LPF_CUTOFF_FREQ 15.0f
#define ATTITUDE_LPF_ENABLE false
#define ATTITUDE_RATE_LPF_CUTOFF_FREQ 30.0f
#define ATTITUDE_RATE_LPF_ENABLE false

static inline int16_t saturateSignedInt16(float in)
{
  // don't use INT16_MIN, because later we may negate it, which won't work for that value.
  if (in > INT16_MAX)
    return INT16_MAX;
  else if (in < -INT16_MAX)
    return -INT16_MAX;
  else
    return (int16_t)in;
}

PidObject pidRollRate;
PidObject pidPitchRate;
PidObject pidYawRate;
PidObject pidRoll;
PidObject pidPitch;
PidObject pidYaw;

static int16_t rollOutput;
static int16_t pitchOutput;
static int16_t yawOutput;

static bool isInit;

void attitudeControllerInit(const float updateDt)
{
  if (isInit)
    return;

  // TODO: get parameters from configuration manager instead
  pidInit(&pidRollRate, 0, PID_ROLL_RATE_KP, PID_ROLL_RATE_KI, PID_ROLL_RATE_KD,
          updateDt, ATTITUDE_RATE, ATTITUDE_RATE_LPF_CUTOFF_FREQ, ATTITUDE_RATE_LPF_ENABLE);
  pidInit(&pidPitchRate, 0, PID_PITCH_RATE_KP, PID_PITCH_RATE_KI, PID_PITCH_RATE_KD,
          updateDt, ATTITUDE_RATE, ATTITUDE_RATE_LPF_CUTOFF_FREQ, ATTITUDE_RATE_LPF_ENABLE);
  pidInit(&pidYawRate, 0, PID_YAW_RATE_KP, PID_YAW_RATE_KI, PID_YAW_RATE_KD,
          updateDt, ATTITUDE_RATE, ATTITUDE_RATE_LPF_CUTOFF_FREQ, ATTITUDE_RATE_LPF_ENABLE);

  pidSetIntegralLimit(&pidRollRate, PID_ROLL_RATE_INTEGRATION_LIMIT);
  pidSetIntegralLimit(&pidPitchRate, PID_PITCH_RATE_INTEGRATION_LIMIT);
  pidSetIntegralLimit(&pidYawRate, PID_YAW_RATE_INTEGRATION_LIMIT);

  pidInit(&pidRoll, 0, PID_ROLL_KP, PID_ROLL_KI, PID_ROLL_KD, updateDt,
          ATTITUDE_RATE, ATTITUDE_LPF_CUTOFF_FREQ, ATTITUDE_LPF_ENABLE);
  pidInit(&pidPitch, 0, PID_PITCH_KP, PID_PITCH_KI, PID_PITCH_KD, updateDt,
          ATTITUDE_RATE, ATTITUDE_LPF_CUTOFF_FREQ, ATTITUDE_LPF_ENABLE);
  pidInit(&pidYaw, 0, PID_YAW_KP, PID_YAW_KI, PID_YAW_KD, updateDt,
          ATTITUDE_RATE, ATTITUDE_LPF_CUTOFF_FREQ, ATTITUDE_LPF_ENABLE);

  pidSetIntegralLimit(&pidRoll, PID_ROLL_INTEGRATION_LIMIT);
  pidSetIntegralLimit(&pidPitch, PID_PITCH_INTEGRATION_LIMIT);
  pidSetIntegralLimit(&pidYaw, PID_YAW_INTEGRATION_LIMIT);

  isInit = true;
}

bool attitudeControllerTest()
{
  return isInit;
}

void attitudeControllerCorrectRatePID(
    float rollRateActual, float pitchRateActual, float yawRateActual,
    float rollRateDesired, float pitchRateDesired, float yawRateDesired)
{
  pidSetDesired(&pidRollRate, rollRateDesired);
  rollOutput = saturateSignedInt16(pidUpdate(&pidRollRate, rollRateActual, true));

  pidSetDesired(&pidPitchRate, pitchRateDesired);
  pitchOutput = saturateSignedInt16(pidUpdate(&pidPitchRate, pitchRateActual, true));

  pidSetDesired(&pidYawRate, yawRateDesired);
  yawOutput = saturateSignedInt16(pidUpdate(&pidYawRate, yawRateActual, true));
}

void attitudeControllerCorrectAttitudePID(
    float eulerRollActual, float eulerPitchActual, float eulerYawActual,
    float eulerRollDesired, float eulerPitchDesired, float eulerYawDesired,
    float *rollRateDesired, float *pitchRateDesired, float *yawRateDesired)
{
  pidSetDesired(&pidRoll, eulerRollDesired);
  *rollRateDesired = pidUpdate(&pidRoll, eulerRollActual, true);

  // Update PID for pitch axis
  pidSetDesired(&pidPitch, eulerPitchDesired);
  *pitchRateDesired = pidUpdate(&pidPitch, eulerPitchActual, true);

  // Update PID for yaw axis
  float yawError;
  yawError = eulerYawDesired - eulerYawActual;
  if (yawError > 180.0f)
    yawError -= 360.0f;
  else if (yawError < -180.0f)
    yawError += 360.0f;
  pidSetError(&pidYaw, yawError);
  *yawRateDesired = pidUpdate(&pidYaw, eulerYawActual, false);
}

void attitudeControllerResetRollAttitudePID(void)
{
  pidReset(&pidRoll);
}

void attitudeControllerResetPitchAttitudePID(void)
{
  pidReset(&pidPitch);
}

void attitudeControllerResetAllPID(void)
{
  pidReset(&pidRoll);
  pidReset(&pidPitch);
  pidReset(&pidYaw);
  pidReset(&pidRollRate);
  pidReset(&pidPitchRate);
  pidReset(&pidYawRate);
}

void attitudeControllerGetActuatorOutput(int16_t *roll, int16_t *pitch, int16_t *yaw)
{
  *roll = rollOutput;
  *pitch = pitchOutput;
  *yaw = yawOutput;
}

/**
 * 打印当前PID参数到串口（每秒调用一次）
 */
void attitudeControllerPrintPidParams(void)
{
  DEBUG_PRINTI("=== PID Parameters ===\n");
  DEBUG_PRINTI("Rate Roll:  Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidRollRate.kp, (double)pidRollRate.ki, (double)pidRollRate.kd);
  DEBUG_PRINTI("Rate Pitch: Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidPitchRate.kp, (double)pidPitchRate.ki, (double)pidPitchRate.kd);
  DEBUG_PRINTI("Rate Yaw:   Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidYawRate.kp, (double)pidYawRate.ki, (double)pidYawRate.kd);
  DEBUG_PRINTI("Att Roll:   Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidRoll.kp, (double)pidRoll.ki, (double)pidRoll.kd);
  DEBUG_PRINTI("Att Pitch:  Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidPitch.kp, (double)pidPitch.ki, (double)pidPitch.kd);
  DEBUG_PRINTI("Att Yaw:    Kp=%.1f, Ki=%.1f, Kd=%.2f\n",
               (double)pidYaw.kp, (double)pidYaw.ki, (double)pidYaw.kd);
}

/**
 * 发送当前PID参数到APP控制台
 */
void attitudeControllerSendPidToConsole(void)
{
  printf("[PID] RateR:%.1f/%.1f/%.2f\n",
         (double)pidRollRate.kp, (double)pidRollRate.ki, (double)pidRollRate.kd);
  printf("[PID] RateP:%.1f/%.1f/%.2f\n",
         (double)pidPitchRate.kp, (double)pidPitchRate.ki, (double)pidPitchRate.kd);
  printf("[PID] RateY:%.1f/%.1f/%.2f\n",
         (double)pidYawRate.kp, (double)pidYawRate.ki, (double)pidYawRate.kd);
  printf("[PID] AttR:%.1f/%.1f/%.2f\n",
         (double)pidRoll.kp, (double)pidRoll.ki, (double)pidRoll.kd);
  printf("[PID] AttP:%.1f/%.1f/%.2f\n",
         (double)pidPitch.kp, (double)pidPitch.ki, (double)pidPitch.kd);
  printf("[PID] AttY:%.1f/%.1f/%.2f\n",
         (double)pidYaw.kp, (double)pidYaw.ki, (double)pidYaw.kd);
}