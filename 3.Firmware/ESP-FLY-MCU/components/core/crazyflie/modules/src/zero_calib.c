/**
 * @file zero_calib.c
 * @brief 姿态角零点自动校准模块实现
 *
 * 通过滑动窗口采集 pitch/roll 角度，计算方差判断稳定性，
 * 稳定后以均值作为零点偏移量。
 */

#include "zero_calib.h"
#include "FreeRTOS.h"
#include "task.h"

#define DEBUG_MODULE "ZERO_CALIB"
#include "debug_cf.h"

// ============ 内部状态 ============
static float buf_pitch[CALIB_WINDOW_SIZE];
static float buf_roll[CALIB_WINDOW_SIZE];

static int buf_idx = 0;
static int buf_count = 0;
static bool calib_done = false;

static float pitch_offset = 0.0f;
static float roll_offset = 0.0f;

static TickType_t last_sample_tick = 0;
static int print_counter = 0;

// ============ 内部函数 ============

static float calc_mean(const float *buf, int count)
{
    float sum = 0.0f;
    for (int i = 0; i < count; i++)
    {
        sum += buf[i];
    }
    return sum / count;
}

static float calc_variance(const float *buf, int count)
{
    float mean = calc_mean(buf, count);
    float sum_sq = 0.0f;
    for (int i = 0; i < count; i++)
    {
        float diff = buf[i] - mean;
        sum_sq += diff * diff;
    }
    return sum_sq / count;
}

// ============ 公共接口 ============

void zero_calib_init(void)
{
    zero_calib_reset();
}

void zero_calib_reset(void)
{
    buf_idx = 0;
    buf_count = 0;
    calib_done = false;
    pitch_offset = 0.0f;
    roll_offset = 0.0f;
    last_sample_tick = 0;
    print_counter = 0;
}

bool zero_calib_update(float pitch_deg, float roll_deg)
{
    if (calib_done)
    {
        return true;
    }

    TickType_t now = xTaskGetTickCount();
    // 按固定间隔采样
    if ((now - last_sample_tick) < pdMS_TO_TICKS(CALIB_SAMPLE_INTERVAL_MS))
    {
        return false;
    }
    last_sample_tick = now;

    // 写入环形缓冲区
    buf_pitch[buf_idx] = pitch_deg;
    buf_roll[buf_idx] = roll_deg;
    buf_idx = (buf_idx + 1) % CALIB_WINDOW_SIZE;
    if (buf_count < CALIB_WINDOW_SIZE)
    {
        buf_count++;
    }

    // 窗口未满，继续采集
    if (buf_count < CALIB_WINDOW_SIZE)
    {
        if (buf_count % 20 == 0)  // 每20个采样点打印一次进度
        {
            DEBUG_PRINTI("[AngleCalib] Sampling %d/%d ...\n", buf_count, CALIB_WINDOW_SIZE);
        }
        return false;
    }

    // 计算方差
    float var_pitch = calc_variance(buf_pitch, buf_count);
    float var_roll = calc_variance(buf_roll, buf_count);

    float mean_pitch = calc_mean(buf_pitch, buf_count);
    float mean_roll = calc_mean(buf_roll, buf_count);

    if (++print_counter >= 20)  // 每20次采样打印一次（约1秒）
    {
        print_counter = 0;
        DEBUG_PRINTI("[AngleCalib] var(P:%.4f,R:%.4f) thr(%.4f), mean(P:%.2f,R:%.2f)\n",
                    (double)var_pitch, (double)var_roll,
                    (double)CALIB_VARIANCE_THR_PITCH,
                    (double)mean_pitch, (double)mean_roll);
    }

    // 判断是否稳定
    if (var_pitch < CALIB_VARIANCE_THR_PITCH &&
        var_roll < CALIB_VARIANCE_THR_ROLL)
    {
        // 用窗口均值作为零点偏移
        pitch_offset = calc_mean(buf_pitch, buf_count);
        roll_offset = calc_mean(buf_roll, buf_count);
        calib_done = true;

        DEBUG_PRINTI("========================================\n");
        DEBUG_PRINTI("[AngleCalib] Done! Offset -> Pitch:%.2f  Roll:%.2f\n",
                    (double)pitch_offset, (double)roll_offset);
        DEBUG_PRINTI("========================================\n");
        return true;
    }

    return false;
}

bool zero_calib_is_done(void)
{
    return calib_done;
}

float zero_calib_get_pitch_offset(void)
{
    return pitch_offset;
}

float zero_calib_get_roll_offset(void)
{
    return roll_offset;
}
