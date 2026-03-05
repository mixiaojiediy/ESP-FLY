#ifndef __POWER_DISTRIBUTION_H__
#define __POWER_DISTRIBUTION_H__

#include "stabilizer_types.h"

void powerDistributionInit(void);
bool powerDistributionTest(void);
void powerDistribution(const control_t *control);
void powerStop();
void powerDistributionSetMotorTestMode(bool enable);

#endif //__POWER_DISTRIBUTION_H__
