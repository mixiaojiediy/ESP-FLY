/**
 * Status LED Driver for WS2812
 * 
 * ESP-Drone Firmware
 * Copyright 2024 Espressif Systems (Shanghai)
 * 
 * GPIO18 - WS2812 RGB LED
 */

#ifndef __STATUS_LED_H__
#define __STATUS_LED_H__

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * LED状态枚举
 */
typedef enum {
    STATUS_LED_BOOTING,      // 启动中 - 绿灯闪烁
    STATUS_LED_CALIBRATING,  // 校准中 - 蓝灯闪烁
    STATUS_LED_NORMAL,       // 正常运行 - 绿灯常亮
    STATUS_LED_ERROR,        // 错误 - 红灯常亮
    STATUS_LED_OFF,          // 关闭
} status_led_state_t;

/**
 * @brief 初始化状态LED
 * 
 * @return true 成功
 * @return false 失败
 */
bool statusLedInit(void);

/**
 * @brief 设置LED状态
 * 
 * @param state LED状态
 */
void statusLedSet(status_led_state_t state);

/**
 * @brief LED测试函数
 * 
 * @return true 测试通过
 * @return false 测试失败
 */
bool statusLedTest(void);

/**
 * @brief 去初始化LED
 */
void statusLedDeinit(void);

#ifdef __cplusplus
}
#endif

#endif /* __STATUS_LED_H__ */
