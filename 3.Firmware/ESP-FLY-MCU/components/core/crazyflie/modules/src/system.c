
#include <stdbool.h>
#include <inttypes.h>
/* FreeRtos includes */
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"

#include "version.h"
#include "config.h"
#include "adc_esp32.h"
#include "pm_esplane.h"
#include "config.h"
#include "system.h"
#include "platform.h"
#include "worker.h"
#include "wifi_esp32.h"
#include "data_sender.h"
#include "protocol_dispatcher.h"
#include "comm.h"
#include "stabilizer.h"
#include "commander.h"
#include "stm32_legacy.h"
#include "status_led.h"
#define DEBUG_MODULE "SYS"
#include "debug_cf.h"
#include "static_mem.h"
#include "cfassert.h"

#ifndef START_DISARMED
#define ARM_INIT true
#else
#define ARM_INIT false
#endif

/* Private variable */
static bool selftestPassed;
static bool canFly;
static bool armed = ARM_INIT;
static bool forceArm;
static bool isInit;

STATIC_MEM_TASK_ALLOC(systemTask, SYSTEM_TASK_STACKSIZE);

/* System wide synchronisation */
xSemaphoreHandle canStartMutex;
static StaticSemaphore_t canStartMutexBuffer;

/* Private functions */
static void systemTask(void *arg);

/* Public functions */
void systemLaunch(void)
{
  STATIC_MEM_TASK_CREATE(systemTask, systemTask, SYSTEM_TASK_NAME, NULL, SYSTEM_TASK_PRI);
}

// This must be the first module to be initialized!
void systemInit(void)
{
  if (isInit)
    return;

  DEBUG_PRINT_LOCAL("----------------------------\n");
  DEBUG_PRINT_LOCAL("%s is up and running!\n", platformConfigGetDeviceTypeName());

  canStartMutex = xSemaphoreCreateMutexStatic(&canStartMutexBuffer);
  xSemaphoreTake(canStartMutex, portMAX_DELAY);

  workerInit();
  adcInit();
  pmInit();

  isInit = true;
}

void systemTask(void *arg)
{
  bool pass = true;

  // ledInit(); // LED disabled
  // ledSet(CHG_LED, 1); // LED disabled
  wifiInit();
  dataSenderInit();
  vTaskDelay(M2T(500));
  // Init the high-levels modules
  systemInit();
  commInit();
  commanderInit();
  protocolDispatcherInit();

  StateEstimatorType estimator = anyEstimator;
  stabilizerInit(estimator);

  /* Test each modules */
  pass &= wifiTest();
  DEBUG_PRINTI("wifiTest = %d ", pass);
  pass &= commTest();
  DEBUG_PRINTI("commTest = %d ", pass);
  pass &= commanderTest();
  DEBUG_PRINTI("commanderTest = %d ", pass);
  pass &= stabilizerTest();
  DEBUG_PRINTI("stabilizerTest = %d ", pass);
  DEBUG_PRINTI("memTest = %d ", pass);
  pass &= cfAssertNormalStartTest();

  // Start the firmware
  if (pass)
  {
    selftestPassed = 1;
    systemStart();
    DEBUG_PRINTI("systemStart ! selftestPassed = %d", selftestPassed);
    // System started, entering angle calibration phase
    statusLedSet(STATUS_LED_CALIBRATING); // Blue LED blinking - angle calibration in progress
  }
  else
  {
    selftestPassed = 0;
    statusLedSet(STATUS_LED_ERROR); // Red LED solid - tests failed
  }
  DEBUG_PRINT("Free heap: %" PRIu32 " bytes\n", xPortGetFreeHeapSize());

  workerLoop();

  // Should never reach this point!
  while (1)
    vTaskDelay(portMAX_DELAY);
}

/* Global system variables */
void systemStart()
{
  xSemaphoreGive(canStartMutex);
#ifndef DEBUG_EP2
  // watchdogInit();
#endif
}

void systemWaitStart(void)
{
  // This permits to guarantee that the system task is initialized before other
  // tasks waits for the start event.
  while (!isInit)
    vTaskDelay(2);

  xSemaphoreTake(canStartMutex, portMAX_DELAY);
  xSemaphoreGive(canStartMutex);
}

void systemSetCanFly(bool val)
{
  canFly = val;
}

bool systemCanFly(void)
{
  return canFly;
}

void systemSetArmed(bool val)
{
  armed = val;
}

bool systemIsArmed()
{

  return armed || forceArm;
}