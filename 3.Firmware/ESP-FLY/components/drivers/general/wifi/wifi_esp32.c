#include <string.h>
#include <stdio.h>

#include "config.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

#include "queuemonitor.h"
#include "wifi_esp32.h"
#include "config_receiver.h"
#include "stm32_legacy.h"
#include "motors.h"
#include "sensors.h"
#include "sensors_mpu6050_hm5883L_ms5611.h"
#include "sensfusion6.h"
#include "console.h"
#include "attitude_controller.h"
#define DEBUG_MODULE "WIFI_UDP"
#include "debug_cf.h"

// 飞行控制参数结构体
typedef struct
{
    float roll;
    float pitch;
    float yaw;
    uint16_t thrust;
} __attribute__((packed)) setpointPacket_t;

// 状态监控打印间隔(毫秒)
#define MONITOR_PRINT_INTERVAL_MS 1000

// 飞控信息打印间隔控制
static uint32_t lastFlightCtrlPrintTime = 0;
#define FLIGHT_CTRL_PRINT_INTERVAL_MS 1000

#define UDP_SERVER_PORT 2390
#define UDP_SERVER_BUFSIZE 128

static struct sockaddr_in6 source_addr; // Large enough for both IPv4 or IPv6

// #define WIFI_SSID      "Udp Server"
static char WIFI_SSID[32] = "ESP-DRONE";
static char WIFI_PWD[64] = "12345678";
static uint8_t WIFI_CH = 1;
#define MAX_STA_CONN (3)

#ifndef MAC2STR
#define MAC2STR(a) (a)[0], (a)[1], (a)[2], (a)[3], (a)[4], (a)[5]
#define MACSTR "%02x:%02x:%02x:%02x:%02x:%02x"
#endif

static char rx_buffer[UDP_SERVER_BUFSIZE];
static char tx_buffer[UDP_SERVER_BUFSIZE];
const int addr_family = (int)AF_INET;
const int ip_protocol = IPPROTO_IP;
static struct sockaddr_in dest_addr;
static int sock;

static xQueueHandle udpDataRx;
static xQueueHandle udpDataTx;
static UDPPacket inPacket;
static UDPPacket outPacket;

static bool isInit = false;
static bool isUDPInit = false;
static bool isUDPConnected = false;

static esp_err_t udp_server_create(void *arg);

static uint8_t calculate_cksum(void *data, size_t len)
{
    unsigned char *c = data;
    int i;
    unsigned char cksum = 0;

    for (i = 0; i < len; i++)
    {
        cksum += *(c++);
    }

    return cksum;
}

static void wifi_event_handler(void *arg, esp_event_base_t event_base,
                               int32_t event_id, void *event_data)
{
    if (event_id == WIFI_EVENT_AP_STACONNECTED)
    {
        wifi_event_ap_staconnected_t *event = (wifi_event_ap_staconnected_t *)event_data;
        DEBUG_PRINT_LOCAL("station" MACSTR "join, AID=%d", MAC2STR(event->mac), event->aid);
    }
    else if (event_id == WIFI_EVENT_AP_STADISCONNECTED)
    {
        wifi_event_ap_stadisconnected_t *event = (wifi_event_ap_stadisconnected_t *)event_data;
        DEBUG_PRINT_LOCAL("station" MACSTR "leave, AID=%d", MAC2STR(event->mac), event->aid);
    }
}

bool wifiTest(void)
{
    return isInit;
};

bool wifiGetDataBlocking(UDPPacket *in)
{
    /* command step - receive  02  from udp rx queue */
    while (xQueueReceive(udpDataRx, in, portMAX_DELAY) != pdTRUE)
    {
        vTaskDelay(1);
    }; // Don't return until we get some data on the UDP

    return true;
};

bool wifiSendData(uint32_t size, uint8_t *data)
{
    static UDPPacket outStage;
    outStage.size = size;
    memcpy(outStage.data, data, size);
    // Dont' block when sending
    return (xQueueSend(udpDataTx, &outStage, M2T(100)) == pdTRUE);
};

