package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * 飞行控制命令生成器 (PacketID = 0x01)
 * 
 * Payload结构 (14 bytes):
 * +-------+-------+-------+---------+
 * | Roll  | Pitch | Yaw   | Thrust  |
 * |4 bytes|4 bytes|4 bytes| 2 bytes |
 * +-------+-------+-------+---------+
 * 
 * 所有数据采用小端序（Little-Endian）
 */
object Commander {
    
    const val PACKET_ID = 0x01
    const val PAYLOAD_SIZE = 14
    
    // 控制参数限制
    const val MAX_ANGLE = 10.0f         // 最大倾斜角度(度)
    const val MIN_ANGLE = -10.0f        // 最小倾斜角度(度)
    const val MAX_YAW = 180.0f          // 最大偏航角速度(度/秒)
    const val MIN_YAW = -180.0f         // 最小偏航角速度(度/秒)
    const val THRUST_MIN = 0            // 最小推力
    const val THRUST_MAX = 60000        // 最大推力
    const val THRUST_HOVER = 35000      // 悬停推力

    /**
     * 创建控制命令数据包
     * 
     * @param roll 横滚角度 (-10 ~ +10 度)
     * @param pitch 俯仰角度 (-10 ~ +10 度), 注意: 发送时会取反
     * @param yaw 偏航角速度 (-180 ~ +180 度/秒)
     * @param thrust 推力值 (0 ~ 60000)
     * @return 完整的数据包（已包含SimplePacket头部和校验和）
     */
    fun createCommandPacket(
        roll: Float,
        pitch: Float,
        yaw: Float,
        thrust: Int
    ): ByteArray {
        // 限制参数范围
        val clampedRoll = roll.coerceIn(MIN_ANGLE, MAX_ANGLE)
        val clampedPitch = pitch.coerceIn(MIN_ANGLE, MAX_ANGLE)
        val clampedYaw = yaw.coerceIn(MIN_YAW, MAX_YAW)
        val clampedThrust = thrust.coerceIn(THRUST_MIN, THRUST_MAX)

        // 构造payload (14字节: 3个float + 1个uint16)
        val payload = ByteBuffer.allocate(PAYLOAD_SIZE).order(ByteOrder.LITTLE_ENDIAN)
        payload.putFloat(clampedRoll)
        payload.putFloat(-clampedPitch)  // 注意: pitch取反
        payload.putFloat(clampedYaw)
        payload.putShort(clampedThrust.toShort())

        // 使用SimplePacket编码
        return SimplePacket.encode(PACKET_ID, payload.array())
    }

    /**
     * 创建悬停命令
     */
    fun createHoverPacket(thrust: Int = THRUST_HOVER): ByteArray {
        return createCommandPacket(0f, 0f, 0f, thrust)
    }
}
