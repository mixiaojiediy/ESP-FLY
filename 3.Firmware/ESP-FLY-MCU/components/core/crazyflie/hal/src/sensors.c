#define DEBUG_MODULE "SENSORS"

#include "sensors.h"
#include "platform.h"
#include "debug_cf.h"

#define xstr(s) str(s)
#define str(s) #s

// Only MPU6050 sensor is supported
#ifdef SENSOR_INCLUDED_MPU6050
#include "sensors_mpu6050.h"
#endif

typedef struct
{
  SensorImplementation_t implements;
  void (*init)(void);
  bool (*test)(void);
  bool (*areCalibrated)(void);
  bool (*manufacturingTest)(void);
  void (*acquire)(sensorData_t *sensors, const uint32_t tick);
  void (*waitDataReady)(void);
  bool (*readGyro)(Axis3f *gyro);
  bool (*readAcc)(Axis3f *acc);
  bool (*readMag)(Axis3f *mag);
  bool (*readBaro)(baro_t *baro);
  void (*setAccMode)(accModes accMode);
  void (*dataAvailableCallback)(void);
} sensorsImplementation_t;

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
static void nullFunction(void) {}
#pragma GCC diagnostic pop

// Only MPU6050 sensor implementation is supported
static const sensorsImplementation_t sensorImplementations[SensorImplementation_COUNT] = {
#ifdef SENSOR_INCLUDED_MPU6050
    {
        .implements = SensorImplementation_mpu6050,
        .init = sensorsMpu6050Init,
        .test = sensorsMpu6050Test,
        .areCalibrated = sensorsMpu6050AreCalibrated,
        .manufacturingTest = sensorsMpu6050ManufacturingTest,
        .acquire = sensorsMpu6050Acquire,
        .waitDataReady = sensorsMpu6050WaitDataReady,
        .readGyro = sensorsMpu6050ReadGyro,
        .readAcc = sensorsMpu6050ReadAcc,
        .readMag = sensorsMpu6050ReadMag,
        .readBaro = sensorsMpu6050ReadBaro,
        .setAccMode = sensorsMpu6050SetAccMode,
        .dataAvailableCallback = nullFunction,
    }
#endif
};

static const sensorsImplementation_t *activeImplementation;
static bool isInit = false;
static const sensorsImplementation_t *findImplementation(SensorImplementation_t implementation);

void sensorsInit(void)
{
  if (isInit)
  {
    return;
  }

#ifndef SENSORS_FORCE
  SensorImplementation_t sensorImplementation = platformConfigGetSensorImplementation();
#else
  SensorImplementation_t sensorImplementation = SENSORS_FORCE;
  DEBUG_PRINTD("Forcing sensors to " xstr(SENSORS_FORCE) "\n");
#endif

  activeImplementation = findImplementation(sensorImplementation);

  activeImplementation->init();

  isInit = true;
}

bool sensorsTest(void)
{
  return activeImplementation->test();
}

bool sensorsAreCalibrated(void)
{
  return activeImplementation->areCalibrated();
}

bool sensorsManufacturingTest(void)
{
  return activeImplementation->manufacturingTest;
}

void sensorsAcquire(sensorData_t *sensors, const uint32_t tick)
{
  activeImplementation->acquire(sensors, tick);
}

void sensorsWaitDataReady(void)
{
  activeImplementation->waitDataReady();
}

bool sensorsReadGyro(Axis3f *gyro)
{
  return activeImplementation->readGyro(gyro);
}

bool sensorsReadAcc(Axis3f *acc)
{
  return activeImplementation->readAcc(acc);
}

bool sensorsReadMag(Axis3f *mag)
{
  return activeImplementation->readMag(mag);
}

bool sensorsReadBaro(baro_t *baro)
{
  return activeImplementation->readBaro(baro);
}

void sensorsSetAccMode(accModes accMode)
{
  activeImplementation->setAccMode(accMode);
}

void __attribute__((used)) EXTI14_Callback(void)
{
  activeImplementation->dataAvailableCallback();
}

static const sensorsImplementation_t *findImplementation(SensorImplementation_t implementation)
{
  const sensorsImplementation_t *result = 0;

  for (int i = 0; i < SensorImplementation_COUNT; i++)
  {
    if (sensorImplementations[i].implements == implementation)
    {
      result = &sensorImplementations[i];
      break;
    }
  }

  return result;
}