static esp_err_t udp_server_create(void *arg)
{
    if (isUDPInit)
    {
        return ESP_OK;
    }

    struct sockaddr_in *pdest_addr = &dest_addr;
    pdest_addr->sin_addr.s_addr = htonl(INADDR_ANY);
    pdest_addr->sin_family = AF_INET;
    pdest_addr->sin_port = htons(UDP_SERVER_PORT);

    sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
    if (sock < 0)
    {
        DEBUG_PRINT_LOCAL("Unable to create socket: errno %d", errno);
        return ESP_FAIL;
    }
    DEBUG_PRINT_LOCAL("Socket created");

    int err = bind(sock, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
    if (err < 0)
    {
        DEBUG_PRINT_LOCAL("Socket unable to bind: errno %d", errno);
    }
    DEBUG_PRINT_LOCAL("Socket bound, port %d", UDP_SERVER_PORT);

    isUDPInit = true;
    return ESP_OK;
}

static void udp_server_rx_task(void *pvParameters)
{
    uint8_t cksum = 0;
    socklen_t socklen = sizeof(source_addr);

    while (true)
    {
        if (isUDPInit == false)
        {
            vTaskDelay(20);
            continue;
        }
        int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer) - 1, 0, (struct sockaddr *)&source_addr, &socklen);
        /* command step - receive  01 from Wi-Fi UDP */
        if (len < 0)
        {
            DEBUG_PRINT_LOCAL("recvfrom failed: errno %d", errno);
            break;
        }
        else if (len > WIFI_RX_TX_PACKET_SIZE - 4)
        {
            DEBUG_PRINT_LOCAL("Received data length = %d > 64", len);
        }
        else
        {
            // copy part of the UDP packet
            rx_buffer[len] = 0; // Null-terminate whatever we received and treat like a string...
            memcpy(inPacket.data, rx_buffer, len);
            cksum = inPacket.data[len - 1];
            // remove cksum, do not belong to CRTP
            inPacket.size = len - 1;

            uint8_t calc_cksum = calculate_cksum(inPacket.data, len - 1);

            // 首先检查是否是配置命令 (第一个字节为0xAA)
            if (inPacket.data[0] == 0xAA)
            {
                DEBUG_PRINT_LOCAL("[UDP_RX] 检测到配置命令包 (0xAA)");
                // 处理配置命令
                if (configReceiverProcess(inPacket.data, inPacket.size))
                {
                    DEBUG_PRINT_LOCAL("[UDP_RX] 配置命令处理成功");
                    if (!isUDPConnected)
                        isUDPConnected = true;
                }
                else
                {
                    DEBUG_PRINT_LOCAL("[UDP_RX] 配置命令处理失败");
                }
            }
            // check packet
            else if (cksum == calc_cksum && inPacket.size < 64)
            {
                // 解析CRTP头部
                uint8_t port = (inPacket.data[0] >> 4) & 0x0F;
                uint8_t channel = inPacket.data[0] & 0x03;

                // 如果是飞行控制命令 (port=3, channel=0)，解析并打印飞行参数
                if (port == 3 && channel == 0 && inPacket.size >= 15)
                {
                    // 限制打印频率为1秒一次
                    uint32_t now = xTaskGetTickCount();
                    if (now - lastFlightCtrlPrintTime >= pdMS_TO_TICKS(FLIGHT_CTRL_PRINT_INTERVAL_MS))
                    {
                        lastFlightCtrlPrintTime = now;
                        setpointPacket_t *setpoint = (setpointPacket_t *)&inPacket.data[1];
                        DEBUG_PRINT_LOCAL("[飞控] Roll=%.2f, Pitch=%.2f, Yaw=%.2f, Thrust=%u",
                                          (double)setpoint->roll, (double)setpoint->pitch,
                                          (double)setpoint->yaw, setpoint->thrust);
                    }
                }
                else
                {
                    DEBUG_PRINT_LOCAL("[UDP_RX] CRTP包: port=%d, channel=%d, payload_size=%d",
                                      port, channel, inPacket.size - 1);
                }

                xQueueSend(udpDataRx, &inPacket, M2T(2));
                if (!isUDPConnected)
                    isUDPConnected = true;
            }
            else
            {
                DEBUG_PRINT_LOCAL("[UDP_RX] 校验和不匹配! 收到=0x%02X, 计算=0x%02X", cksum, calc_cksum);
            }

#ifdef DEBUG_UDP
            DEBUG_PRINT_LOCAL("1.Received data size = %d  %02X \n cksum = %02X", len, inPacket.data[0], cksum);
            for (size_t i = 0; i < len; i++)
            {
                DEBUG_PRINT_LOCAL(" data[%d] = %02X ", i, inPacket.data[i]);
            }
#endif
        }
    }
}

