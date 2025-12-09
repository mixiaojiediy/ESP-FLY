/**
 * ESP-Drone Firmware
 *
 * Copyright 2019-2020  Espressif Systems (Shanghai)
 * Copyright (c) 2014, Bitcraze AB, All rights reserved.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 3.0 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.
 *
 * i2c_drv.c - i2c driver implementation
 *
 * @note
 * For some reason setting CR1 reg in sequence with
 * I2C_AcknowledgeConfig(I2C_SENSORS, ENABLE) and after
 * I2C_GenerateSTART(I2C_SENSORS, ENABLE) sometimes creates an
 * instant start->stop condition (3.9us long) which I found out with an I2C
 * analyzer. This fast start->stop is only possible to generate if both
 * start and stop flag is set in CR1 at the same time. So i tried setting the CR1
 * at once with I2C_SENSORS->CR1 = (I2C_CR1_START | I2C_CR1_ACK | I2C_CR1_PE) and the
 * problem is gone. Go figure...
 */

#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"

#include "driver/gpio.h"
#include "stm32_legacy.h"
#include "i2c_drv.h"
#include "config.h"
#define DEBUG_MODULE "I2CDRV"
#include "debug_cf.h"

// Definitions of sensors I2C bus
#define I2C_DEFAULT_SENSORS_CLOCK_SPEED 100000
// #define I2C_DEFAULT_SENSORS_CLOCK_SPEED 400000

// Definition of eeprom and deck I2C buss,use two i2c with 400Khz clock simultaneously could trigger the watchdog
#define I2C_DEFAULT_DECK_CLOCK_SPEED 100000

static bool isinit_i2cPort[2] = {0, 0};

// Cost definitions of busses
static const I2cDef sensorBusDef = {
    .i2cPort = I2C_NUM_0,
    .i2cClockSpeed = I2C_DEFAULT_SENSORS_CLOCK_SPEED,
    .gpioSCLPin = CONFIG_I2C0_PIN_SCL,
    .gpioSDAPin = CONFIG_I2C0_PIN_SDA,
    .gpioPullup = GPIO_PULLUP_ENABLE, // 启用上拉电阻以支持 I2C 通信
};

I2cDrv sensorsBus = {
    .def = &sensorBusDef,
    .isBusFreeMutex = NULL,
};

static const I2cDef deckBusDef = {
#ifdef CONFIG_IDF_TARGET_ESP32C3
    .i2cPort = I2C_NUM_0, // ESP32-C3 only has I2C_NUM_0
    // ESP32-C3只有一个I2C端口，必须与sensorsBus共享相同的引脚
    .i2cClockSpeed = I2C_DEFAULT_SENSORS_CLOCK_SPEED, // 使用传感器的速度
    .gpioSCLPin = CONFIG_I2C0_PIN_SCL,                // 使用传感器总线的引脚 (GPIO6)
    .gpioSDAPin = CONFIG_I2C0_PIN_SDA,                // 使用传感器总线的引脚 (GPIO7)
#else
    .i2cPort = I2C_NUM_1,
    .i2cClockSpeed = I2C_DEFAULT_DECK_CLOCK_SPEED,
    .gpioSCLPin = CONFIG_I2C1_PIN_SCL,
    .gpioSDAPin = CONFIG_I2C1_PIN_SDA,
#endif
    .gpioPullup = GPIO_PULLUP_ENABLE,
};

I2cDrv deckBus = {
    .def = &deckBusDef,
    .isBusFreeMutex = NULL,
};

