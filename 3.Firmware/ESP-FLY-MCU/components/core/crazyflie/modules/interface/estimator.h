#ifndef __ESTIMATOR_H__
#define __ESTIMATOR_H__

#include "stabilizer_types.h"

typedef enum
{
  anyEstimator = 0,
  complementaryEstimator,
  StateEstimatorTypeCount,
} StateEstimatorType;

bool registerRequiredEstimator(StateEstimatorType estimator);
StateEstimatorType deckGetRequiredEstimator();
void stateEstimatorInit(StateEstimatorType estimator);
bool stateEstimatorTest(void);
void stateEstimatorSwitchTo(StateEstimatorType estimator);
void stateEstimator(state_t *state, sensorData_t *sensors, control_t *control, const uint32_t tick);
StateEstimatorType getStateEstimator(void);
const char *stateEstimatorGetName();

// Support to incorporate additional sensors into the state estimate via the following functions:
bool estimatorEnqueueTDOA(const tdoaMeasurement_t *uwb);
bool estimatorEnqueuePosition(const positionMeasurement_t *pos);
bool estimatorEnqueuePose(const poseMeasurement_t *pose);
bool estimatorEnqueueDistance(const distanceMeasurement_t *dist);
bool estimatorEnqueueTOF(const tofMeasurement_t *tof);
bool estimatorEnqueueAbsoluteHeight(const heightMeasurement_t *height);
bool estimatorEnqueueFlow(const flowMeasurement_t *flow);
bool estimatorEnqueueYawError(const yawErrorMeasurement_t *error);
// bool estimatorEnqueueSweepAngles(const sweepAngleMeasurement_t *angles);

#endif //__ESTIMATOR_H__