// 监控任务：每秒打印电机PWM和MPU6050姿态信息，并发送到APP
static void status_monitor_task(void *pvParameters)
{
    Axis3f gyroData = {0};
    Axis3f accData = {0};
    float roll, pitch, yaw; // 姿态角度

    vTaskDelay(M2T(5000)); // 等待系统初始化完成

    while (TRUE)
    {
        vTaskDelay(M2T(MONITOR_PRINT_INTERVAL_MS));

        // 直接获取传感器数据（不通过队列）
        sensorsGetData(&gyroData, &accData);

        // 获取融合后的姿态角度
        sensfusion6GetEulerRPY(&roll, &pitch, &yaw);

        // 打印电机PWM值到串口
        printf("\n========== 状态监控 ==========\n");
        printf("[电机PWM] M1=%d, M2=%d, M3=%d, M4=%d\n",
               motorsGetRatio(0), motorsGetRatio(1),
               motorsGetRatio(2), motorsGetRatio(3));

        // 打印姿态角度（融合后的结果）
        printf("[姿态角] Roll=%.2f, Pitch=%.2f, Yaw=%.2f (deg)\n",
               (double)roll, (double)pitch, (double)yaw);

        // 打印MPU6050原始数据
        printf("[陀螺仪] GX=%.2f, GY=%.2f, GZ=%.2f (deg/s)\n",
               (double)gyroData.x, (double)gyroData.y, (double)gyroData.z);
        printf("[加速度] AX=%.2f, AY=%.2f, AZ=%.2f (g)\n",
               (double)accData.x, (double)accData.y, (double)accData.z);
        printf("===============================\n");

        // 发送状态数据到APP控制台（仅在UDP连接后发送）
        if (isUDPConnected)
        {
            // 发送电机PWM
            consolePrintf("[PWM] M1=%d M2=%d M3=%d M4=%d\n",
                          motorsGetRatio(0), motorsGetRatio(1),
                          motorsGetRatio(2), motorsGetRatio(3));
            
            // 发送姿态角
            consolePrintf("[ATT] R=%.1f P=%.1f Y=%.1f\n",
                          (double)roll, (double)pitch, (double)yaw);
            
            // 发送陀螺仪数据
            consolePrintf("[GYR] X=%.2f Y=%.2f Z=%.2f\n",
                          (double)gyroData.x, (double)gyroData.y, (double)gyroData.z);
            
            // 发送加速度数据
            consolePrintf("[ACC] X=%.2f Y=%.2f Z=%.2f\n",
                          (double)accData.x, (double)accData.y, (double)accData.z);
            
            // 发送PID参数
            attitudeControllerSendPidToConsole();
            
            // 刷新控制台缓冲区
            consoleFlush();
        }
    }
}

