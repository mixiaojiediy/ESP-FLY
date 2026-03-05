package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * PID参数响应包 (PacketID = 0x83)
 * 
 * 单级PID控制，仅角度环，3轴 × 3参数 = 9个float
 * 
 * Payload结构 (36 bytes):
 * - Roll:  kp, ki, kd (3个float, 12B)
 * - Pitch: kp, ki, kd (3个float, 12B)
 * - Yaw:   kp, ki, kd (3个float, 12B)
 */
object PidResponsePacket {
    
    const val PACKET_ID = 0x83
    const val PAYLOAD_SIZE = 36  // 9 * 4 bytes
    
    /**
     * PID参数响应数据类
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
        val yawAngleKd: Float
    ) {
        /**
         * 格式化为可读字符串（用于控制台打印）
         */
        fun toFormattedString(): String {
            return buildString {
                appendLine("[PID参数] 角度环:")
                appendLine("  Roll:  Kp=%.2f, Ki=%.2f, Kd=%.2f".format(rollAngleKp, rollAngleKi, rollAngleKd))
                appendLine("  Pitch: Kp=%.2f, Ki=%.2f, Kd=%.2f".format(pitchAngleKp, pitchAngleKi, pitchAngleKd))
                append("  Yaw:   Kp=%.2f, Ki=%.2f, Kd=%.2f".format(yawAngleKp, yawAngleKi, yawAngleKd))
            }
        }
        
        /**
         * 简化格式（多行显示）
         */
        fun toCompactString(): String {
            return String.format(
                "[PID] 角度环: \n      Roll (%6.1f,%6.1f,%6.1f) \n      Pitch(%6.1f,%6.1f,%6.1f) \n      Yaw  (%6.1f,%6.1f,%6.1f)",
                rollAngleKp, rollAngleKi, rollAngleKd,
                pitchAngleKp, pitchAngleKi, pitchAngleKd,
                yawAngleKp, yawAngleKi, yawAngleKd
            )
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
            
            // 解析角度环参数
            val rollAngleKp = buffer.float
            val rollAngleKi = buffer.float
            val rollAngleKd = buffer.float
            
            val pitchAngleKp = buffer.float
            val pitchAngleKi = buffer.float
            val pitchAngleKd = buffer.float
            
            val yawAngleKp = buffer.float
            val yawAngleKi = buffer.float
            val yawAngleKd = buffer.float

            PidResponseData(
                rollAngleKp = rollAngleKp,
                rollAngleKi = rollAngleKi,
                rollAngleKd = rollAngleKd,
                pitchAngleKp = pitchAngleKp,
                pitchAngleKi = pitchAngleKi,
                pitchAngleKd = pitchAngleKd,
                yawAngleKp = yawAngleKp,
                yawAngleKi = yawAngleKi,
                yawAngleKd = yawAngleKd
            )
        } catch (e: Exception) {
            null
        }
    }
}
