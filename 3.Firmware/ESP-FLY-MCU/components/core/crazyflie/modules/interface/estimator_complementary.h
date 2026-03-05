#ifndef __ESTIMATOR_COMPLEMENTARY_H__
#define __ESTIMATOR_COMPLEMENTARY_H__

#include "stabilizer_types.h"

void estimatorComplementaryInit(void);
bool estimatorComplementaryTest(void);
void estimatorComplementary(state_t *state, sensorData_t *sensors, control_t *control, const uint32_t tick);

bool estimatorComplementaryEnqueueTOF(const tofMeasurement_t *tof);

#endif //__ESTIMATOR_COMPLEMENTARY_H__