static void i2cdrvInitBus(I2cDrv *i2c)
{
    // Always create mutex for this bus instance, even if the I2C port is shared
    if (i2c->isBusFreeMutex == NULL)
    {
        i2c->isBusFreeMutex = xSemaphoreCreateMutex();
    }

    if (isinit_i2cPort[i2c->def->i2cPort])
    {
        return;
    }

    // 打印I2C配置信息
    DEBUG_PRINTI("Initializing I2C%d: SDA=GPIO%lu, SCL=GPIO%lu, Speed=%luHz, Pullup=%s",
                 i2c->def->i2cPort,
                 (unsigned long)i2c->def->gpioSDAPin,
                 (unsigned long)i2c->def->gpioSCLPin,
                 (unsigned long)i2c->def->i2cClockSpeed,
                 i2c->def->gpioPullup ? "EN" : "DIS");

    // 先复位GPIO，避免之前的配置干扰
    gpio_reset_pin(i2c->def->gpioSDAPin);
    gpio_reset_pin(i2c->def->gpioSCLPin);
    vTaskDelay(pdMS_TO_TICKS(10));

    i2c_config_t conf = {0};
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = i2c->def->gpioSDAPin;
    conf.sda_pullup_en = i2c->def->gpioPullup;
    conf.scl_io_num = i2c->def->gpioSCLPin;
    conf.scl_pullup_en = i2c->def->gpioPullup;
    conf.master.clk_speed = i2c->def->i2cClockSpeed;

    // ESP32-C3特殊配置：添加时钟拉伸超时设置
    conf.clk_flags = 0;

    esp_err_t err = i2c_param_config(i2c->def->i2cPort, &conf);
    DEBUG_PRINTI("i2c_param_config return = %d", err);

    if (!err)
    {
        err = i2c_driver_install(i2c->def->i2cPort, conf.mode, 0, 0, 0);
        DEBUG_PRINTI("i2c_driver_install return = %d", err);
    }
    else
    {
        DEBUG_PRINTE("I2C param config failed!");
    }

    DEBUG_PRINTI("i2c %d driver install final status = %d", i2c->def->i2cPort, err);
    isinit_i2cPort[i2c->def->i2cPort] = true;
}

//-----------------------------------------------------------

void i2cdrvInit(I2cDrv *i2c)
{
    i2cdrvInitBus(i2c);
}

void i2cdrvTryToRestartBus(I2cDrv *i2c)
{
    i2cdrvInitBus(i2c);
}

// I2C总线扫描函数 - 用于检测连接的设备
void i2cdrvScanBus(I2cDrv *i2c)
{
    DEBUG_PRINTI("Scanning I2C bus %d...", i2c->def->i2cPort);
    DEBUG_PRINTI("SDA pin level: %d, SCL pin level: %d",
                 (int)gpio_get_level(i2c->def->gpioSDAPin),
                 (int)gpio_get_level(i2c->def->gpioSCLPin));

    uint8_t devices_found = 0;

    // 扫描常用的I2C地址范围
    for (uint8_t addr = 0x08; addr < 0x78; addr++)
    {
        i2c_cmd_handle_t cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
        i2c_master_stop(cmd);

        esp_err_t ret = i2c_master_cmd_begin(i2c->def->i2cPort, cmd, pdMS_TO_TICKS(100));
        i2c_cmd_link_delete(cmd);

        if (ret == ESP_OK)
        {
            DEBUG_PRINTI("  Found device at address: 0x%02X", addr);
            devices_found++;
        }
        else if (addr == 0x68) // MPU6050的地址
        {
            DEBUG_PRINTW("  Address 0x68 (MPU6050) scan failed, error: 0x%X", ret);
        }

        vTaskDelay(pdMS_TO_TICKS(2)); // 给总线一些恢复时间
    }

    if (devices_found == 0)
    {
        DEBUG_PRINTW("No I2C devices found on bus %d!", i2c->def->i2cPort);
        DEBUG_PRINTW("Please check:");
        DEBUG_PRINTW("  1. Hardware connections (SDA=GPIO%lu, SCL=GPIO%lu)",
                     (unsigned long)i2c->def->gpioSDAPin, (unsigned long)i2c->def->gpioSCLPin);
        DEBUG_PRINTW("  2. External pull-up resistors (typically 4.7k ohm)");
        DEBUG_PRINTW("  3. Device power supply");
    }
    else
    {
        DEBUG_PRINTI("Total devices found: %d", devices_found);
    }
}