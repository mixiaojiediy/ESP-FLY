/*
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
 * debug_cf.h - Debugging utility functions
 */
#ifndef _DEBUG_CF_H
#define _DEBUG_CF_H
#endif

#include "config.h"
#include "esp_log.h"

#ifndef DEBUG_MODULE
#define DEBUG_MODULE "NULL"
#endif

#define DEBUG_PRINT_LOCAL(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_INFO, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINT(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_DEBUG, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINTE(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_ERROR, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINTW(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_WARN, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINTI(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_INFO, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINTD(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_DEBUG, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINTV(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_VERBOSE, DEBUG_MODULE, fmt, ##__VA_ARGS__)
#define DEBUG_PRINT_OS(fmt, ...) ESP_LOG_LEVEL_LOCAL(ESP_LOG_INFO, DEBUG_MODULE, fmt, ##__VA_ARGS__)