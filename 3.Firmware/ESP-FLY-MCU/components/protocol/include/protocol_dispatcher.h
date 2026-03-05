/**
 * Protocol Dispatcher - 协议分发模块
 */

#ifndef __PROTOCOL_DISPATCHER_H__
#define __PROTOCOL_DISPATCHER_H__

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * 初始化协议分发模块
 */
void protocolDispatcherInit(void);

/**
 * 测试协议分发模块是否已初始化
 */
bool protocolDispatcherTest(void);

#ifdef __cplusplus
}
#endif

#endif // __PROTOCOL_DISPATCHER_H__
