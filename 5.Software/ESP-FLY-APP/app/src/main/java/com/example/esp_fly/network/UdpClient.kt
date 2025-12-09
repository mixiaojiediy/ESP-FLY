package com.example.esp_fly.network

import android.util.Log
import com.example.esp_fly.protocol.BatteryInfo
import com.example.esp_fly.protocol.CrtpPacket
import com.example.esp_fly.protocol.CrtpPort
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
        const val DEFAULT_LOCAL_PORT = 2399
        private const val RECEIVE_BUFFER_SIZE = 1024
        private const val SEND_TIMEOUT_MS = 1000
    }

    // 连接状态
    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    // 电池信息流
    private val _batteryInfo = MutableSharedFlow<BatteryInfo>(replay = 1)
    val batteryInfo: SharedFlow<BatteryInfo> = _batteryInfo

    // 控制台消息流
    private val _consoleMessage = MutableSharedFlow<String>(replay = 10)
    val consoleMessage: SharedFlow<String> = _consoleMessage

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
                // 创建Socket
                socket = DatagramSocket(null).apply {
                    reuseAddress = true
                    soTimeout = SEND_TIMEOUT_MS
                    bind(InetSocketAddress(localPort))
                }
                deviceAddress = InetAddress.getByName(deviceIp)

                Log.d(TAG, "Socket created, local port: $localPort")

                // 启动接收线程
                startReceiveThread()
                // 启动发送线程
                startSendThread()

                // 发送初始化空包
                sendQueue.offer(CrtpPacket.createNullPacket())

                _isConnected.value = true
                _connectionMessage.emit("已连接到 $deviceIp:$devicePort")
                Log.i(TAG, "Connected to $deviceIp:$devicePort")
                true
            } catch (e: Exception) {
                Log.e(TAG, "Connect failed: ${e.message}")
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
        Log.d(TAG, "Disconnecting...")
        
        sendJob?.cancel()
        receiveJob?.cancel()
        sendJob = null
        receiveJob = null

        socket?.close()
        socket = null
        deviceAddress = null

        sendQueue.clear()
        _isConnected.value = false

        scope.launch {
            _connectionMessage.emit("已断开连接")
        }
        Log.i(TAG, "Disconnected")
    }

    /**
     * 发送数据包
     */
    fun sendPacket(data: ByteArray): Boolean {
        if (!_isConnected.value) {
            Log.w(TAG, "Not connected, cannot send packet")
            return false
        }
        return sendQueue.offer(data)
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
                    socket?.let { sock ->
                        deviceAddress?.let { addr ->
                            val packet = DatagramPacket(data, data.size, addr, devicePort)
                            sock.send(packet)
                            Log.v(TAG, "Sent ${data.size} bytes: ${data.toHexString()}")
                        }
                    }
                } catch (e: InterruptedException) {
                    break
                } catch (e: Exception) {
                    Log.e(TAG, "Send error: ${e.message}")
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
            Log.d(TAG, "Receive thread started")
            val buffer = ByteArray(RECEIVE_BUFFER_SIZE)
            val udpPacket = DatagramPacket(buffer, buffer.size)

            while (isActive && _isConnected.value) {
                try {
                    socket?.receive(udpPacket)
                    val receivedData = buffer.copyOfRange(0, udpPacket.length)
                    Log.v(TAG, "Received ${receivedData.size} bytes: ${receivedData.toHexString()}")
                    
                    // 解析CRTP包
                    processReceivedData(receivedData)
                } catch (e: java.net.SocketTimeoutException) {
                    // 超时正常，继续等待
                } catch (e: Exception) {
                    if (_isConnected.value) {
                        Log.e(TAG, "Receive error: ${e.message}")
                    }
                }
            }
            Log.d(TAG, "Receive thread stopped")
        }
    }

    /**
     * 处理接收到的数据
     */
    private suspend fun processReceivedData(data: ByteArray) {
        val packet = CrtpPacket.fromByteArray(data)
        if (packet == null) {
            Log.w(TAG, "Invalid packet received (checksum failed)")
            return
        }

        when (packet.port) {
            CrtpPort.PLATFORM -> {
                // 电池信息包
                val batteryData = CrtpPacket.parseBatteryInfo(packet.payload)
                if (batteryData != null) {
                    Log.d(TAG, "Battery: ${batteryData.level}%, ${batteryData.voltage}V")
                    _batteryInfo.emit(batteryData)
                }
            }
            CrtpPort.CONSOLE -> {
                // 控制台消息
                val message = CrtpPacket.parseConsoleMessage(packet.payload)
                if (message.isNotEmpty()) {
                    Log.d(TAG, "Console: $message")
                    _consoleMessage.emit(message)
                }
            }
            else -> {
                Log.v(TAG, "Received packet port=${packet.port}, channel=${packet.channel}")
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

