package com.example.esp_fly.network

import android.util.Log
import com.example.esp_fly.protocol.BatteryPacket
import com.example.esp_fly.protocol.PidResponsePacket
import com.example.esp_fly.protocol.SimplePacket
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.InetSocketAddress
import java.util.concurrent.LinkedBlockingQueue

/**
 * UDP通信客户端
 * 负责与ESP32设备进行UDP通信
 * 使用Simple Packet Protocol协议
 */
class UdpClient(
    private val deviceIp: String = DEFAULT_DEVICE_IP,
    private val devicePort: Int = DEFAULT_DEVICE_PORT,
    private val localPort: Int = DEFAULT_LOCAL_PORT
) {
    companion object {
        private const val TAG = "UdpClient"
        const val DEFAULT_DEVICE_IP = "192.168.43.42"
        const val DEFAULT_DEVICE_PORT = 2390
        const val DEFAULT_LOCAL_PORT = 2399  // 使用不同端口避免与设备端冲突
        private const val RECEIVE_BUFFER_SIZE = 1024
        private const val SEND_TIMEOUT_MS = 1000
    }

    // 连接状态
    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    // 电池信息流
    private val _batteryInfo = MutableSharedFlow<BatteryPacket.BatteryInfo>(replay = 1)
    val batteryInfo: SharedFlow<BatteryPacket.BatteryInfo> = _batteryInfo

    // PID参数响应流
    private val _pidResponse = MutableSharedFlow<PidResponsePacket.PidResponseData>(replay = 1)
    val pidResponse: SharedFlow<PidResponsePacket.PidResponseData> = _pidResponse

    // RPY角度数据流（来自0x81高频数据包，Triple: roll, pitch, yaw，单位：度）
    private val _rpyData = MutableSharedFlow<Triple<Float, Float, Float>>(replay = 1)
    val rpyData: SharedFlow<Triple<Float, Float, Float>> = _rpyData

    // 连接状态消息
    private val _connectionMessage = MutableSharedFlow<String>(replay = 1)
    val connectionMessage: SharedFlow<String> = _connectionMessage

    // 发送队列
    private val sendQueue = LinkedBlockingQueue<ByteArray>()

    // 网络相关
    private var socket: DatagramSocket? = null
    private var deviceAddress: InetAddress? = null
    private var sendJob: Job? = null
    private var receiveJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    /**
     * 连接到设备
     */
    suspend fun connect(): Boolean {
        if (_isConnected.value) {
            Log.w(TAG, "Already connected")
            return true
        }

        return withContext(Dispatchers.IO) {
            try {
                Log.i(TAG, "========== Starting connection ==========")
                Log.i(TAG, "Device IP: $deviceIp")
                Log.i(TAG, "Device Port: $devicePort")
                Log.i(TAG, "Local Port: $localPort")
                
                // 确保旧 Socket 完全关闭并释放端口
                if (socket != null) {
                    Log.i(TAG, "Cleaning up existing socket...")
                    disconnect()
                    // 等待操作系统释放端口（避免 TIME_WAIT 状态）
                    Thread.sleep(500)
                }
                
                // 创建 Socket - 明确绑定到 0.0.0.0 以接收 UDP 广播
                // 使用更健壮的方式处理端口绑定
                var bindSuccess = false
                var lastException: Exception? = null
                val maxRetries = 5
                
                for (attempt in 1..maxRetries) {
                    try {
                        Log.i(TAG, "Attempt $attempt/$maxRetries to bind to port $localPort...")
                        
                        val tempSocket = DatagramSocket(null)
                        // 关键：必须在 bind 之前设置这些选项
                        tempSocket.reuseAddress = true  // 允许地址重用
                        tempSocket.broadcast = true     // 允许接收广播包
                        
                        // 尝试绑定到指定端口
                        tempSocket.bind(InetSocketAddress("0.0.0.0", localPort))
                        
                        // 绑定成功后设置超时
                        tempSocket.soTimeout = SEND_TIMEOUT_MS
                        
                        socket = tempSocket
                        bindSuccess = true
                        Log.i(TAG, "Successfully bound to port $localPort on attempt $attempt")
                        break
                    } catch (e: java.net.BindException) {
                        lastException = e
                        Log.w(TAG, "Bind failed on attempt $attempt: ${e.message}")
                        if (attempt < maxRetries) {
                            // 递增等待时间，给系统更多时间释放端口
                            val waitTime = 300L * attempt
                            Log.i(TAG, "Waiting ${waitTime}ms before retry...")
                            Thread.sleep(waitTime)
                        }
                    } catch (e: Exception) {
                        lastException = e
                        Log.e(TAG, "Unexpected error on attempt $attempt: ${e.message}")
                        break
                    }
                }
                
                if (!bindSuccess) {
                    throw Exception("Failed to bind to port $localPort after $maxRetries attempts. ${lastException?.message}\n\n" +
                            "解决方案：\n" +
                            "1. 完全关闭 APP（从最近任务中滑掉）\n" +
                            "2. 等待 5 秒\n" +
                            "3. 重新打开 APP")
                }
                deviceAddress = InetAddress.getByName(deviceIp)

                val actualLocalPort = socket?.localPort ?: -1
                val actualLocalAddress = socket?.localAddress?.hostAddress ?: "unknown"
                
                Log.i(TAG, "========== Socket created successfully ==========")
                Log.i(TAG, "Socket bound to: $actualLocalAddress:$actualLocalPort (0.0.0.0 for broadcast)")
                Log.i(TAG, "Target device: $deviceIp:$devicePort")
                Log.i(TAG, "Socket isBound: ${socket?.isBound}")
                Log.i(TAG, "Socket isClosed: ${socket?.isClosed}")
                Log.i(TAG, "Socket broadcast enabled: ${socket?.broadcast}")
                Log.i(TAG, "Socket reuseAddress: ${socket?.reuseAddress}")
                Log.i(TAG, "================================================")
                Log.i(TAG, "Listening for UDP broadcasts on port $actualLocalPort")
                Log.i(TAG, "Device should broadcast to 255.255.255.255:$devicePort")
                
                // 验证端口绑定是否成功
                if (actualLocalPort != localPort) {
                    Log.e(TAG, "========== PORT BINDING FAILED ==========")
                    Log.e(TAG, "Requested port: $localPort")
                    Log.e(TAG, "Actual port: $actualLocalPort")
                    Log.e(TAG, "Port $localPort is likely already in use by another process")
                    Log.e(TAG, "Cannot receive broadcasts on wrong port!")
                    Log.e(TAG, "=========================================")
                    throw Exception("Failed to bind to port $localPort (got $actualLocalPort). Port may be in use.")
                }

                // 重要：必须先设置连接状态为 true，再启动接收线程
                // 否则接收线程会因为 _isConnected.value = false 而立即退出
                _isConnected.value = true
                
                // 启动接收线程
                Log.i(TAG, "Starting receive thread...")
                startReceiveThread()
                // 启动发送线程
                Log.i(TAG, "Starting send thread...")
                startSendThread()

                _connectionMessage.emit("已连接到 $deviceIp:$devicePort")
                Log.i(TAG, "========== Connection established ==========")
                Log.i(TAG, "Ready to receive packets on port $actualLocalPort")
                Log.i(TAG, "===========================================")
                true
            } catch (e: Exception) {
                Log.e(TAG, "========== CONNECTION FAILED ==========")
                Log.e(TAG, "Error: ${e.message}")
                Log.e(TAG, "Exception type: ${e.javaClass.simpleName}")
                e.printStackTrace()
                Log.e(TAG, "========================================")
                _connectionMessage.emit("连接失败: ${e.message}")
                disconnect()
                false
            }
        }
    }

    /**
     * 断开连接
     */
    fun disconnect() {
        Log.i(TAG, "========== Disconnecting ==========")
        
        sendJob?.cancel()
        receiveJob?.cancel()
        sendJob = null
        receiveJob = null

        // 确保Socket完全关闭
        socket?.let { s ->
            try {
                if (!s.isClosed) {
                    Log.i(TAG, "Closing socket...")
                    s.close()
                    // 等待Socket关闭
                    var waitCount = 0
                    while (!s.isClosed && waitCount < 10) {
                        Thread.sleep(50)
                        waitCount++
                    }
                    if (s.isClosed) {
                        Log.i(TAG, "Socket closed successfully")
                    } else {
                        Log.w(TAG, "Socket may still be closing, but continuing...")
                    }
                } else {
                    Log.i(TAG, "Socket was already closed")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Error closing socket: ${e.message}")
            }
        }
        socket = null
        deviceAddress = null

        sendQueue.clear()
        _isConnected.value = false

        scope.launch {
            _connectionMessage.emit("已断开连接")
        }
        Log.i(TAG, "========== Disconnected ==========")
    }

    /**
     * 发送数据包
     */
    fun sendPacket(data: ByteArray): Boolean {
        if (!_isConnected.value) {
            Log.w(TAG, "Not connected, cannot send packet")
            return false
        }
        val success = sendQueue.offer(data)
        if (!success) {
            Log.w(TAG, "Send queue is full, packet dropped")
        } else {
            Log.d(TAG, "Packet queued for send, queue size: ${sendQueue.size}, data: ${data.toHexString()}")
        }
        return success
    }

    /**
     * 启动发送线程
     */
    private fun startSendThread() {
        sendJob = scope.launch {
            Log.d(TAG, "Send thread started")
            while (isActive && _isConnected.value) {
                try {
                    val data = sendQueue.take()
                    if (socket == null) {
                        Log.e(TAG, "Socket is null, cannot send")
                        continue
                    }
                    if (deviceAddress == null) {
                        Log.e(TAG, "Device address is null, cannot send")
                        continue
                    }
                    val packet = DatagramPacket(data, data.size, deviceAddress, devicePort)
                    socket?.send(packet)
                    Log.d(TAG, "Sent ${data.size} bytes to $deviceIp:$devicePort: ${data.toHexString()}")
                } catch (e: InterruptedException) {
                    Log.d(TAG, "Send thread interrupted")
                    break
                } catch (e: Exception) {
                    Log.e(TAG, "Send error: ${e.message}", e)
                }
            }
            Log.d(TAG, "Send thread stopped")
        }
    }

    /**
     * 启动接收线程
     */
    private fun startReceiveThread() {
        receiveJob = scope.launch {
            Log.i(TAG, "========== Receive thread starting ==========")
            Log.i(TAG, "Socket: ${socket != null}")
            Log.i(TAG, "Socket isBound: ${socket?.isBound}")
            Log.i(TAG, "Socket isClosed: ${socket?.isClosed}")
            Log.i(TAG, "Local port: $localPort")
            Log.i(TAG, "Socket localPort: ${socket?.localPort}")
            Log.i(TAG, "Socket localAddress: ${socket?.localAddress?.hostAddress}")
            Log.i(TAG, "Target device: $deviceIp:$devicePort")
            Log.i(TAG, "isConnected state: ${_isConnected.value}")
            
            if (socket == null) {
                Log.e(TAG, "ERROR: Socket is null when starting receive thread!")
                return@launch
            }
            
            if (!socket!!.isBound) {
                Log.e(TAG, "ERROR: Socket is not bound!")
                return@launch
            }
            
            val buffer = ByteArray(RECEIVE_BUFFER_SIZE)
            val udpPacket = DatagramPacket(buffer, buffer.size)
            
            Log.i(TAG, "========== Starting to receive UDP packets ==========")
            var receiveCount = 0
            var lastLogTime = System.currentTimeMillis()
            
            while (isActive && _isConnected.value) {
                try {
                    // 每2秒打印一次等待日志
                    val currentTime = System.currentTimeMillis()
                    if (currentTime - lastLogTime > 2000) {
                        Log.i(TAG, "Waiting for UDP packet... (loop $receiveCount, socket bound: ${socket?.isBound}, connected: ${_isConnected.value})")
                        lastLogTime = currentTime
                    }
                    receiveCount++
                    
                    socket?.receive(udpPacket)
                    
                    val receivedData = buffer.copyOfRange(0, udpPacket.length)
                    val sourceIp = udpPacket.address.hostAddress
                    val sourcePort = udpPacket.port
                    
                    // 调试：打印接收到的数据包信息（无论IP是否匹配）
                    Log.i(TAG, "========== RECEIVED PACKET ==========")
                    Log.i(TAG, "Size: ${receivedData.size} bytes")
                    Log.i(TAG, "From: $sourceIp:$sourcePort")
                    Log.i(TAG, "Expected: $deviceIp:$devicePort")
                    Log.i(TAG, "Data: ${receivedData.toHexString()}")
                    Log.i(TAG, "=====================================")
                    
                    // 只接收来自目标设备IP的数据包
                    if (sourceIp != deviceIp) {
                        Log.w(TAG, "WARNING: Packet from $sourceIp (expected $deviceIp) - processing anyway for debugging")
                    }
                    
                    Log.d(TAG, "Processing packet from $sourceIp: ${receivedData.toHexString()}")
                    
                    // 解析数据包
                    processReceivedData(receivedData)
                } catch (e: java.net.SocketTimeoutException) {
                    // 超时正常，继续等待（如果设置了超时）
                    Log.v(TAG, "Receive timeout, continuing...")
                } catch (e: Exception) {
                    if (_isConnected.value) {
                        Log.e(TAG, "========== RECEIVE ERROR ==========")
                        Log.e(TAG, "Error message: ${e.message}")
                        Log.e(TAG, "Exception type: ${e.javaClass.simpleName}")
                        Log.e(TAG, "Socket isBound: ${socket?.isBound}")
                        Log.e(TAG, "Socket isClosed: ${socket?.isClosed}")
                        Log.e(TAG, "isConnected: ${_isConnected.value}")
                        e.printStackTrace()
                        Log.e(TAG, "===================================")
                    }
                }
            }
            Log.i(TAG, "========== Receive thread stopped ==========")
        }
    }

    /**
     * 处理接收到的数据（Simple Packet Protocol）
     */
    private suspend fun processReceivedData(data: ByteArray) {
        // 使用Simple Packet Protocol解析
        val packet = SimplePacket.decode(data)
        if (packet == null) {
            Log.w(TAG, "Invalid packet received (checksum failed or malformed)")
            return
        }

        when (packet.packetId) {
            0x81 -> {
                // 高频飞行数据包 (0x81, 50Hz) - 解析RPY角度（偏移0~11字节，3个float）
                val payload = packet.payload
                if (payload.size >= 12) {
                    val roll = java.nio.ByteBuffer.wrap(payload, 0, 4)
                        .order(java.nio.ByteOrder.LITTLE_ENDIAN).float
                    val pitch = java.nio.ByteBuffer.wrap(payload, 4, 4)
                        .order(java.nio.ByteOrder.LITTLE_ENDIAN).float
                    val yaw = java.nio.ByteBuffer.wrap(payload, 8, 4)
                        .order(java.nio.ByteOrder.LITTLE_ENDIAN).float
                    _rpyData.emit(Triple(roll, pitch, yaw))
                }
            }
            BatteryPacket.PACKET_ID -> {
                // 电池状态包 (0x82, 1Hz)
                val batteryData = BatteryPacket.parse(packet.payload)
                if (batteryData != null) {
                    Log.d(TAG, "Battery: ${batteryData.voltage}V")
                    _batteryInfo.emit(batteryData)
                } else {
                    Log.w(TAG, "Failed to parse battery packet")
                }
            }
            PidResponsePacket.PACKET_ID -> {
                // PID参数响应包 (0x83, on request)
                val pidData = PidResponsePacket.parse(packet.payload)
                if (pidData != null) {
                    Log.d(TAG, "PID Response received")
                    Log.v(TAG, pidData.toCompactString())
                    _pidResponse.emit(pidData)
                } else {
                    Log.w(TAG, "Failed to parse PID response packet")
                }
            }
            else -> {
                Log.v(TAG, "Received unknown packet: packetId=0x${packet.packetId.toString(16)}")
            }
        }
    }

    /**
     * 释放资源
     */
    fun release() {
        disconnect()
        scope.cancel()
    }

    /**
     * ByteArray转十六进制字符串(用于调试)
     */
    private fun ByteArray.toHexString(): String {
        return joinToString(" ") { String.format("%02X", it) }
    }
}

