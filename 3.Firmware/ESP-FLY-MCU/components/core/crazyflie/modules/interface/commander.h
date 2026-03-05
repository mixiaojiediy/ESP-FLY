#ifndef COMMANDER_H_
#define COMMANDER_H_
#include <stdint.h>
#include <stdbool.h>
#include "config.h"
#include "stabilizer_types.h"

#define DEFAULT_YAW_MODE XMODE

#define COMMANDER_WDT_TIMEOUT_STABILIZE M2T(500)
#define COMMANDER_WDT_TIMEOUT_SHUTDOWN M2T(2000)

#define COMMANDER_PRIORITY_DISABLE 0
#define COMMANDER_PRIORITY_CRTP 1
#define COMMANDER_PRIORITY_EXTRX 2

void commanderInit(void);
bool commanderTest(void);
uint32_t commanderGetInactivityTime(void);

void commanderSetSetpoint(setpoint_t *setpoint, int priority);
int commanderGetActivePriority(void);

/* Inform the commander that streaming setpoints are about to stop.
 * Parameter controls the amount of time the last setpoint will remain valid.
 * This gives the PC time to send the next command, e.g. with the high-level
 * commander, before we enter timeout mode.
 */
void commanderNotifySetpointsStop(int remainValidMillisecs);

void commanderGetSetpoint(setpoint_t *setpoint, const state_t *state);

#endif /* COMMANDER_H_ */
