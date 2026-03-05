#include <string.h>
#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"
#include "esp_log.h"

#include "config.h"
#include "system.h"
#include "pm_esplane.h"
#include "adc_esp32.h"
#include "commander.h"
#include "stm32_legacy.h"
#include "wifi_esp32.h"
#define DEBUG_MODULE "PM"
#include "debug_cf.h"
#include "static_mem.h"

// 电池信息发送间隔（毫秒）
#define BATTERY_INFO_SEND_INTERVAL_MS 1000

// 电池信息包通道定义
#define BATTERY_INFO_CHANNEL 0

typedef struct _PmSyslinkInfo
{
  union
  {
    uint8_t flags;
    struct
    {
      uint8_t chg : 1;
      uint8_t pgood : 1;
      uint8_t unused : 6;
    };
  };
  float vBat;
  float chargeCurrent;
#ifdef PM_SYSTLINK_INLCUDE_TEMP
  float temp;
#endif
} __attribute__((packed)) PmSyslinkInfo;

static float batteryVoltage;
static uint16_t batteryVoltageMV;
static float batteryVoltageMin = 6.0;
static float batteryVoltageMax = 0.0;

static float extBatteryVoltage;
static uint16_t extBatteryVoltageMV;
static uint16_t extBatVoltDeckPin;
static bool isExtBatVoltDeckPinSet = false;
static float extBatVoltMultiplier;
static float extBatteryCurrent;
static uint16_t extBatCurrDeckPin;
static bool isExtBatCurrDeckPinSet = false;
static float extBatCurrAmpPerVolt;

#ifdef PM_SYSTLINK_INLCUDE_TEMP
static float temp;
#endif

static uint32_t batteryLowTimeStamp;
static uint32_t batteryCriticalLowTimeStamp;
static bool isInit;
static PMStates pmState;
static PmSyslinkInfo pmSyslinkInfo;

static uint8_t batteryLevel;

static void pmSetBatteryVoltage(float voltage);

const static float bat671723HS25C[10] =
    {
        3.00, // 00%
        3.78, // 10%
        3.83, // 20%
        3.87, // 30%
        3.89, // 40%
        3.92, // 50%
        3.96, // 60%
        4.00, // 70%
        4.04, // 80%
        4.10  // 90%
};

STATIC_MEM_TASK_ALLOC(pmTask, PM_TASK_STACKSIZE);

void pmInit(void)
{
  ESP_LOGI("PM", "pmInit() called, isInit=%d", isInit);
  if (isInit)
  {
    return;
  }

  pmEnableExtBatteryVoltMeasuring(CONFIG_ADC1_PIN, 2); // ADC1 PIN is fixed to ADC channel
  ESP_LOGI("PM", "pmEnableExtBatteryVoltMeasuring done");

  pmSyslinkInfo.pgood = false;
  pmSyslinkInfo.chg = false;
  pmSyslinkInfo.vBat = 3.7f;
  pmSetBatteryVoltage(pmSyslinkInfo.vBat);

  STATIC_MEM_TASK_CREATE(pmTask, pmTask, PM_TASK_NAME, NULL, PM_TASK_PRI);
  ESP_LOGI("PM", "PM Task created");
  isInit = true;
  ESP_LOGI("PM", "pmInit() done, isInit=%d", isInit);
}

/**
 * Sets the battery voltage and its min and max values
 */
static void pmSetBatteryVoltage(float voltage)
{
  batteryVoltage = voltage;
  batteryVoltageMV = (uint16_t)(voltage * 1000);
  if (batteryVoltageMax < voltage)
  {
    batteryVoltageMax = voltage;
  }
  if (batteryVoltageMin > voltage)
  {
    batteryVoltageMin = voltage;
  }
}

/**
 * Returns a number from 0 to 9 where 0 is completely discharged
 * and 9 is 90% charged.
 */
static int32_t pmBatteryChargeFromVoltage(float voltage)
{
  int charge = 0;

  if (voltage < bat671723HS25C[0])
  {
    return 0;
  }
  if (voltage > bat671723HS25C[9])
  {
    return 9;
  }
  while (voltage > bat671723HS25C[charge])
  {
    charge++;
  }

  return charge;
}

float pmGetBatteryVoltage(void)
{
  return batteryVoltage;
}

float pmGetBatteryVoltageMin(void)
{
  return batteryVoltageMin;
}

float pmGetBatteryVoltageMax(void)
{
  return batteryVoltageMax;
}

PMStates pmUpdateState()
{
  PMStates state;
  bool isCharging = pmSyslinkInfo.chg;
  bool isPgood = pmSyslinkInfo.pgood;
  uint32_t batteryLowTime;

  batteryLowTime = xTaskGetTickCount() - batteryLowTimeStamp;

  if (isPgood && !isCharging)
  {
    state = charged;
  }
  else if (isPgood && isCharging)
  {
    state = charging;
  }
  else if (!isPgood && !isCharging && (batteryLowTime > PM_BAT_LOW_TIMEOUT))
  {
    state = lowPower;
  }
  else
  {
    state = battery;
  }

  return state;
}

