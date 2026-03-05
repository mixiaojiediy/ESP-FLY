package com.example.esp_fly.viewmodel

import android.app.Application
import android.content.Context
import android.util.Log
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.esp_fly.network.UdpClient
import com.example.esp_fly.protocol.BatteryPacket
import com.example.esp_fly.protocol.Commander
import com.example.esp_fly.protocol.PidConfigPacket
import com.example.esp_fly.protocol.PidResponsePacket
import com.example.esp_fly.ui.components.JoystickPosition
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlin.math.abs

// DataStore 扩展
private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "drone_settings")

/**
 * PID参数数据类
 */
data class PidParams(
    val kp: Float = 0f,
    val ki: Float = 0f,
    val kd: Float = 0f
)

/**
 * PID设置状态（单级PID，仅角度环）
 * 默认值与 ESP-FLY 固件 pid.h 中的定义保持一致
 */
data class PidSettings(
    // 角度环 (Angle) - Roll/Pitch/Yaw
    val angleRoll: PidParams = PidParams(5.9f, 2.9f, 0f),
    val anglePitch: PidParams = PidParams(5.9f, 2.9f, 0f),
    val angleYaw: PidParams = PidParams(6f, 1f, 0.35f)
)

/**
 * 飞行数据状态
 */
data class FlightData(
    val roll: Float = 0f,
    val pitch: Float = 0f,
    val yaw: Float = 0f,
    val thrust: Int = 0
)

/**
 * UI状态
 */
data class DroneUiState(
    val isConnected: Boolean = false,
    val batteryVoltage: Float = 0f,
    val flightData: FlightData = FlightData(),
    val consoleMessages: List<String> = emptyList(),
    val connectionMessage: String = "",
    val pidSettings: PidSettings = PidSettings()
)

/**
 * 无人机控制ViewModel
 */
class DroneViewModel(application: Application) : AndroidViewModel(application) {

    companion object {
        private const val TAG = "DroneViewModel"
        private const val CONTROL_FREQUENCY_MS = 20L  // 50Hz
        private const val MAX_CONSOLE_MESSAGES = 100
        private const val CONSOLE_PRINT_INTERVAL_MS = 1000L  // 1Hz (每秒打印一次)
        
        // DataStore Keys（角度环 9个参数）
        private val KEY_ANGLE_ROLL_KP = floatPreferencesKey("angle_roll_kp")
        private val KEY_ANGLE_ROLL_KI = floatPreferencesKey("angle_roll_ki")
        private val KEY_ANGLE_ROLL_KD = floatPreferencesKey("angle_roll_kd")
        private val KEY_ANGLE_PITCH_KP = floatPreferencesKey("angle_pitch_kp")
        private val KEY_ANGLE_PITCH_KI = floatPreferencesKey("angle_pitch_ki")
        private val KEY_ANGLE_PITCH_KD = floatPreferencesKey("angle_pitch_kd")
        private val KEY_ANGLE_YAW_KP = floatPreferencesKey("angle_yaw_kp")
        private val KEY_ANGLE_YAW_KI = floatPreferencesKey("angle_yaw_ki")
        private val KEY_ANGLE_YAW_KD = floatPreferencesKey("angle_yaw_kd")
    }

    private val dataStore = application.dataStore
    private val udpClient = UdpClient()

    // UI状态
    private val _uiState = MutableStateFlow(DroneUiState())
    val uiState: StateFlow<DroneUiState> = _uiState.asStateFlow()

    // 控制命令发送任务
    private var controlJob: Job? = null
    
    // 控制台打印任务
    private var consolePrintJob: Job? = null
    
    // 当前摇杆位置
    private var leftJoystickY: Float = 0f   // 油门
    private var rightJoystickX: Float = 0f  // 映射到 pitch (左负右正)
    private var rightJoystickY: Float = 0f  // 映射到 roll (上负下正)

    // 当前油门值(保持)
    private var currentThrust: Int = 0
    
