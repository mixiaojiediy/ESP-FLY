/**
 * Command Receiver - 飞行控制命令处理
 */

#ifndef __COMMAND_RECEIVER_H__
#define __COMMAND_RECEIVER_H__

#include <stdbool.h>
#include "packet_codec.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * 初始化命令接收模块
 */
void commandReceiverInit(void);

/**
 * 测试命令接收模块是否已初始化
 * @return true if initialized
 */
bool commandReceiverTest(void);

/**
 * 处理飞行控制命令
 */
void commandReceiverHandleFlightControl(const FlightControlPacket_t *fc_packet);

#ifdef __cplusplus
}
#endif

#endif // __COMMAND_RECEIVER_H__
