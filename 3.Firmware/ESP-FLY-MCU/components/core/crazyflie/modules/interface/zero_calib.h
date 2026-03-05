/**
 * @file zero_calib.h
 * @brief 姿态角零点自动校准模块
 *
 * 通过滑动窗口采集 pitch/roll 角度数据，当方差低于阈值时，
 * 以窗口均值作为零点偏移量完成校准。
 *
 * 参考 ESP-FLY-MCU-PIO 中的 ZeroCalib 实现。
 */

#ifndef __ZERO_CALIB_H__
#define __ZERO_CALIB_H__

#include <stdbool.h>

// ============ 零点校准可配置参数 ============
#define CALIB_WINDOW_SIZE          200     // 滑动窗口大小（采样点数）
#define CALIB_VARIANCE_THR_PITCH   0.005f  // pitch 方差阈值（度^2）
#define CALIB_VARIANCE_THR_ROLL    0.005f  // roll 方差阈值（度^2）
#define CALIB_SAMPLE_INTERVAL_MS   50      // 校准采样间隔（ms）

/**
 * @brief 初始化零点校准模块
 */
void zero_calib_init(void);

/**
 * @brief 重置校准状态，重新开始校准
 */
void zero_calib_reset(void);

/**
 * @brief 更新校准数据（在姿态估计循环中反复调用）
 *
 * @param pitch_deg 当前 pitch 角度（度）
 * @param roll_deg  当前 roll 角度（度）
 * @return true 校准已完成，false 校准仍在进行
 */
bool zero_calib_update(float pitch_deg, float roll_deg);

/**
 * @brief 校准是否已完成
 * @return true 已完成，false 未完成
 */
bool zero_calib_is_done(void);

/**
 * @brief 获取 pitch 零点偏移量（度）
 */
float zero_calib_get_pitch_offset(void);

/**
 * @brief 获取 roll 零点偏移量（度）
 */
float zero_calib_get_roll_offset(void);

#endif /* __ZERO_CALIB_H__ */
