#ifndef __CONTROLLER_PID_H__
#define __CONTROLLER_PID_H__

#include "stabilizer_types.h"

void controllerPidInit(void);
bool controllerPidTest(void);
void controllerPid(control_t *control, setpoint_t *setpoint,
                   const sensorData_t *sensors,
                   const state_t *state,
                   const uint32_t tick);

/**
 * Get the desired rate (output of attitude PID)
 * @param roll  Pointer to store roll rate desired (deg/s)
 * @param pitch Pointer to store pitch rate desired (deg/s)
 * @param yaw   Pointer to store yaw rate desired (deg/s)
 */
void controllerPidGetRateDesired(float *roll, float *pitch, float *yaw);

#endif //__CONTROLLER_PID_H__
