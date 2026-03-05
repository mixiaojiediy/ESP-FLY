/**
 * ,---------,       ____  _ __
 * |  ,-^-,  |      / __ )(_) /_______________ _____  ___
 * | (  O  ) |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
 * | / ,--´  |    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
 *    +------`   /_____/_/\__/\___/_/   \__,_/ /___/\___/
 *
 * Crazyflie control firmware
 *
 * Copyright (C) 2019 Bitcraze AB
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, in version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 *
 * estimator_complementary.c - a complementary estimator
 */

#include "FreeRTOS.h"
#include "queue.h"
#include "stabilizer.h"
#include "estimator_complementary.h"
#include "sensfusion6.h"
#include "sensors.h"
#include "stabilizer_types.h"
#include "static_mem.h"
#include "config.h"
#include "zero_calib.h"

#define ATTITUDE_UPDATE_RATE RATE_250_HZ
#define ATTITUDE_UPDATE_DT 1.0 / ATTITUDE_UPDATE_RATE

#define POS_UPDATE_RATE RATE_100_HZ
#define POS_UPDATE_DT 1.0 / POS_UPDATE_RATE

static bool latestTofMeasurement(tofMeasurement_t *tofMeasurement);

// TOF sensor not supported - keep queue for compatibility but always return invalid measurement
#define TOF_QUEUE_LENGTH (1)
static xQueueHandle tofDataQueue;
STATIC_MEM_QUEUE_ALLOC(tofDataQueue, TOF_QUEUE_LENGTH, sizeof(tofMeasurement_t));

void estimatorComplementaryInit(void)
{
  tofDataQueue = STATIC_MEM_QUEUE_CREATE(tofDataQueue);

  sensfusion6Init();
  zero_calib_init();
}

bool estimatorComplementaryTest(void)
{
  bool pass = true;

  pass &= sensfusion6Test();

  return pass;
}

void estimatorComplementary(state_t *state, sensorData_t *sensorData, control_t *control, const uint32_t tick)
{
  sensorsAcquire(sensorData, tick); // Read sensors at full rate (1000Hz)
  if (RATE_DO_EXECUTE(ATTITUDE_UPDATE_RATE, tick))
  {
    sensfusion6UpdateQ(sensorData->gyro.x, sensorData->gyro.y, sensorData->gyro.z,
                       sensorData->acc.x, sensorData->acc.y, sensorData->acc.z,
                       ATTITUDE_UPDATE_DT);

    // Save attitude, adjusted for the legacy CF2 body coordinate system
    sensfusion6GetEulerRPY(&state->attitude.roll, &state->attitude.pitch, &state->attitude.yaw);

    // Auto zero-point calibration
    if (!zero_calib_is_done())
    {
      // Calibration phase: feed raw angles into calibration algorithm
      zero_calib_update(state->attitude.pitch, state->attitude.roll);
    }
    else
    {
      // Normal phase: apply auto-calibrated offset compensation
      state->attitude.pitch -= zero_calib_get_pitch_offset();
      state->attitude.roll -= zero_calib_get_roll_offset();
    }

    // Save quaternion, hopefully one day this could be used in a better controller.
    // Note that this is not adjusted for the legacy coordinate system
    sensfusion6GetQuaternion(
        &state->attitudeQuaternion.x,
        &state->attitudeQuaternion.y,
        &state->attitudeQuaternion.z,
        &state->attitudeQuaternion.w);

    state->acc.z = sensfusion6GetAccZWithoutGravity(sensorData->acc.x,
                                                    sensorData->acc.y,
                                                    sensorData->acc.z);
  }
}

__attribute__((unused)) static bool latestTofMeasurement(tofMeasurement_t *tofMeasurement)
{
  // TOF sensor not supported - return invalid measurement
  if (tofMeasurement)
  {
    tofMeasurement->distance = 0.0f;
    tofMeasurement->stdDev = 0.0f;
    tofMeasurement->timestamp = 0;
  }
  return false; // Always return false to indicate no valid measurement
}

bool estimatorComplementaryEnqueueTOF(const tofMeasurement_t *tof)
{
  // TOF sensor not supported - do nothing but return success for compatibility
  (void)tof;    // Suppress unused parameter warning
  return false; // Return false to indicate TOF is not available
}