static void udp_server_tx_task(void *pvParameters)
{

    while (TRUE)
    {
        if (isUDPInit == false)
        {
            vTaskDelay(20);
            continue;
        }
        if ((xQueueReceive(udpDataTx, &outPacket, 5) == pdTRUE) && isUDPConnected)
        {
            memcpy(tx_buffer, outPacket.data, outPacket.size);
            tx_buffer[outPacket.size] = calculate_cksum(tx_buffer, outPacket.size);
            tx_buffer[outPacket.size + 1] = 0;

            int err = sendto(sock, tx_buffer, outPacket.size + 1, 0, (struct sockaddr *)&source_addr, sizeof(source_addr));
            if (err < 0)
            {
                DEBUG_PRINT_LOCAL("Error occurred during sending: errno %d", errno);
                continue;
            }
#ifdef DEBUG_UDP
            DEBUG_PRINT_LOCAL("Send data to");
            for (size_t i = 0; i < outPacket.size + 1; i++)
            {
                DEBUG_PRINT_LOCAL(" data_send[%d] = %02X ", i, tx_buffer[i]);
            }
#endif
        }
    }
}

void wifiInit(void)
{
    if (isInit)
    {
        return;
    }

    esp_netif_t *ap_netif = NULL;
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ap_netif = esp_netif_create_default_wifi_ap();
    uint8_t mac[6];

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));

    ESP_ERROR_CHECK(esp_wifi_get_mac(ESP_IF_WIFI_AP, mac));
    sprintf(WIFI_SSID, "ESP-DRONE_%02X%02X%02X%02X%02X%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    wifi_config_t wifi_config = {
        .ap = {
            .channel = WIFI_CH,
            .max_connection = MAX_STA_CONN,
            .authmode = WIFI_AUTH_WPA_WPA2_PSK,
        },
    };

    memcpy(wifi_config.ap.ssid, WIFI_SSID, strlen(WIFI_SSID) + 1);
    wifi_config.ap.ssid_len = strlen(WIFI_SSID);
    memcpy(wifi_config.ap.password, WIFI_PWD, strlen(WIFI_PWD) + 1);

    if (strlen(WIFI_PWD) == 0)
    {
        wifi_config.ap.authmode = WIFI_AUTH_OPEN;
    }

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_AP, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    esp_netif_ip_info_t ip_info = {
        .ip.addr = ipaddr_addr("192.168.43.42"),
        .netmask.addr = ipaddr_addr("255.255.255.0"),
        .gw.addr = ipaddr_addr("192.168.43.42"),
    };
    ESP_ERROR_CHECK(esp_netif_dhcps_stop(ap_netif));
    ESP_ERROR_CHECK(esp_netif_set_ip_info(ap_netif, &ip_info));
    ESP_ERROR_CHECK(esp_netif_dhcps_start(ap_netif));

    DEBUG_PRINT_LOCAL("wifi_init_softap complete.SSID:%s password:%s", WIFI_SSID, WIFI_PWD);

    // 初始化配置接收模块
    configReceiverInit();

    // This should probably be reduced to a CRTP packet size
    udpDataRx = xQueueCreate(5, sizeof(UDPPacket)); /* Buffer packets (max 64 bytes) */
    DEBUG_QUEUE_MONITOR_REGISTER(udpDataRx);
    udpDataTx = xQueueCreate(5, sizeof(UDPPacket)); /* Buffer packets (max 64 bytes) */
    DEBUG_QUEUE_MONITOR_REGISTER(udpDataTx);
    if (udp_server_create(NULL) == ESP_FAIL)
    {
        DEBUG_PRINT_LOCAL("UDP server create socket failed!!!");
    }
    else
    {
        DEBUG_PRINT_LOCAL("UDP server create socket succeed!!!");
    }
    xTaskCreate(udp_server_tx_task, UDP_TX_TASK_NAME, UDP_TX_TASK_STACKSIZE, NULL, UDP_TX_TASK_PRI, NULL);
    xTaskCreate(udp_server_rx_task, UDP_RX_TASK_NAME, UDP_RX_TASK_STACKSIZE, NULL, UDP_RX_TASK_PRI, NULL);
    xTaskCreate(status_monitor_task, "STATUS_MON", 4096, NULL, 1, NULL);
    isInit = true;
}