    // 触摸状态追踪
    private var isLeftJoystickTouching: Boolean = false
    private var isRightJoystickTouching: Boolean = false
    private var needSendZeroCommand: Boolean = false
    
    // 最后收到的PID参数
    private var lastPidResponse: PidResponsePacket.PidResponseData? = null

    init {
        // 监听连接状态
        viewModelScope.launch {
            udpClient.isConnected.collect { connected ->
                _uiState.update { it.copy(isConnected = connected) }
            }
        }

        // 监听电池信息
        viewModelScope.launch {
            udpClient.batteryInfo.collect { battery ->
                _uiState.update { 
                    it.copy(batteryVoltage = battery.voltage)
                }
            }
        }

        // 监听PID参数响应
        viewModelScope.launch {
            udpClient.pidResponse.collect { pidData ->
                lastPidResponse = pidData
            }
        }

        // 监听连接消息
        viewModelScope.launch {
            udpClient.connectionMessage.collect { message ->
                _uiState.update { it.copy(connectionMessage = message) }
            }
        }

        // 加载PID设置
        loadPidSettings()
    }

    /**
     * 连接/断开设备
     */
    fun toggleConnection() {
        Log.i(TAG, "========== toggleConnection called ==========")
        Log.i(TAG, "Current connection state: ${_uiState.value.isConnected}")
        viewModelScope.launch {
            if (_uiState.value.isConnected) {
                Log.i(TAG, "Disconnecting...")
                disconnect()
            } else {
                Log.i(TAG, "Connecting...")
                connect()
            }
        }
    }

    /**
     * 连接设备
     */
    private suspend fun connect() {
        Log.i(TAG, "========== DroneViewModel.connect() called ==========")
        val success = udpClient.connect()
        Log.i(TAG, "UDP client connect result: $success")
        if (success) {
            Log.i(TAG, "Starting control loop and console print loop...")
            startControlLoop()
            startConsolePrintLoop()
            Log.i(TAG, "Connection setup complete")
        } else {
            Log.e(TAG, "Connection failed!")
        }
        Log.i(TAG, "=====================================================")
    }

    /**
     * 断开连接
     */
    private fun disconnect() {
        stopControlLoop()
        stopConsolePrintLoop()
        udpClient.disconnect()
    }

    /**
     * 更新左摇杆位置(油门)
     * 油门模式：中心=0%，向上=0~100%，向下忽略
     */
    fun updateLeftJoystick(position: JoystickPosition) {
        leftJoystickY = position.y
        
        // position.y: 0~1 (中心为0，向上最大为1)
        // 映射到 0~60000
        currentThrust = (position.y * Commander.THRUST_MAX).toInt()
        
        updateFlightData()
    }

    /**
     * 更新右摇杆位置(Pitch/Roll)
     */
    fun updateRightJoystick(position: JoystickPosition) {
        rightJoystickX = position.x
        rightJoystickY = position.y
        
        updateFlightData()
    }

    /**
     * 更新左摇杆触摸状态
     */
    fun updateLeftJoystickTouchState(isTouching: Boolean) {
        val wasAnyTouching = isLeftJoystickTouching || isRightJoystickTouching
        isLeftJoystickTouching = isTouching
        val isAnyTouching = isLeftJoystickTouching || isRightJoystickTouching
        
        // 从"有触摸"变为"无触摸"时，标记需要发送归零命令
        if (wasAnyTouching && !isAnyTouching) {
            needSendZeroCommand = true
        }
    }

    /**
     * 更新右摇杆触摸状态
     */
    fun updateRightJoystickTouchState(isTouching: Boolean) {
        val wasAnyTouching = isLeftJoystickTouching || isRightJoystickTouching
        isRightJoystickTouching = isTouching
        val isAnyTouching = isLeftJoystickTouching || isRightJoystickTouching
        
        // 从"有触摸"变为"无触摸"时，标记需要发送归零命令
        if (wasAnyTouching && !isAnyTouching) {
            needSendZeroCommand = true
        }
    }

