#ifndef ATTITUDE_CONTROLLER_H_
#define ATTITUDE_CONTROLLER_H_

#include <stdbool.h>
#include "commander.h"

void attitudeControllerInit(const float updateDt);
bool attitudeControllerTest(void);

/**
 * Make the controller run an update of the attitude PID. The output is
 * the desired rate which should be fed into a rate controller. The
 * attitude controller can be run in a slower update rate then the rate
 * controller.
 */
void attitudeControllerCorrectAttitudePID(
    float eulerRollActual, float eulerPitchActual, float eulerYawActual,
    float eulerRollDesired, float eulerPitchDesired, float eulerYawDesired,
    float *rollRateDesired, float *pitchRateDesired, float *yawRateDesired);

/**
 * Make the controller run an update of the rate PID. The output is
 * the actuator force.
 */
void attitudeControllerCorrectRatePID(
    float rollRateActual, float pitchRateActual, float yawRateActual,
    float rollRateDesired, float pitchRateDesired, float yawRateDesired);

/**
 * Reset controller roll attitude PID
 */
void attitudeControllerResetRollAttitudePID(void);

/**
 * Reset controller pitch attitude PID
 */
void attitudeControllerResetPitchAttitudePID(void);

/**
 * Reset controller roll, pitch and yaw PID's.
 */
void attitudeControllerResetAllPID(void);

/**
 * Get the actuator output.
 */
void attitudeControllerGetActuatorOutput(int16_t *roll, int16_t *pitch, int16_t *yaw);

/**
 * Print current PID parameters to serial console.
 * Call this function once per second for periodic PID parameter display.
 */
void attitudeControllerPrintPidParams(void);

/**
 * Send current PID parameters to APP console via CRTP protocol.
 * Call this function once per second for periodic PID parameter display on APP.
 */
void attitudeControllerSendPidToConsole(void);

#endif /* ATTITUDE_CONTROLLER_H_ */
