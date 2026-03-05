/**
 * Packet Protocol Implementation
 * 数据包协议实现
 */

#include "packet_codec.h"
#include <stdlib.h>

// ============================================================================
// 内部辅助函数
// ============================================================================

/**
 * 计算校验和
 */
uint8_t packet_calculateChecksum(const uint8_t *data, uint16_t len)
{
    uint8_t checksum = 0;
    for (uint16_t i = 0; i < len; i++)
    {
        checksum += data[i];
    }
    return checksum;
}

/**
 * 验证数据包校验和
 */
bool packet_verifyChecksum(const uint8_t *data, uint16_t len)
{
    if (len < 3)
    { // 至少需要: PacketID + Length + Checksum
        return false;
    }

    // 计算除最后一字节外的所有数据的校验和
    uint8_t calculated = packet_calculateChecksum(data, len - 1);
    uint8_t received = data[len - 1];

    return (calculated == received);
}

// ============================================================================
// 核心打包/解包函数
// ============================================================================

/**
 * 打包数据为PacketFrame
 */
bool packet_pack(PacketFrame_t *packet, uint8_t packet_id,
                 const uint8_t *payload, uint8_t payload_len)
{
    if (packet == NULL || (payload == NULL && payload_len > 0))
    {
        return false;
    }

    if (payload_len > PACKET_MAX_PAYLOAD_SIZE)
    {
        return false;
    }

    packet->packet_id = packet_id;
    packet->length = payload_len;

    if (payload_len > 0)
    {
        memcpy(packet->payload, payload, payload_len);
    }

    // 计算校验和 (PacketID + Length + Payload)
    uint8_t temp_buffer[PACKET_MAX_SIZE];
    temp_buffer[0] = packet->packet_id;
    temp_buffer[1] = packet->length;
    if (payload_len > 0)
    {
        memcpy(&temp_buffer[2], packet->payload, payload_len);
    }

    packet->checksum = packet_calculateChecksum(temp_buffer, 2 + payload_len);

    return true;
}

/**
 * 将PacketFrame序列化为字节流
 */
uint16_t packet_serialize(const PacketFrame_t *packet, uint8_t *buffer, uint16_t buffer_size)
{
    if (packet == NULL || buffer == NULL)
    {
        return 0;
    }

    uint16_t total_len = 2 + packet->length + 1; // PacketID + Length + Payload + Checksum

    if (buffer_size < total_len)
    {
        return 0;
    }

    buffer[0] = packet->packet_id;
    buffer[1] = packet->length;

    if (packet->length > 0)
    {
        memcpy(&buffer[2], packet->payload, packet->length);
    }

    buffer[2 + packet->length] = packet->checksum;

    return total_len;
}

/**
 * 从字节流解析PacketFrame
 */
bool packet_parse(const uint8_t *buffer, uint16_t buffer_len, PacketFrame_t *packet)
{
    if (buffer == NULL || packet == NULL)
    {
        return false;
    }

    // 最小长度检查: PacketID + Length + Checksum = 3
    if (buffer_len < 3)
    {
        return false;
    }

    // 验证校验和
    if (!packet_verifyChecksum(buffer, buffer_len))
    {
        return false;
    }

    // 解析头部
    packet->packet_id = buffer[0];
    packet->length = buffer[1];

    // 长度验证
    if (packet->length > PACKET_MAX_PAYLOAD_SIZE)
    {
        return false;
    }

    // 验证缓冲区长度是否匹配
    uint16_t expected_len = 2 + packet->length + 1;
    if (buffer_len != expected_len)
    {
        return false;
    }

    // 提取payload
    if (packet->length > 0)
    {
        memcpy(packet->payload, &buffer[2], packet->length);
    }

    packet->checksum = buffer[buffer_len - 1];

    return true;
}

// ============================================================================
// 发送数据包创建
// ============================================================================

/**
 * 创建高频飞行数据包
 */
uint16_t packet_createHighFreqData(uint8_t *buffer, uint16_t buffer_size,
                                   const HighFreqDataPacket_t *hf_data)
{
    if (hf_data == NULL)
    {
        return 0;
    }

    PacketFrame_t packet;
    if (!packet_pack(&packet, PKT_ID_HIGH_FREQ_DATA,
                     (const uint8_t *)hf_data, sizeof(HighFreqDataPacket_t)))
    {
        return 0;
    }

    return packet_serialize(&packet, buffer, buffer_size);
}

/**
 * 创建电池状态包
 */
uint16_t packet_createBatteryStatus(uint8_t *buffer, uint16_t buffer_size,
                                    const BatteryStatusPacket_t *battery)
{
    if (battery == NULL)
    {
        return 0;
    }

    PacketFrame_t packet;
    if (!packet_pack(&packet, PKT_ID_BATTERY_STATUS,
                     (const uint8_t *)battery, sizeof(BatteryStatusPacket_t)))
    {
        return 0;
    }

    return packet_serialize(&packet, buffer, buffer_size);
}

/**
 * 创建PID参数响应包
 */
uint16_t packet_createPIDResponse(uint8_t *buffer, uint16_t buffer_size,
                                  const PIDConfigPacket_t *pid_config)
{
    if (pid_config == NULL)
    {
        return 0;
    }

    PacketFrame_t packet;
    if (!packet_pack(&packet, PKT_ID_PID_RESPONSE,
                     (const uint8_t *)pid_config, sizeof(PIDConfigPacket_t)))
    {
        return 0;
    }

    return packet_serialize(&packet, buffer, buffer_size);
}

// ============================================================================
// 接收数据包处理
// ============================================================================

/**
 * 解析飞行控制命令包
 */
bool packet_parseFlightControl(const PacketFrame_t *packet, FlightControlPacket_t *fc_packet)
{
    if (packet == NULL || fc_packet == NULL)
    {
        return false;
    }

    if (packet->packet_id != PKT_ID_FLIGHT_CONTROL)
    {
        return false;
    }

    if (packet->length != sizeof(FlightControlPacket_t))
    {
        return false;
    }

    memcpy(fc_packet, packet->payload, sizeof(FlightControlPacket_t));
    return true;
}

/**
 * 解析PID配置包
 */
bool packet_parsePIDConfig(const PacketFrame_t *packet, PIDConfigPacket_t *pid_config)
{
    if (packet == NULL || pid_config == NULL)
    {
        return false;
    }

    if (packet->packet_id != PKT_ID_PID_CONFIG)
    {
        return false;
    }

    if (packet->length != sizeof(PIDConfigPacket_t))
    {
        return false;
    }

    memcpy(pid_config, packet->payload, sizeof(PIDConfigPacket_t));
    return true;
}

/**
 * 解析电机测试包
 */
bool packet_parseMotorTest(const PacketFrame_t *packet, MotorTestPacket_t *motor_test)
{
    if (packet == NULL || motor_test == NULL)
    {
        return false;
    }

    if (packet->packet_id != PKT_ID_MOTOR_TEST)
    {
        return false;
    }

    if (packet->length != sizeof(MotorTestPacket_t))
    {
        return false;
    }

    memcpy(motor_test, packet->payload, sizeof(MotorTestPacket_t));
    return true;
}
