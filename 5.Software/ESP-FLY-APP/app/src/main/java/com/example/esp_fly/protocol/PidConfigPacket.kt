package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * PID配置数据包 (PacketID = 0x02)
 * 
 * 单级PID控制，仅角度环，3轴 × 3参数 = 9个float
 * 
 * Payload结构 (36 bytes):
 * - Roll:  kp, ki, kd (3个float, 12B)
 * - Pitch: kp, ki, kd (3个float, 12B)
 * - Yaw:   kp, ki, kd (3个float, 12B)
 */
object PidConfigPacket {
    
    const val PACKET_ID = 0x02
    const val PAYLOAD_SIZE = 36  // 9 * 4 bytes

    /**
     * 创建PID配置数据包
     * 
     * 一次性发送3组角度环PID参数（Roll/Pitch/Yaw）
     * 
     * @return 完整数据包（已包含SimplePacket头部和校验和）
     */
    fun createPacket(
        rollAngleKp: Float,
        rollAngleKi: Float,
        rollAngleKd: Float,
        pitchAngleKp: Float,
        pitchAngleKi: Float,
        pitchAngleKd: Float,
        yawAngleKp: Float,
        yawAngleKi: Float,
        yawAngleKd: Float
    ): ByteArray {
        // 构造payload (36 bytes: 9个float)
        val payload = ByteBuffer.allocate(PAYLOAD_SIZE).order(ByteOrder.LITTLE_ENDIAN)
        
        // Roll角度环PID参数
        payload.putFloat(rollAngleKp)
        payload.putFloat(rollAngleKi)
        payload.putFloat(rollAngleKd)
        
        // Pitch角度环PID参数
        payload.putFloat(pitchAngleKp)
        payload.putFloat(pitchAngleKi)
        payload.putFloat(pitchAngleKd)
        
        // Yaw角度环PID参数
        payload.putFloat(yawAngleKp)
        payload.putFloat(yawAngleKi)
        payload.putFloat(yawAngleKd)

        // 使用SimplePacket编码
        return SimplePacket.encode(PACKET_ID, payload.array())
    }
}