    /**
     * 更新飞行数据显示
     * 右摇杆映射: 左=pitch负, 右=pitch正, 上=roll负, 下=roll正
     */
    private fun updateFlightData() {
        val roll = -rightJoystickY * Commander.MAX_ANGLE   // 上=负, 下=正
        val pitch = rightJoystickX * Commander.MAX_ANGLE   // 左=负, 右=正
        
        _uiState.update {
            it.copy(
                flightData = FlightData(
                    roll = roll,
                    pitch = pitch,
                    yaw = 0f,
                    thrust = currentThrust
                )
            )
        }
    }

    /**
     * 启动控制命令发送循环
     */
    private fun startControlLoop() {
        controlJob?.cancel()
        controlJob = viewModelScope.launch(Dispatchers.IO) {
            while (isActive && _uiState.value.isConnected) {
                sendControlCommand()
                delay(CONTROL_FREQUENCY_MS)
            }
        }
    }

    /**
     * 停止控制命令发送循环
     */
    private fun stopControlLoop() {
        controlJob?.cancel()
        controlJob = null
    }

    /**
     * 发送控制命令
     * 检测触摸状态变化，在松开手指时发送归零命令
     */
    private fun sendControlCommand() {
        // 检查是否需要发送归零命令（双手都松开时）
        if (needSendZeroCommand) {
            // 发送全0命令，让飞机停止
            val zeroPacket = Commander.createCommandPacket(0f, 0f, 0f, 0)
            udpClient.sendPacket(zeroPacket)
            Log.d(TAG, "发送归零命令: Roll=0, Pitch=0, Yaw=0, Thrust=0")
            
            // 清除标志
            needSendZeroCommand = false
        }
        
        // 检查是否有摇杆在活动状态（阈值0.01避免浮点误差）
        val hasThrottle = leftJoystickY > 0.01f  // 油门有值
        val hasAttitude = abs(rightJoystickX) > 0.01f || abs(rightJoystickY) > 0.01f  // 姿态摇杆有值
        
        // 如果摇杆无输入，跳过发送
        if (!hasThrottle && !hasAttitude) {
            return
        }
        
        // 正常发送控制命令 (右摇杆: 左=pitch负, 右=pitch正, 上=roll负, 下=roll正)
        val roll = -rightJoystickY * Commander.MAX_ANGLE
        val pitch = rightJoystickX * Commander.MAX_ANGLE
        val yaw = 0f  // 暂不使用偏航控制
        
        val packet = Commander.createCommandPacket(roll, pitch, yaw, currentThrust)
        udpClient.sendPacket(packet)
        
        // 每秒打印一次控制命令（用于调试）
        if (System.currentTimeMillis() % 1000 < CONTROL_FREQUENCY_MS) {
            Log.d(TAG, "Control CMD: Roll=%.2f, Pitch=%.2f, Yaw=%.2f, Thrust=%d".format(roll, pitch, yaw, currentThrust))
        }
    }

    /**
     * 启动控制台打印循环 (1Hz)
     */
    private fun startConsolePrintLoop() {
        consolePrintJob?.cancel()
        consolePrintJob = viewModelScope.launch(Dispatchers.IO) {
            while (isActive && _uiState.value.isConnected) {
                printDataToConsole()
                delay(CONSOLE_PRINT_INTERVAL_MS)
            }
        }
    }

    /**
     * 停止控制台打印循环
     */
    private fun stopConsolePrintLoop() {
        consolePrintJob?.cancel()
        consolePrintJob = null
    }

