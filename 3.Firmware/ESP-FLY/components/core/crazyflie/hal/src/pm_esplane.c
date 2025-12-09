/**
 *    ||          ____  _ __
 * +------+      / __ )(_) /_______________ _____  ___
 * | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
 * +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
 *  ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
 *
 * ESP-Drone Firmware
 *
 * Copyright 2019-2020  Espressif Systems (Shanghai)
 * Copyright (C) 2011-2012 Bitcraze AB
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, in version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * pm.c - Power Management driver and functions.
 */

#include <string.h>
#include <stdbool.h>

#include "FreeRTOS.h"
#include "task.h"
#include "esp_log.h"

#include "config.h"
#include "system.h"
#include "pm_esplane.h"
#include "adc_esp32.h"
// #include "led.h"  // LED hardware removed
#include "log.h"
#include "ledseq.h"
#include "commander.h"
#include "sound.h"
#include "stm32_legacy.h"
#include "wifi_esp32.h" // 用于发送电池信息
#include "crtp.h"       // CRTP协议定义
// #include "deck.h"
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
// nRF51 internal temp
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

bool pmTest(void)
{
  return isInit;
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
 * Shutdown system
 */
static void pmSystemShutdown(void)
{
#ifdef ACTIVATE_AUTO_SHUTDOWN
// TODO: Implement syslink call to shutdown
#endif
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

void pmSyslinkUpdate(SyslinkPacket *slp)
{
  if (slp->type == SYSLINK_PM_BATTERY_STATE)
  {
    memcpy(&pmSyslinkInfo, &slp->data[0], sizeof(pmSyslinkInfo));
    pmSetBatteryVoltage(pmSyslinkInfo.vBat);
#ifdef PM_SYSTLINK_INLCUDE_TEMP
    temp = pmSyslinkInfo.temp;
#endif
  }
}

void pmSetChargeState(PMChargeStates chgState)
{
  // TODO: Send syslink packafe with charge state
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

/**
 * 发送电池信息到WiFi客户端
 * 数据格式：
 * - Header: CRTP_PORT_PLATFORM (0x0D), channel 0
 * - Data[0-3]: float vbat (电池电压)
 * - Data[4-5]: uint16_t vbatMV (电池电压毫伏)
 * - Data[6]: uint8_t level (电池电量百分比 0-100)
 * - Data[7]: uint8_t state (电池状态)
 */
static void pmSendBatteryInfo(void)
{
  static uint8_t sendBuffer[10];
  uint8_t dataSize = 0;

  // CRTP Header: port=0x0D (PLATFORM), channel=0
  sendBuffer[0] = CRTP_HEADER(CRTP_PORT_PLATFORM, BATTERY_INFO_CHANNEL);
  dataSize++;

  // 电池电压 (float, 4 bytes)
  float vbat = pmGetBatteryVoltage();
  memcpy(&sendBuffer[dataSize], &vbat, sizeof(float));
  dataSize += sizeof(float);

  // 电池电压毫伏 (uint16_t, 2 bytes)
  memcpy(&sendBuffer[dataSize], &batteryVoltageMV, sizeof(uint16_t));
  dataSize += sizeof(uint16_t);

  // 电池电量百分比 (uint8_t, 1 byte)
  sendBuffer[dataSize++] = batteryLevel;

  // 电池状态 (uint8_t, 1 byte)
  sendBuffer[dataSize++] = (uint8_t)pmState;

  // 发送数据
  wifiSendData(dataSize, sendBuffer);
}

void pmTask(void *param)
{
  PMStates pmStateOld = battery;
  uint32_t tickCount = 0;
  static bool batteryInfoPrinted = false;  // 电池信息是否已打印标志
  static uint32_t lastBatterySendTick = 0; // 上次发送电池信息的时间

  ESP_LOGI("PM", "pmTask started!");

#ifdef configUSE_APPLICATION_TASK_TAG
#if configUSE_APPLICATION_TASK_TAG == 1
  vTaskSetApplicationTaskTag(0, (void *)TASK_PM_ID_NBR);
#endif
#endif

  tickCount = xTaskGetTickCount();
  batteryLowTimeStamp = tickCount;
  batteryCriticalLowTimeStamp = tickCount;
  pmSetChargeState(charge300mA);

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

#ifdef DEBUG_EP2
    DEBUG_PRINTD("batteryLevel=%u extBatteryVoltageMV=%u \n", batteryLevel, extBatteryVoltageMV);
#endif
    tickCount = xTaskGetTickCount();

    // 定时发送电池信息到WiFi客户端
    if ((tickCount - lastBatterySendTick) >= M2T(BATTERY_INFO_SEND_INTERVAL_MS))
    {
      lastBatterySendTick = tickCount;
      pmSendBatteryInfo();
    }

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
        // ledseqStop(&seq_charging);
        // ledseqRunBlocking(&seq_charged);
        soundSetEffect(SND_BAT_FULL);
        systemSetCanFly(false);
        break;
      case charging:
        // ledseqStop(&seq_lowbat);
        // ledseqStop(&seq_charged);
        // ledseqRunBlocking(&seq_charging); // LED disabled
        soundSetEffect(SND_USB_CONN);
        systemSetCanFly(false);
        break;

      case lowPower:
        // ledseqRunBlocking(&seq_lowbat); // LED disabled
        soundSetEffect(SND_BAT_LOW);
        systemSetCanFly(true);
        break;
      case battery:
        // ledseqRunBlocking(&seq_charging);
        // ledseqRun(&seq_charged);
        soundSetEffect(SND_USB_DISC);
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
    {
      // Charge level between 0.0 and 1.0
      float chargeLevel = pmBatteryChargeFromVoltage(pmGetBatteryVoltage()) / 10.0f;
      ledseqSetChargeLevel(chargeLevel);
    }
    break;
    case lowPower:
    {
      uint32_t batteryCriticalLowTime;

      batteryCriticalLowTime = tickCount - batteryCriticalLowTimeStamp;
      if (batteryCriticalLowTime > PM_BAT_CRITICAL_LOW_TIMEOUT)
      {
        pmSystemShutdown();
      }
    }
    break;
    case battery:
    {
      if ((commanderGetInactivityTime() > PM_SYSTEM_SHUTDOWN_TIMEOUT))
      {
        pmSystemShutdown();
      }
    }
    break;
    default:
      break;
    }
  }
}

LOG_GROUP_START(pm)
LOG_ADD(LOG_FLOAT, vbat, &batteryVoltage)
LOG_ADD(LOG_UINT16, vbatMV, &batteryVoltageMV)
LOG_ADD(LOG_FLOAT, extVbat, &extBatteryVoltage)
LOG_ADD(LOG_UINT16, extVbatMV, &extBatteryVoltageMV)
LOG_ADD(LOG_FLOAT, extCurr, &extBatteryCurrent)
LOG_ADD(LOG_FLOAT, chargeCurrent, &pmSyslinkInfo.chargeCurrent)
LOG_ADD(LOG_INT8, state, &pmState)
LOG_ADD(LOG_UINT8, batteryLevel, &batteryLevel)
#ifdef PM_SYSTLINK_INLCUDE_TEMP
LOG_ADD(LOG_FLOAT, temp, &temp)
#endif
LOG_GROUP_STOP(pm)
