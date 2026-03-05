#ifndef __WORKER_H
#define __WORKER_H

#include <stdbool.h>

void workerInit();

bool workerTest();

/**
 * Light printf implementation
 *
 * This function exectute the worker loop and never returns except if the worker
 * module has not been initialized.
 */
void workerLoop();

/**
 * Schedule a function for execution by the worker loop
 * The function will be executed as soon as possible by the worker loop.
 * Scheduled functions are stacked in a FIFO queue.
 *
 * @param function Function to be executed
 * @param arg      Argument that will be passed to the function when executed
 * @return         0 in case of success. Anything else on failure.
 */
int workerSchedule(void (*function)(void *), void *arg);

#endif //__WORKER_H
