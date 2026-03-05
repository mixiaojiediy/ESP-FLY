/**
 * Data Sender - 数据发送模块
 *
 * 负责从全局变量中采集飞行数据并定时发送到上位机
 */

#ifndef __DATA_SENDER_H__
#define __DATA_SENDER_H__

#include <stdint.h>
#include <stdbool.h>

/**
 * 初始化数据发送模块
 */
void dataSenderInit(void);

/**
 * 高频数据传输任务 (50Hz)
 * 负责发送姿态、控制、电机和传感器数据
 */
void dataSenderHighFreqTask(void *param);

/**
 * 低频数据传输任务 (1Hz)
 * 负责发送 PID 参数和电池状态
 */
void dataSenderLowFreqTask(void *param);

#endif // __DATA_SENDER_H__