void pmEnableExtBatteryCurrMeasuring(uint8_t pin, float ampPerVolt)
{
  extBatCurrDeckPin = pin;
  isExtBatCurrDeckPinSet = true;
  extBatCurrAmpPerVolt = ampPerVolt;
}

float pmMeasureExtBatteryCurrent(void)
{
  float current;

  if (isExtBatCurrDeckPinSet)
  {
    current = analogReadVoltage(extBatCurrDeckPin) * extBatCurrAmpPerVolt;
  }
  else
  {
    current = 0.0;
  }

  return current;
}

uint8_t pmGetBatteryLevel(void)
{
  return batteryLevel;
}

PMStates pmGetState(void)
{
  return pmState;
}

void pmEnableExtBatteryVoltMeasuring(uint8_t pin, float multiplier)
{
  extBatVoltDeckPin = pin;
  isExtBatVoltDeckPinSet = true;
  extBatVoltMultiplier = multiplier;
}

float pmMeasureExtBatteryVoltage(void)
{
  float voltage;

  if (isExtBatVoltDeckPinSet)
  {
    voltage = analogReadVoltage(extBatVoltDeckPin) * extBatVoltMultiplier;
  }
  else
  {
    voltage = 0.0;
  }

  return voltage;
}

bool pmIsBatteryLow(void)
{
  return (pmState == lowPower);
}

bool pmIsChargerConnected(void)
{
  return (pmState == charging) || (pmState == charged);
}

bool pmIsCharging(void)
{
  return (pmState == charging);
}
// return true if battery discharging
bool pmIsDischarging(void)
{
  PMStates pmState;
  pmState = pmUpdateState();
  return (pmState == lowPower) || (pmState == battery);
}

void pmTask(void *param)
{
  PMStates pmStateOld = battery;
  uint32_t tickCount = 0;
  static bool batteryInfoPrinted = false; // 电池信息是否已打印标志

  ESP_LOGI("PM", "pmTask started!");

  tickCount = xTaskGetTickCount();
  batteryLowTimeStamp = tickCount;
  batteryCriticalLowTimeStamp = tickCount;

  ESP_LOGI("PM", "pmTask waiting for systemStart...");
  systemWaitStart();
  ESP_LOGI("PM", "pmTask systemStart done, entering main loop");

  while (1)
  {
    vTaskDelay(M2T(100));
    extBatteryVoltage = pmMeasureExtBatteryVoltage();
    extBatteryVoltageMV = (uint16_t)(extBatteryVoltage * 1000);
    extBatteryCurrent = pmMeasureExtBatteryCurrent();
    pmSetBatteryVoltage(extBatteryVoltage);
    batteryLevel = pmBatteryChargeFromVoltage(pmGetBatteryVoltage()) * 10;

    // 上电时只打印一次电池电压信息
    if (!batteryInfoPrinted)
    {
      batteryInfoPrinted = true;
      ESP_LOGI("PM", "========== Battery Status (power on) ==========");
      ESP_LOGI("PM", "  ExtBatteryVoltage: %.3fV (%umV)", extBatteryVoltage, extBatteryVoltageMV);
      ESP_LOGI("PM", "  BatteryVoltage: %.3fV (%umV)", batteryVoltage, batteryVoltageMV);
      ESP_LOGI("PM", "  BatteryLevel: %u%%", batteryLevel);
      ESP_LOGI("PM", "  ExtBatVoltDeckPin: %u, isSet: %d, Multiplier: %.2f",
               extBatVoltDeckPin, isExtBatVoltDeckPinSet, extBatVoltMultiplier);
      ESP_LOGI("PM", "================================================");
    }

    tickCount = xTaskGetTickCount();

    if (pmGetBatteryVoltage() > PM_BAT_LOW_VOLTAGE)
    {
      batteryLowTimeStamp = tickCount;
    }
    if (pmGetBatteryVoltage() > PM_BAT_CRITICAL_LOW_VOLTAGE)
    {
      batteryCriticalLowTimeStamp = tickCount;
    }

    pmState = pmUpdateState();

    if (pmState != pmStateOld)
    {
      // Actions on state change
      switch (pmState)
      {
      case charged:
        // Battery fully charged
        systemSetCanFly(false);
        break;
      case charging:
        // USB connected, charging
        systemSetCanFly(false);
        break;

      case lowPower:
        // Low battery warning
        systemSetCanFly(true);
        break;
      case battery:
        // USB disconnected
        systemSetCanFly(true);
        break;
      default:
        systemSetCanFly(true);
        break;
      }
      pmStateOld = pmState;
    }
    // Actions during state
    switch (pmState)
    {
    case charged:
      break;
    case charging:
      break;
    case lowPower:
      break;
    case battery:
      break;
    default:
      break;
    }
  }
}
