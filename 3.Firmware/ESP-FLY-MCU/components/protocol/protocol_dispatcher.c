/**
 * Protocol Dispatcher - 协议分发模块
 */

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "protocol_dispatcher.h"
#include "packet_codec.h"
#include "wifi_esp32.h"
#include "command_receiver.h"
#include "config_receiver.h"
#include "motors.h"
#include "power_distribution.h"
#include "zero_calib.h"

#define DEBUG_MODULE "PROTO_DISP"
#include "debug_cf.h"

static bool isInit = false;

static void protocolDispatcherTask(void *param)
{
    UDPPacket udp_packet;
    PacketFrame_t frame;

    DEBUG_PRINT("Protocol Dispatcher task started\n");

    while (1)
    {
        if (!wifiGetDataBlocking(&udp_packet))
        {
            vTaskDelay(1);
            continue;
        }

        if (!packet_parse(udp_packet.data, udp_packet.size, &frame))
        {
            DEBUG_PRINT_LOCAL("[PROTO_RX] Parse failed, len=%u", udp_packet.size);
            continue;
        }

        switch (frame.packet_id)
        {
        case PKT_ID_FLIGHT_CONTROL:
        {
            if (!zero_calib_is_done())
            {
                DEBUG_PRINT_LOCAL("[PROTO] Calibrating, flight control command ignored");
                break;
            }
            FlightControlPacket_t fc_packet;
            if (packet_parseFlightControl(&frame, &fc_packet))
            {
                DEBUG_PRINT_LOCAL("[CTRL] Roll=%.2f, Pitch=%.2f, Yaw=%.2f, Thrust=%u",
                                  (double)fc_packet.roll, (double)fc_packet.pitch,
                                  (double)fc_packet.yaw, fc_packet.thrust);

                commandReceiverHandleFlightControl(&fc_packet);
            }
            break;
        }

        case PKT_ID_PID_CONFIG:
        {
            PIDConfigPacket_t pid_config;
            if (packet_parsePIDConfig(&frame, &pid_config))
            {
                DEBUG_PRINT_LOCAL("[PID] Received all PID parameters");

                // 应用姿态环PID参数
                PIDConfig pid_cfg;

                // Roll 姿态环
                pid_cfg.axis = 0;       // Roll
                pid_cfg.isRateLoop = 0; // 姿态环
                pid_cfg.kp = pid_config.roll_angle_kp;
                pid_cfg.ki = pid_config.roll_angle_ki;
                pid_cfg.kd = pid_config.roll_angle_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Roll Angle: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);

                // Pitch 姿态环
                pid_cfg.axis = 1; // Pitch
                pid_cfg.isRateLoop = 0;
                pid_cfg.kp = pid_config.pitch_angle_kp;
                pid_cfg.ki = pid_config.pitch_angle_ki;
                pid_cfg.kd = pid_config.pitch_angle_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Pitch Angle: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);

                // Yaw 姿态环
                pid_cfg.axis = 2; // Yaw
                pid_cfg.isRateLoop = 0;
                pid_cfg.kp = pid_config.yaw_angle_kp;
                pid_cfg.ki = pid_config.yaw_angle_ki;
                pid_cfg.kd = pid_config.yaw_angle_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Yaw Angle: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);

                // 应用速度环PID参数

                // Roll 速度环
                pid_cfg.axis = 0;       // Roll
                pid_cfg.isRateLoop = 1; // 速度环
                pid_cfg.kp = pid_config.roll_rate_kp;
                pid_cfg.ki = pid_config.roll_rate_ki;
                pid_cfg.kd = pid_config.roll_rate_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Roll Rate: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);

                // Pitch 速度环
                pid_cfg.axis = 1; // Pitch
                pid_cfg.isRateLoop = 1;
                pid_cfg.kp = pid_config.pitch_rate_kp;
                pid_cfg.ki = pid_config.pitch_rate_ki;
                pid_cfg.kd = pid_config.pitch_rate_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Pitch Rate: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);

                // Yaw 速度环
                pid_cfg.axis = 2; // Yaw
                pid_cfg.isRateLoop = 1;
                pid_cfg.kp = pid_config.yaw_rate_kp;
                pid_cfg.ki = pid_config.yaw_rate_ki;
                pid_cfg.kd = pid_config.yaw_rate_kd;
                configReceiverApplyPID(&pid_cfg);
                DEBUG_PRINT_LOCAL("[PID] Yaw Rate: Kp=%.3f, Ki=%.3f, Kd=%.3f",
                                  (double)pid_cfg.kp, (double)pid_cfg.ki, (double)pid_cfg.kd);
            }
            break;
        }

        case PKT_ID_MOTOR_TEST:
        {
            if (!zero_calib_is_done())
            {
                DEBUG_PRINT_LOCAL("[PROTO] Calibrating, motor test command ignored");
                break;
            }
            MotorTestPacket_t motor_test;
            if (packet_parseMotorTest(&frame, &motor_test))
            {
                DEBUG_PRINT_LOCAL("[MOTOR] Enable=%d, M1=%u, M2=%u, M3=%u, M4=%u",
                                  motor_test.enable, motor_test.motor1_pwm, motor_test.motor2_pwm,
                                  motor_test.motor3_pwm, motor_test.motor4_pwm);

                // 根据使能标志判断是否进入测试模式
                if (motor_test.enable == 0)
                {
                    // 禁用测试模式
                    powerDistributionSetMotorTestMode(false);
                    powerStop(); // 停止所有电机
                    DEBUG_PRINT_LOCAL("[MOTOR] Motor test mode disabled");
                }
                else
                {
                    // 启用电机测试模式，防止姿态控制覆盖电机设置
                    powerDistributionSetMotorTestMode(true);

                    // 设置四个电机的PWM占空比
                    motorsSetRatio(0, motor_test.motor1_pwm);
                    motorsSetRatio(1, motor_test.motor2_pwm);
                    motorsSetRatio(2, motor_test.motor3_pwm);
                    motorsSetRatio(3, motor_test.motor4_pwm);
                }
            }
            break;
        }

        default:
            DEBUG_PRINT_LOCAL("[PROTO_RX] Unknown packet: 0x%02X", frame.packet_id);
            break;
        }
    }
}

void protocolDispatcherInit(void)
{
    if (isInit)
    {
        return;
    }

    configReceiverInit();

    xTaskCreate(protocolDispatcherTask, "PROTO_DISP", 4096, NULL, 3, NULL);

    isInit = true;
    DEBUG_PRINT("Protocol Dispatcher initialized\n");
}

bool protocolDispatcherTest(void)
{
    return isInit;
}
