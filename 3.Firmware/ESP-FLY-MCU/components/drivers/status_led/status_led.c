/**
 * Status LED Driver for WS2812
 * 
 * ESP-Drone Firmware
 * Copyright 2024 Espressif Systems (Shanghai)
 */

#include "status_led.h"
#include "led_strip.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/gpio.h"

#define STATUS_LED_GPIO         18      // GPIO18用于WS2812
#define STATUS_LED_RMT_CHANNEL  0       // RMT通道
#define STATUS_LED_COUNT        1       // LED数量（单个LED）

#define LED_BRIGHTNESS          50      // LED亮度 (0-255)

// LED颜色定义 (使用结构体避免宏在三元运算符中的逗号问题)
typedef struct {
    uint32_t r;
    uint32_t g;
    uint32_t b;
} led_color_t;

static const led_color_t COLOR_RED   = { LED_BRIGHTNESS, 0, 0 };
static const led_color_t COLOR_GREEN = { 0, LED_BRIGHTNESS, 0 };
static const led_color_t COLOR_BLUE  = { 0, 0, LED_BRIGHTNESS };
static const led_color_t COLOR_OFF   = { 0, 0, 0 };

static inline esp_err_t led_set_color(led_strip_handle_t strip, uint32_t index, led_color_t color)
{
    return led_strip_set_pixel(strip, index, color.r, color.g, color.b);
}

static const char *TAG = "STATUS_LED";

static led_strip_handle_t led_strip = NULL;
static TaskHandle_t led_task_handle = NULL;
static status_led_state_t current_state = STATUS_LED_OFF;
static bool is_init = false;

/**
 * LED任务 - 统一处理所有LED状态显示
 */
static void led_task(void *pvParameters)
{
    bool blink_state = false;
    status_led_state_t last_state = STATUS_LED_OFF;

    while (1) {
        // 状态切换时重置闪烁相位
        if (current_state != last_state) {
            blink_state = false;
            last_state = current_state;
        }

        switch (current_state) {
            case STATUS_LED_BOOTING:
                // 启动中 - 绿灯闪烁 (500ms周期)
                led_set_color(led_strip, 0, blink_state ? COLOR_GREEN : COLOR_OFF);
                led_strip_refresh(led_strip);
                blink_state = !blink_state;
                vTaskDelay(pdMS_TO_TICKS(250));
                break;

            case STATUS_LED_CALIBRATING:
                // 校准中 - 蓝灯闪烁 (500ms周期)
                led_set_color(led_strip, 0, blink_state ? COLOR_BLUE : COLOR_OFF);
                led_strip_refresh(led_strip);
                blink_state = !blink_state;
                vTaskDelay(pdMS_TO_TICKS(250));
                break;

            case STATUS_LED_NORMAL:
                // 正常运行 - 绿灯常亮
                led_set_color(led_strip, 0, COLOR_GREEN);
                led_strip_refresh(led_strip);
                vTaskDelay(pdMS_TO_TICKS(100));
                break;

            case STATUS_LED_ERROR:
                // 错误 - 红灯常亮
                led_set_color(led_strip, 0, COLOR_RED);
                led_strip_refresh(led_strip);
                vTaskDelay(pdMS_TO_TICKS(100));
                break;

            case STATUS_LED_OFF:
            default:
                // 关闭LED
                led_set_color(led_strip, 0, COLOR_OFF);
                led_strip_refresh(led_strip);
                vTaskDelay(pdMS_TO_TICKS(100));
                break;
        }
    }
}

bool statusLedInit(void)
{
    if (is_init) {
        ESP_LOGW(TAG, "Status LED already initialized");
        return true;
    }

    ESP_LOGI(TAG, "Initializing Status LED on GPIO%d", STATUS_LED_GPIO);

    // 配置LED Strip
    led_strip_config_t strip_config = {
        .strip_gpio_num = STATUS_LED_GPIO,
        .max_leds = STATUS_LED_COUNT,
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,  // WS2812使用GRB格式
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };

    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000, // 10MHz
        .flags.with_dma = false,
    };

    esp_err_t ret = led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create LED strip: %s", esp_err_to_name(ret));
        return false;
    }

    // 清除LED（关闭）
    led_strip_clear(led_strip);

    // 创建LED任务
    BaseType_t task_ret = xTaskCreate(
        led_task,
        "led_task",
        2048,
        NULL,
        5,
        &led_task_handle
    );

    if (task_ret != pdPASS) {
        ESP_LOGE(TAG, "Failed to create LED task");
        led_strip_del(led_strip);
        led_strip = NULL;
        return false;
    }

    is_init = true;
    ESP_LOGI(TAG, "Status LED initialized successfully");
    
    return true;
}

void statusLedSet(status_led_state_t state)
{
    if (!is_init) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }

    current_state = state;
    ESP_LOGD(TAG, "Set LED state: %d", state);
}

bool statusLedTest(void)
{
    if (!is_init) {
        ESP_LOGE(TAG, "Status LED not initialized");
        return false;
    }

    ESP_LOGI(TAG, "Testing Status LED...");

    // 红色
    led_set_color(led_strip, 0, COLOR_RED);
    led_strip_refresh(led_strip);
    vTaskDelay(pdMS_TO_TICKS(500));

    // 绿色
    led_set_color(led_strip, 0, COLOR_GREEN);
    led_strip_refresh(led_strip);
    vTaskDelay(pdMS_TO_TICKS(500));

    // 蓝色
    led_set_color(led_strip, 0, COLOR_BLUE);
    led_strip_refresh(led_strip);
    vTaskDelay(pdMS_TO_TICKS(500));

    // 关闭
    led_set_color(led_strip, 0, COLOR_OFF);
    led_strip_refresh(led_strip);

    ESP_LOGI(TAG, "Status LED test complete");
    return true;
}

void statusLedDeinit(void)
{
    if (!is_init) {
        return;
    }

    // 删除任务
    if (led_task_handle != NULL) {
        vTaskDelete(led_task_handle);
        led_task_handle = NULL;
    }

    // 关闭LED
    if (led_strip != NULL) {
        led_strip_clear(led_strip);
        led_strip_del(led_strip);
        led_strip = NULL;
    }

    is_init = false;
    ESP_LOGI(TAG, "Status LED deinitialized");
}
