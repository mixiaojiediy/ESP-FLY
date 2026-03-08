package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * PID参数响应包 (PacketID = 0x83)
 *
 * 双环 PID 控制：角度环（外环）+ 角速度环（内环）
 * 3轴 × 2环 × 3参数 = 18个float = 72字节
 *
 * Payload结构 (72 bytes):
 * 偏移  0~35: 角度环 Roll/Pitch/Yaw 各 kp,ki,kd
 * 偏移 36~71: 角速度环 Roll/Pitch/Yaw 各 kp,ki,kd
 */
object PidResponsePacket {

    const val PACKET_ID = 0x83
    const val PAYLOAD_SIZE = 72  // 18 * 4 bytes

    /**
     * 双环PID参数响应数据类
     */
    data class PidResponseData(
        // 角度环 (Angle Loop)
        val rollAngleKp: Float,
        val rollAngleKi: Float,
        val rollAngleKd: Float,
        val pitchAngleKp: Float,
        val pitchAngleKi: Float,
        val pitchAngleKd: Float,
        val yawAngleKp: Float,
        val yawAngleKi: Float,
        val yawAngleKd: Float,
        // 角速度环 (Rate Loop)
        val rollRateKp: Float,
        val rollRateKi: Float,
        val rollRateKd: Float,
        val pitchRateKp: Float,
        val pitchRateKi: Float,
        val pitchRateKd: Float,
        val yawRateKp: Float,
        val yawRateKi: Float,
        val yawRateKd: Float
    ) {
        /**
         * 格式化为可读字符串（用于控制台打印）
         */
        fun toFormattedString(): String {
            return buildString {
                appendLine("[PID参数] 角度环 (外环):")
                appendLine("  Roll:  Kp=%.3f, Ki=%.3f, Kd=%.3f".format(rollAngleKp, rollAngleKi, rollAngleKd))
                appendLine("  Pitch: Kp=%.3f, Ki=%.3f, Kd=%.3f".format(pitchAngleKp, pitchAngleKi, pitchAngleKd))
                appendLine("  Yaw:   Kp=%.3f, Ki=%.3f, Kd=%.3f".format(yawAngleKp, yawAngleKi, yawAngleKd))
                appendLine("[PID参数] 角速度环 (内环):")
                appendLine("  Roll:  Kp=%.3f, Ki=%.3f, Kd=%.3f".format(rollRateKp, rollRateKi, rollRateKd))
                appendLine("  Pitch: Kp=%.3f, Ki=%.3f, Kd=%.3f".format(pitchRateKp, pitchRateKi, pitchRateKd))
                append("  Yaw:   Kp=%.3f, Ki=%.3f, Kd=%.3f".format(yawRateKp, yawRateKi, yawRateKd))
            }
        }

        /**
         * 结构化格式（控制台显示，每环独立分组）
         */
        fun toCompactString(): String {
            return buildString {
                appendLine("┌─ 角度环(外环) ─────────────────────")
                appendLine("│ Roll : Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(rollAngleKp, rollAngleKi, rollAngleKd))
                appendLine("│ Pitch: Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(pitchAngleKp, pitchAngleKi, pitchAngleKd))
                appendLine("│ Yaw  : Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(yawAngleKp, yawAngleKi, yawAngleKd))
                appendLine("├─ 角速度环(内环) ───────────────────")
                appendLine("│ Roll : Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(rollRateKp, rollRateKi, rollRateKd))
                appendLine("│ Pitch: Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(pitchRateKp, pitchRateKi, pitchRateKd))
                append("│ Yaw  : Kp=%-6.2f Ki=%-6.2f Kd=%-6.2f".format(yawRateKp, yawRateKi, yawRateKd))
            }
        }
    }

    /**
     * 解析PID参数响应包
     *
     * @param payload 数据包payload (不包含PacketID和Length)
     * @return 解析成功返回PidResponseData，失败返回null
     */
    fun parse(payload: ByteArray): PidResponseData? {
        if (payload.size < PAYLOAD_SIZE) return null

        return try {
            val buffer = ByteBuffer.wrap(payload).order(ByteOrder.LITTLE_ENDIAN)

            // 角度环
            val rollAngleKp = buffer.float
            val rollAngleKi = buffer.float
            val rollAngleKd = buffer.float
            val pitchAngleKp = buffer.float
            val pitchAngleKi = buffer.float
            val pitchAngleKd = buffer.float
            val yawAngleKp = buffer.float
            val yawAngleKi = buffer.float
            val yawAngleKd = buffer.float

            // 角速度环
            val rollRateKp = buffer.float
            val rollRateKi = buffer.float
            val rollRateKd = buffer.float
            val pitchRateKp = buffer.float
            val pitchRateKi = buffer.float
            val pitchRateKd = buffer.float
            val yawRateKp = buffer.float
            val yawRateKi = buffer.float
            val yawRateKd = buffer.float

            PidResponseData(
                rollAngleKp = rollAngleKp,
                rollAngleKi = rollAngleKi,
                rollAngleKd = rollAngleKd,
                pitchAngleKp = pitchAngleKp,
                pitchAngleKi = pitchAngleKi,
                pitchAngleKd = pitchAngleKd,
                yawAngleKp = yawAngleKp,
                yawAngleKi = yawAngleKi,
                yawAngleKd = yawAngleKd,
                rollRateKp = rollRateKp,
                rollRateKi = rollRateKi,
                rollRateKd = rollRateKd,
                pitchRateKp = pitchRateKp,
                pitchRateKi = pitchRateKi,
                pitchRateKd = pitchRateKd,
                yawRateKp = yawRateKp,
                yawRateKi = yawRateKi,
                yawRateKd = yawRateKd
            )
        } catch (e: Exception) {
            null
        }
    }
}
