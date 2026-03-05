#ifndef __CONTROLLER_H__
#define __CONTROLLER_H__

#include "stabilizer_types.h"

typedef enum
{
  ControllerTypeAny,
  ControllerTypePID,
  ControllerType_COUNT,
} ControllerType;

void controllerInit(ControllerType controller);
bool controllerTest(void);
void controller(control_t *control, setpoint_t *setpoint,
                const sensorData_t *sensors,
                const state_t *state,
                const uint32_t tick);
ControllerType getControllerType(void);
const char *controllerGetName();

#endif //__CONTROLLER_H__
