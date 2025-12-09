package com.example.esp_fly.protocol

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * 飞行控制命令生成器
 * 
 * 控制命令包格式 (Port=0x03, Channel=0x00):
 * +----------+-------+-------+-------+---------+----------+
 * |  Header  |  Roll | Pitch |  Yaw  | Thrust  | Checksum |
 * |  1 byte  |4 bytes|4 bytes|4 bytes| 2 bytes |  1 byte  |
 * +----------+-------+-------+-------+---------+----------+
 */
object Commander {
    
    // 控制参数限制
    const val MAX_ANGLE = 30.0f         // 最大倾斜角度(度)
    const val MIN_ANGLE = -30.0f        // 最小倾斜角度(度)
    const val MAX_YAW = 180.0f          // 最大偏航角速度(度/秒)
    const val MIN_YAW = -180.0f         // 最小偏航角速度(度/秒)
    const val THRUST_MIN = 0            // 最小推力
    const val THRUST_MAX = 60000        // 最大推力
    const val THRUST_HOVER = 35000      // 悬停推力

    /**
     * 创建控制命令数据包
     * 
     * @param roll 横滚角度 (-30 ~ +30 度)
     * @param pitch 俯仰角度 (-30 ~ +30 度), 注意: 发送时会取反
     * @param yaw 偏航角速度 (-180 ~ +180 度/秒)
     * @param thrust 推力值 (0 ~ 60000)
     * @return 完整的UDP数据包(包含校验和)
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
        val payload = ByteBuffer.allocate(14).order(ByteOrder.LITTLE_ENDIAN)
        payload.putFloat(clampedRoll)
        payload.putFloat(-clampedPitch)  // 注意: pitch取反
        payload.putFloat(clampedYaw)
        payload.putShort(clampedThrust.toShort())

        val packet = CrtpPacket(
            port = CrtpPort.COMMANDER,
            channel = 0,
            payload = payload.array()
        )

        return packet.toByteArray()
    }

    /**
     * 创建停止命令(推力为0)
     */
    fun createStopPacket(): ByteArray {
        return createCommandPacket(0f, 0f, 0f, 0)
    }

    /**
     * 创建悬停命令
     */
    fun createHoverPacket(thrust: Int = THRUST_HOVER): ByteArray {
        return createCommandPacket(0f, 0f, 0f, thrust)
    }
}

/**
 * 配置命令生成器
 * 
 * 配置命令包格式:
 * +--------+---------+-----------------+----------+
 * | 0xAA   | CmdType |      Data       | Checksum |
 * | 1 byte | 1 byte  |   0-62 bytes    |  1 byte  |
 * +--------+---------+-----------------+----------+
 */
object ConfigCommander {
    
    // 配置命令类型
    const val CMD_WIFI_SSID = 0x01
    const val CMD_WIFI_PASSWORD = 0x02
    const val CMD_FLIGHT_PARAMS = 0x03
    const val CMD_PID_PARAMS = 0x04
    const val CMD_DEVICE_NAME = 0x05
    const val CMD_GENERAL_CONFIG = 0x06
    const val CMD_PID_QUERY = 0x84   // PID参数查询 (0x04 | 0x80)
    const val CMD_TEST = 0xFF

    // PID轴定义
    const val AXIS_ROLL = 0
    const val AXIS_PITCH = 1
    const val AXIS_YAW = 2

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
     * 创建PID配置命令
     * 
     * @param axis 控制轴 (0:Roll, 1:Pitch, 2:Yaw)
     * @param kp 比例系数
     * @param ki 积分系数
     * @param kd 微分系数
     * @param isRateLoop true表示角速度环，false表示姿态环
     */
    fun createPidConfigPacket(
        axis: Int,
        kp: Float,
        ki: Float,
        kd: Float,
        isRateLoop: Boolean
    ): ByteArray {
        // 数据: axis(1) + kp(4) + ki(4) + kd(4) + isRate(1) = 14字节
        val payload = ByteBuffer.allocate(14).order(ByteOrder.LITTLE_ENDIAN)
        payload.put(axis.toByte())
        payload.putFloat(kp)
        payload.putFloat(ki)
        payload.putFloat(kd)
        payload.put(if (isRateLoop) 1.toByte() else 0.toByte())

        // 构造配置包: 0xAA + CMD_TYPE + DATA
        val dataWithoutChecksum = ByteArray(2 + payload.capacity())
        dataWithoutChecksum[0] = 0xAA.toByte()
        dataWithoutChecksum[1] = CMD_PID_PARAMS.toByte()
        System.arraycopy(payload.array(), 0, dataWithoutChecksum, 2, payload.capacity())

        // 添加校验和
        val checksum = calculateChecksum(dataWithoutChecksum)
        val result = ByteArray(dataWithoutChecksum.size + 1)
        System.arraycopy(dataWithoutChecksum, 0, result, 0, dataWithoutChecksum.size)
        result[result.size - 1] = checksum

        return result
    }

    /**
     * 创建PID参数查询命令
     * 发送此命令后，飞控会通过控制台返回所有PID参数
     */
    fun createPidQueryPacket(): ByteArray {
        val dataWithoutChecksum = ByteArray(2)
        dataWithoutChecksum[0] = 0xAA.toByte()
        dataWithoutChecksum[1] = CMD_PID_QUERY.toByte()

        val checksum = calculateChecksum(dataWithoutChecksum)
        val result = ByteArray(dataWithoutChecksum.size + 1)
        System.arraycopy(dataWithoutChecksum, 0, result, 0, dataWithoutChecksum.size)
        result[result.size - 1] = checksum

        return result
    }

    /**
     * 创建测试命令
     */
    fun createTestPacket(message: String): ByteArray {
        val msgBytes = message.toByteArray(Charsets.UTF_8)
        val dataWithoutChecksum = ByteArray(2 + msgBytes.size.coerceAtMost(62))
        dataWithoutChecksum[0] = 0xAA.toByte()
        dataWithoutChecksum[1] = CMD_TEST.toByte()
        System.arraycopy(msgBytes, 0, dataWithoutChecksum, 2, 
            msgBytes.size.coerceAtMost(62))

        val checksum = calculateChecksum(dataWithoutChecksum)
        val result = ByteArray(dataWithoutChecksum.size + 1)
        System.arraycopy(dataWithoutChecksum, 0, result, 0, dataWithoutChecksum.size)
        result[result.size - 1] = checksum

        return result
    }
}