    /**
     * 打印PID参数到控制台 (1秒一次)
     */
    private fun printDataToConsole() {
        val pidData = lastPidResponse
        if (pidData != null) {
            // 打印PID参数（简化格式）
            val pidLog = pidData.toCompactString()
            Log.d(TAG, pidLog)
            
            // 添加到UI控制台
            viewModelScope.launch(Dispatchers.Main) {
                _uiState.update { state ->
                    val newMessages = (state.consoleMessages + pidLog)
                        .takeLast(MAX_CONSOLE_MESSAGES)
                    state.copy(consoleMessages = newMessages)
                }
            }
        }
    }

    /**
     * 清空控制台日志
     */
    fun clearConsoleMessages() {
        _uiState.update { it.copy(consoleMessages = emptyList()) }
    }

    /**
     * 更新PID参数
     */
    fun updatePidSettings(settings: PidSettings) {
        _uiState.update { it.copy(pidSettings = settings) }
        savePidSettings(settings)
    }

    /**
     * 发送所有PID参数到设备（一次性发送，仅角度环9个参数）
     */
    fun sendAllPidToDevice() {
        val settings = _uiState.value.pidSettings
        viewModelScope.launch(Dispatchers.IO) {
            val packet = PidConfigPacket.createPacket(
                rollAngleKp = settings.angleRoll.kp,
                rollAngleKi = settings.angleRoll.ki,
                rollAngleKd = settings.angleRoll.kd,
                pitchAngleKp = settings.anglePitch.kp,
                pitchAngleKi = settings.anglePitch.ki,
                pitchAngleKd = settings.anglePitch.kd,
                yawAngleKp = settings.angleYaw.kp,
                yawAngleKi = settings.angleYaw.ki,
                yawAngleKd = settings.angleYaw.kd
            )
            udpClient.sendPacket(packet)
            
            Log.d(TAG, "PID参数已发送")
        }
    }

    /**
     * 保存PID设置到DataStore
     */
    private fun savePidSettings(settings: PidSettings) {
        viewModelScope.launch {
            dataStore.edit { prefs ->
                // 角度环
                prefs[KEY_ANGLE_ROLL_KP] = settings.angleRoll.kp
                prefs[KEY_ANGLE_ROLL_KI] = settings.angleRoll.ki
                prefs[KEY_ANGLE_ROLL_KD] = settings.angleRoll.kd
                prefs[KEY_ANGLE_PITCH_KP] = settings.anglePitch.kp
                prefs[KEY_ANGLE_PITCH_KI] = settings.anglePitch.ki
                prefs[KEY_ANGLE_PITCH_KD] = settings.anglePitch.kd
                prefs[KEY_ANGLE_YAW_KP] = settings.angleYaw.kp
                prefs[KEY_ANGLE_YAW_KI] = settings.angleYaw.ki
                prefs[KEY_ANGLE_YAW_KD] = settings.angleYaw.kd
            }
        }
    }

    /**
     * 从DataStore加载PID设置
     * 默认值与 ESP-FLY 固件 pid.h 中的定义保持一致
     */
    private fun loadPidSettings() {
        viewModelScope.launch {
            dataStore.data.collect { prefs ->
                val settings = PidSettings(
                    angleRoll = PidParams(
                        prefs[KEY_ANGLE_ROLL_KP] ?: 5.9f,
                        prefs[KEY_ANGLE_ROLL_KI] ?: 2.9f,
                        prefs[KEY_ANGLE_ROLL_KD] ?: 0f
                    ),
                    anglePitch = PidParams(
                        prefs[KEY_ANGLE_PITCH_KP] ?: 5.9f,
                        prefs[KEY_ANGLE_PITCH_KI] ?: 2.9f,
                        prefs[KEY_ANGLE_PITCH_KD] ?: 0f
                    ),
                    angleYaw = PidParams(
                        prefs[KEY_ANGLE_YAW_KP] ?: 6f,
                        prefs[KEY_ANGLE_YAW_KI] ?: 1f,
                        prefs[KEY_ANGLE_YAW_KD] ?: 0.35f
                    )
                )
                _uiState.update { it.copy(pidSettings = settings) }
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        stopControlLoop()
        udpClient.release()
    }
}
