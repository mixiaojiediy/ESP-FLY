#ifndef __SENSORS_H__
#define __SENSORS_H__

#include "stabilizer_types.h"

typedef enum
{
    ACC_MODE_PROPTEST,
    ACC_MODE_FLIGHT
} accModes;

void sensorsInit(void);
bool sensorsTest(void);
bool sensorsAreCalibrated(void);

/**
 * More extensive test of the sensors
 */
bool sensorsManufacturingTest(void);

// For legacy control
void sensorsAcquire(sensorData_t *sensors, const uint32_t tick);

/**
 * This function should block and unlock at 1KhZ
 */
void sensorsWaitDataReady(void);

// Allows individual sensor measurement
bool sensorsReadGyro(Axis3f *gyro);
bool sensorsReadAcc(Axis3f *acc);
bool sensorsReadMag(Axis3f *mag);
bool sensorsReadBaro(baro_t *baro);

/**
 * Set acc mode, one of accModes enum
 */
void sensorsSetAccMode(accModes accMode);

#endif //__SENSORS_H__
