package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * CRTP协议端口定义
 */
object CrtpPort {
    const val CONSOLE = 0x00        // 控制台输出
    const val PARAM = 0x02          // 参数访问
    const val COMMANDER = 0x03      // 控制命令
    const val MEM = 0x04            // 内存访问
    const val LOG = 0x05            // 日志数据
    const val LOCALIZATION = 0x06   // 定位数据
    const val SETPOINT_GENERIC = 0x07
    const val SETPOINT_HL = 0x08
    const val PLATFORM = 0x0D       // 平台相关(电池信息)
    const val LINK = 0x0F           // 链路控制
}

/**
 * 电池状态定义
 */
object BatteryState {
    const val BATTERY = 0       // 正常使用
    const val CHARGING = 1      // 充电中
    const val CHARGED = 2       // 已充满
    const val LOW_POWER = 3     // 低电量
    const val SHUTDOWN = 4      // 关机
}

/**
 * 电池信息数据类
 */
data class BatteryInfo(
    val voltage: Float,         // 电压(V)
    val voltageMv: Int,         // 电压(mV)
    val level: Int,             // 电量百分比(0-100)
    val state: Int              // 电池状态
)

/**
 * CRTP数据包类
 * 
 * 数据包格式:
 * +----------+-------------------+----------+
 * |  Header  |      Payload      | Checksum |
 * |  1 byte  |    0-30 bytes     |  1 byte  |
 * +----------+-------------------+----------+
 */
class CrtpPacket(
    val port: Int,
    val channel: Int = 0,
    val payload: ByteArray = ByteArray(0)
) {
    /**
     * 获取CRTP头部字节
     */
    val header: Byte
        get() = ((port and 0x0F) shl 4 or (channel and 0x03)).toByte()

    /**
     * 计算校验和
     */
    private fun calculateChecksum(data: ByteArray): Byte {
        var sum = 0
        for (b in data) {
            sum += (b.toInt() and 0xFF)
        }
        return (sum and 0xFF).toByte()
    }

    /**
     * 打包为UDP发送的字节数组(包含校验和)
     */
    fun toByteArray(): ByteArray {
        val data = ByteArray(1 + payload.size)
        data[0] = header
        System.arraycopy(payload, 0, data, 1, payload.size)
        
        val checksum = calculateChecksum(data)
        val result = ByteArray(data.size + 1)
        System.arraycopy(data, 0, result, 0, data.size)
        result[result.size - 1] = checksum
        
        return result
    }

    companion object {
        /**
         * 创建空包(用于保持连接)
         */
        fun createNullPacket(): ByteArray {
            return byteArrayOf(0xFF.toByte(), 0xFF.toByte())
        }

        /**
         * 从接收的字节数组解析CRTP包
         * @return 解析成功返回CrtpPacket，校验失败返回null
         */
        fun fromByteArray(data: ByteArray): CrtpPacket? {
            if (data.size < 2) return null

            // 验证校验和
            val payloadWithHeader = data.copyOfRange(0, data.size - 1)
            val receivedChecksum = data[data.size - 1]
            var calculatedSum = 0
            for (b in payloadWithHeader) {
                calculatedSum += (b.toInt() and 0xFF)
            }
            if ((calculatedSum and 0xFF).toByte() != receivedChecksum) {
                return null // 校验和不匹配
            }

            val header = data[0].toInt() and 0xFF
            val port = (header shr 4) and 0x0F
            val channel = header and 0x03
            val payload = if (data.size > 2) {
                data.copyOfRange(1, data.size - 1)
            } else {
                ByteArray(0)
            }

            return CrtpPacket(port, channel, payload)
        }

        /**
         * 解析电池信息包
         */
        fun parseBatteryInfo(payload: ByteArray): BatteryInfo? {
            if (payload.size < 8) return null

            val buffer = ByteBuffer.wrap(payload).order(ByteOrder.LITTLE_ENDIAN)
            val voltage = buffer.float          // 4 bytes
            val voltageMv = buffer.short.toInt() and 0xFFFF  // 2 bytes
            val level = buffer.get().toInt() and 0xFF        // 1 byte
            val state = buffer.get().toInt() and 0xFF        // 1 byte

            return BatteryInfo(voltage, voltageMv, level, state)
        }

        /**
         * 解析控制台消息
         */
        fun parseConsoleMessage(payload: ByteArray): String {
            return String(payload, Charsets.UTF_8).trim('\u0000')
        }
    }
}

