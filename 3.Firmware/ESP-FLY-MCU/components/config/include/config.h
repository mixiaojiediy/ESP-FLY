#ifndef CONFIG_H_
#define CONFIG_H_
#include "usec_time.h"

#define PROTOCOL_VERSION 4
#define QUAD_FORMATION_X
#endif

// #define DEBUG_UDP

// Task priorities. Higher number higher priority
#define STABILIZER_TASK_PRI 5
#define SENSORS_TASK_PRI 4
#define UDP_TX_TASK_PRI 3
#define UDP_RX_TASK_PRI 3
#define SYSTEM_TASK_PRI 2
#define LEDSEQCMD_TASK_PRI 1
#define PM_TASK_PRI 0

// Task names
#define SYSTEM_TASK_NAME "SYSTEM"
#define LEDSEQCMD_TASK_NAME "LEDSEQCMD"
#define PM_TASK_NAME "PWRMGNT"
#define SENSORS_TASK_NAME "SENSORS"
#define STABILIZER_TASK_NAME "STABILIZER"
#define UDP_TX_TASK_NAME "UDP_TX"
#define UDP_RX_TASK_NAME "UDP_RX"

#define configBASE_STACK_SIZE CONFIG_BASE_STACK_SIZE

// Task stack sizes
#define SYSTEM_TASK_STACKSIZE (6 * configBASE_STACK_SIZE)
#define LEDSEQCMD_TASK_STACKSIZE (2 * configBASE_STACK_SIZE)
#define PM_TASK_STACKSIZE (4 * configBASE_STACK_SIZE)
#define SENSORS_TASK_STACKSIZE (5 * configBASE_STACK_SIZE)
#define STABILIZER_TASK_STACKSIZE (5 * configBASE_STACK_SIZE)
#define UDP_TX_TASK_STACKSIZE (2 * configBASE_STACK_SIZE)
#define UDP_RX_TASK_STACKSIZE (4 * configBASE_STACK_SIZE)

/**
 * This is the threshold for a propeller/motor to pass. It calculates the variance of the accelerometer X+Y
 * when the propeller is spinning.
 */
#define PROPELLER_BALANCE_TEST_THRESHOLD 2.5f