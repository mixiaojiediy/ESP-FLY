
#include <stdbool.h>
#define DEBUG_MODULE "COMM"
#include "comm.h"
#include "config.h"

#include "debug_cf.h"
#include "wifi_esp32.h"

static bool isInit;

void commInit(void)
{
  if (isInit)
  {
    return;
  }

  isInit = true;
}

bool commTest(void)
{
  bool pass = isInit;
  DEBUG_PRINTI("wifilinkTest skipped (migrated to wifi_esp32.c)");
  DEBUG_PRINTI("consoleTest skipped (console removed)");

  return pass;
}
