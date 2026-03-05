package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * 电池状态数据包 (PacketID = 0x82)
 * 
 * Payload结构 (4 bytes):
 * +----------+
 * | Voltage  |
 * | 4 bytes  |
 * +----------+
 * 
 * 字段说明:
 * - voltage: 电池电压(伏特), float
 */
object BatteryPacket {
    
    const val PACKET_ID = 0x82
    const val PAYLOAD_SIZE = 4
    
    /**
     * 电池信息数据类
     */
    data class BatteryInfo(
        val voltage: Float         // 电压(V)
    ) {
        /**
         * 格式化为字符串
         */
        fun toFormattedString(): String {
            return String.format("[电池] 电压: %.2fV", voltage)
        }
    }

    /**
     * 解析电池状态包
     * 
     * @param payload 数据包payload (不包含PacketID和Length)
     * @return 解析成功返回BatteryInfo，失败返回null
     */
    fun parse(payload: ByteArray): BatteryInfo? {
        if (payload.size < PAYLOAD_SIZE) return null

        return try {
            val buffer = ByteBuffer.wrap(payload).order(ByteOrder.LITTLE_ENDIAN)
            val voltage = buffer.float  // 4 bytes

            BatteryInfo(voltage = voltage)
        } catch (e: Exception) {
            null
        }
    }
}
