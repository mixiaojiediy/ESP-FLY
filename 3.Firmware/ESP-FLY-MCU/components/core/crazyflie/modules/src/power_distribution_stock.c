
#include <string.h>

#include "power_distribution.h"

#include <string.h>
#include "num.h"
#include "platform.h"
#include "motors.h"
#define DEBUG_MODULE "PWR_DIST"
#include "debug_cf.h"

static bool motorSetEnable = false;
static bool motorTestMode = false; // 电机测试模式标志

static struct
{
  uint32_t m1;
  uint32_t m2;
  uint32_t m3;
  uint32_t m4;
} motorPower;

static struct
{
  uint16_t m1;
  uint16_t m2;
  uint16_t m3;
  uint16_t m4;
} motorPowerSet;

#ifndef DEFAULT_IDLE_THRUST
#define DEFAULT_IDLE_THRUST 0
#endif

static uint32_t idleThrust = DEFAULT_IDLE_THRUST;

void powerDistributionInit(void)
{
  motorsInit(platformConfigGetMotorMapping());
}

bool powerDistributionTest(void)
{
  bool pass = true;

  pass &= motorsTest();

  return pass;
}

#define limitThrust(VAL) limitUint16(VAL)

void powerStop()
{
  motorsSetRatio(MOTOR_M1, 0);
  motorsSetRatio(MOTOR_M2, 0);
  motorsSetRatio(MOTOR_M3, 0);
  motorsSetRatio(MOTOR_M4, 0);
}

void powerDistributionSetMotorTestMode(bool enable)
{
  motorTestMode = enable;
}

void powerDistribution(const control_t *control)
{
  // 如果处于电机测试模式，跳过姿态控制的电机设置，避免覆盖测试值
  if (motorTestMode)
  {
    return;
  }

#ifdef QUAD_FORMATION_X
  int16_t r = control->roll;
  int16_t p = control->pitch;
  motorPower.m1 = limitThrust(control->thrust + r - p + control->yaw);
  motorPower.m2 = limitThrust(control->thrust - r - p - control->yaw);
  motorPower.m3 = limitThrust(control->thrust - r + p + control->yaw);
  motorPower.m4 = limitThrust(control->thrust + r + p - control->yaw);
#else // QUAD_FORMATION_NORMAL
  motorPower.m1 = limitThrust(control->thrust + control->pitch +
                              control->yaw);
  motorPower.m2 = limitThrust(control->thrust - control->roll -
                              control->yaw);
  motorPower.m3 = limitThrust(control->thrust - control->pitch +
                              control->yaw);
  motorPower.m4 = limitThrust(control->thrust + control->roll -
                              control->yaw);
#endif

  if (motorSetEnable)
  {
    motorsSetRatio(MOTOR_M1, motorPowerSet.m1);
    motorsSetRatio(MOTOR_M2, motorPowerSet.m2);
    motorsSetRatio(MOTOR_M3, motorPowerSet.m3);
    motorsSetRatio(MOTOR_M4, motorPowerSet.m4);
  }
  else
  {
    if (motorPower.m1 < idleThrust)
    {
      motorPower.m1 = idleThrust;
    }
    if (motorPower.m2 < idleThrust)
    {
      motorPower.m2 = idleThrust;
    }
    if (motorPower.m3 < idleThrust)
    {
      motorPower.m3 = idleThrust;
    }
    if (motorPower.m4 < idleThrust)
    {
      motorPower.m4 = idleThrust;
    }

    motorsSetRatio(MOTOR_M1, motorPower.m1);
    motorsSetRatio(MOTOR_M2, motorPower.m2);
    motorsSetRatio(MOTOR_M3, motorPower.m3);
    motorsSetRatio(MOTOR_M4, motorPower.m4);
  }
}