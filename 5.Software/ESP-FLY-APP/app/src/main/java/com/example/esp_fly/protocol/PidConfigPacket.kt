package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * PID配置数据包 (PacketID = 0x02)
 *
 * 双环 PID 控制：角度环（外环）+ 角速度环（内环）
 * 3轴 × 2环 × 3参数 = 18个float = 72字节
 *
 * Payload结构 (72 bytes):
 * 偏移  0~35: 角度环 Roll/Pitch/Yaw 各 kp,ki,kd
 * 偏移 36~71: 角速度环 Roll/Pitch/Yaw 各 kp,ki,kd
 */
object PidConfigPacket {

    const val PACKET_ID = 0x02
    const val PAYLOAD_SIZE = 72  // 18 * 4 bytes

    /**
     * 创建双环PID配置数据包
     */
    fun createPacket(
        // 角度环 (Angle Loop)
        rollAngleKp: Float,
        rollAngleKi: Float,
        rollAngleKd: Float,
        pitchAngleKp: Float,
        pitchAngleKi: Float,
        pitchAngleKd: Float,
        yawAngleKp: Float,
        yawAngleKi: Float,
        yawAngleKd: Float,
        // 角速度环 (Rate Loop)
        rollRateKp: Float,
        rollRateKi: Float,
        rollRateKd: Float,
        pitchRateKp: Float,
        pitchRateKi: Float,
        pitchRateKd: Float,
        yawRateKp: Float,
        yawRateKi: Float,
        yawRateKd: Float
    ): ByteArray {
        val payload = ByteBuffer.allocate(PAYLOAD_SIZE).order(ByteOrder.LITTLE_ENDIAN)

        // 角度环
        payload.putFloat(rollAngleKp)
        payload.putFloat(rollAngleKi)
        payload.putFloat(rollAngleKd)
        payload.putFloat(pitchAngleKp)
        payload.putFloat(pitchAngleKi)
        payload.putFloat(pitchAngleKd)
        payload.putFloat(yawAngleKp)
        payload.putFloat(yawAngleKi)
        payload.putFloat(yawAngleKd)

        // 角速度环
        payload.putFloat(rollRateKp)
        payload.putFloat(rollRateKi)
        payload.putFloat(rollRateKd)
        payload.putFloat(pitchRateKp)
        payload.putFloat(pitchRateKi)
        payload.putFloat(pitchRateKd)
        payload.putFloat(yawRateKp)
        payload.putFloat(yawRateKi)
        payload.putFloat(yawRateKd)

        return SimplePacket.encode(PACKET_ID, payload.array())
    }
}
