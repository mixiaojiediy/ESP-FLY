
#ifndef __SENSORS_MPU6050_H__
#define __SENSORS_MPU6050_H__

#include "sensors.h"

void sensorsMpu6050Init(void);
bool sensorsMpu6050Test(void);
bool sensorsMpu6050AreCalibrated(void);
bool sensorsMpu6050ManufacturingTest(void);
void sensorsMpu6050Acquire(sensorData_t *sensors, const uint32_t tick);
void sensorsMpu6050WaitDataReady(void);
bool sensorsMpu6050ReadGyro(Axis3f *gyro);
bool sensorsMpu6050ReadAcc(Axis3f *acc);
bool sensorsMpu6050ReadMag(Axis3f *mag);
bool sensorsMpu6050ReadBaro(baro_t *baro);
void sensorsMpu6050SetAccMode(accModes accMode);

// 直接获取当前传感器数据（不通过队列）
void sensorsGetData(Axis3f *gyro, Axis3f *acc);

#endif // __SENSORS_MPU6050_H__
