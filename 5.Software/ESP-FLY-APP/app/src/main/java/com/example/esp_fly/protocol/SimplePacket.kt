package com.example.esp_fly.protocol

/**
 * Simple Packet Protocol 核心实现
 * 
 * 数据包格式:
 * +----------+----------+-------------------+----------+
 * | PacketID | Length   | Payload           | Checksum |
 * | 1 byte   | 1 byte   | 0-120 bytes       | 1 byte   |
 * +----------+----------+-------------------+----------+
 * 
 * 校验和计算: Checksum = (PacketID + Length + 所有Payload字节) & 0xFF
 */
object SimplePacket {
    
    const val MAX_PAYLOAD_SIZE = 120
    
    /**
     * 数据包类
     */
    data class Packet(
        val packetId: Int,
        val payload: ByteArray
    ) {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false

            other as Packet

            if (packetId != other.packetId) return false
            if (!payload.contentEquals(other.payload)) return false

            return true
        }

        override fun hashCode(): Int {
            var result = packetId
            result = 31 * result + payload.contentHashCode()
            return result
        }
    }

    /**
     * 编码数据包
     * 
     * @param packetId 数据包ID (0x00-0xFF)
     * @param payload 有效载荷 (最大120字节)
     * @return 完整数据包（包含校验和）
     * @throws IllegalArgumentException 如果payload太大
     */
    fun encode(packetId: Int, payload: ByteArray): ByteArray {
        val length = payload.size
        require(length <= MAX_PAYLOAD_SIZE) { "Payload too large: $length bytes (max: $MAX_PAYLOAD_SIZE)" }
        require(packetId in 0..0xFF) { "PacketID must be 0x00-0xFF" }

        // 构建数据包: PacketID + Length + Payload + Checksum
        val packet = ByteArray(2 + length + 1)
        packet[0] = packetId.toByte()
        packet[1] = length.toByte()
        System.arraycopy(payload, 0, packet, 2, length)

        // 计算校验和
        val checksum = calculateChecksum(packet, 0, 2 + length)
        packet[2 + length] = checksum

        return packet
    }

    /**
     * 解码数据包
     * 
     * @param data 原始数据
     * @return 解码后的数据包，格式错误或校验失败返回null
     */
    fun decode(data: ByteArray): Packet? {
        // 最小长度检查: PacketID(1) + Length(1) + Checksum(1) = 3 bytes
        if (data.size < 3) return null

        val packetId = data[0].toInt() and 0xFF
        val length = data[1].toInt() and 0xFF

        // 长度检查
        if (length > MAX_PAYLOAD_SIZE) return null
        if (data.size < 2 + length + 1) return null

        // 验证校验和
        val receivedChecksum = data[2 + length]
        val calculatedChecksum = calculateChecksum(data, 0, 2 + length)
        
        if (receivedChecksum != calculatedChecksum) {
            return null  // 校验和不匹配
        }

        // 提取payload
        val payload = if (length > 0) {
            data.copyOfRange(2, 2 + length)
        } else {
            ByteArray(0)
        }

        return Packet(packetId, payload)
    }

    /**
     * 计算校验和
     * 
     * 校验和 = (所有字节之和) & 0xFF
     * 
     * @param data 数据数组
     * @param offset 起始偏移
     * @param length 计算长度
     * @return 校验和字节
     */
    private fun calculateChecksum(data: ByteArray, offset: Int, length: Int): Byte {
        var sum = 0
        for (i in offset until offset + length) {
            sum += (data[i].toInt() and 0xFF)
        }
        return (sum and 0xFF).toByte()
    }
}
