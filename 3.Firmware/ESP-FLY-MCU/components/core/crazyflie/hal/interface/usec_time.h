#ifndef USEC_TIME_H_
#define USEC_TIME_H_

#include <stdint.h>

/**
 * Initialize microsecond-resolution timer (TIM1).
 */
void initUsecTimer(void);

/**
 * Get microsecond-resolution timestamp.
 */
uint64_t usecTimestamp(void);

#endif /* USEC_TIME_H_ */
