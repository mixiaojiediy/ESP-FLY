package com.example.esp_fly.viewmodel

import android.app.Application
import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.esp_fly.network.UdpClient
import com.example.esp_fly.protocol.BatteryInfo
import com.example.esp_fly.protocol.Commander
import com.example.esp_fly.protocol.ConfigCommander
import com.example.esp_fly.ui.components.JoystickPosition
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

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
 * PID设置状态
 * 默认值与 ESP-FLY 固件 pid.h 中的定义保持一致
 */
data class PidSettings(
    // 角速度环 (Rate) - 对应 PID_ROLL_RATE_KP/KI/KD 等
    val rateRoll: PidParams = PidParams(250f, 500f, 2.5f),
    val ratePitch: PidParams = PidParams(250f, 500f, 2.5f),
    val rateYaw: PidParams = PidParams(120f, 16.7f, 0f),
    // 姿态环 (Attitude) - 对应 PID_ROLL_KP/KI/KD 等
    val attitudeRoll: PidParams = PidParams(5.9f, 2.9f, 0f),
    val attitudePitch: PidParams = PidParams(5.9f, 2.9f, 0f),
    val attitudeYaw: PidParams = PidParams(6f, 1f, 0.35f)
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
    val batteryLevel: Int = 0,
    val batteryVoltage: Float = 0f,
    val batteryState: Int = 0,
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
        
        // DataStore Keys
        private val KEY_RATE_ROLL_KP = floatPreferencesKey("rate_roll_kp")
        private val KEY_RATE_ROLL_KI = floatPreferencesKey("rate_roll_ki")
        private val KEY_RATE_ROLL_KD = floatPreferencesKey("rate_roll_kd")
        private val KEY_RATE_PITCH_KP = floatPreferencesKey("rate_pitch_kp")
        private val KEY_RATE_PITCH_KI = floatPreferencesKey("rate_pitch_ki")
        private val KEY_RATE_PITCH_KD = floatPreferencesKey("rate_pitch_kd")
        private val KEY_RATE_YAW_KP = floatPreferencesKey("rate_yaw_kp")
        private val KEY_RATE_YAW_KI = floatPreferencesKey("rate_yaw_ki")
        private val KEY_RATE_YAW_KD = floatPreferencesKey("rate_yaw_kd")
        private val KEY_ATT_ROLL_KP = floatPreferencesKey("att_roll_kp")
        private val KEY_ATT_ROLL_KI = floatPreferencesKey("att_roll_ki")
        private val KEY_ATT_ROLL_KD = floatPreferencesKey("att_roll_kd")
        private val KEY_ATT_PITCH_KP = floatPreferencesKey("att_pitch_kp")
        private val KEY_ATT_PITCH_KI = floatPreferencesKey("att_pitch_ki")
        private val KEY_ATT_PITCH_KD = floatPreferencesKey("att_pitch_kd")
        private val KEY_ATT_YAW_KP = floatPreferencesKey("att_yaw_kp")
        private val KEY_ATT_YAW_KI = floatPreferencesKey("att_yaw_ki")
        private val KEY_ATT_YAW_KD = floatPreferencesKey("att_yaw_kd")
    }

    private val dataStore = application.dataStore
    private val udpClient = UdpClient()

    // UI状态
    private val _uiState = MutableStateFlow(DroneUiState())
    val uiState: StateFlow<DroneUiState> = _uiState.asStateFlow()

    // 控制命令发送任务
    private var controlJob: Job? = null
    
    // 当前摇杆位置
    private var leftJoystickY: Float = 0f   // 油门
    private var rightJoystickX: Float = 0f  // Roll
    private var rightJoystickY: Float = 0f  // Pitch

    // 当前油门值(保持)
    private var currentThrust: Int = 0

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
                    it.copy(
                        batteryLevel = battery.level,
                        batteryVoltage = battery.voltage,
                        batteryState = battery.state
                    )
                }
            }
        }

        // 监听控制台消息
        viewModelScope.launch {
            udpClient.consoleMessage.collect { message ->
                _uiState.update { state ->
                    val newMessages = (state.consoleMessages + message)
                        .takeLast(MAX_CONSOLE_MESSAGES)
                    state.copy(consoleMessages = newMessages)
                }
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
        viewModelScope.launch {
            if (_uiState.value.isConnected) {
                disconnect()
            } else {
                connect()
            }
        }
    }

    /**
     * 连接设备
     */
    private suspend fun connect() {
        val success = udpClient.connect()
        if (success) {
            startControlLoop()
        }
    }

    /**
     * 断开连接
     */
    private fun disconnect() {
        stopControlLoop()
        udpClient.disconnect()
    }

    /**
     * 紧急停止
     */
    fun emergencyStop() {
        currentThrust = 0
        leftJoystickY = 0f
        rightJoystickX = 0f
        rightJoystickY = 0f
        
        // 立即发送停止命令
        viewModelScope.launch(Dispatchers.IO) {
            repeat(3) {  // 发送多次确保收到
                udpClient.sendPacket(Commander.createStopPacket())
                delay(10)
            }
        }
        
        _uiState.update { 
            it.copy(flightData = FlightData())
        }
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
     * 更新飞行数据显示
     */
    private fun updateFlightData() {
        val roll = rightJoystickX * Commander.MAX_ANGLE
        val pitch = rightJoystickY * Commander.MAX_ANGLE
        
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
     */
    private fun sendControlCommand() {
        val roll = rightJoystickX * Commander.MAX_ANGLE
        val pitch = rightJoystickY * Commander.MAX_ANGLE
        val yaw = 0f  // 暂不使用偏航控制
        
        val packet = Commander.createCommandPacket(roll, pitch, yaw, currentThrust)
        udpClient.sendPacket(packet)
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
     * 发送PID参数到设备
     */
    fun sendPidToDevice(axis: Int, params: PidParams, isRateLoop: Boolean) {
        viewModelScope.launch(Dispatchers.IO) {
            val packet = ConfigCommander.createPidConfigPacket(
                axis = axis,
                kp = params.kp,
                ki = params.ki,
                kd = params.kd,
                isRateLoop = isRateLoop
            )
            udpClient.sendPacket(packet)
        }
    }

    /**
     * 发送所有PID参数到设备
     */
    fun sendAllPidToDevice() {
        val settings = _uiState.value.pidSettings
        viewModelScope.launch(Dispatchers.IO) {
            // 发送角速度环参数
            sendPidToDevice(ConfigCommander.AXIS_ROLL, settings.rateRoll, true)
            delay(50)
            sendPidToDevice(ConfigCommander.AXIS_PITCH, settings.ratePitch, true)
            delay(50)
            sendPidToDevice(ConfigCommander.AXIS_YAW, settings.rateYaw, true)
            delay(50)
            
            // 发送姿态环参数
            sendPidToDevice(ConfigCommander.AXIS_ROLL, settings.attitudeRoll, false)
            delay(50)
            sendPidToDevice(ConfigCommander.AXIS_PITCH, settings.attitudePitch, false)
            delay(50)
            sendPidToDevice(ConfigCommander.AXIS_YAW, settings.attitudeYaw, false)
        }
    }

    /**
     * 从设备读取当前PID参数
     * 发送查询命令后，设备会通过控制台返回PID参数
     */
    fun queryPidFromDevice() {
        viewModelScope.launch(Dispatchers.IO) {
            val packet = ConfigCommander.createPidQueryPacket()
            udpClient.sendPacket(packet)
        }
    }

    /**
     * 保存PID设置到DataStore
     */
    private fun savePidSettings(settings: PidSettings) {
        viewModelScope.launch {
            dataStore.edit { prefs ->
                // 角速度环
                prefs[KEY_RATE_ROLL_KP] = settings.rateRoll.kp
                prefs[KEY_RATE_ROLL_KI] = settings.rateRoll.ki
                prefs[KEY_RATE_ROLL_KD] = settings.rateRoll.kd
                prefs[KEY_RATE_PITCH_KP] = settings.ratePitch.kp
                prefs[KEY_RATE_PITCH_KI] = settings.ratePitch.ki
                prefs[KEY_RATE_PITCH_KD] = settings.ratePitch.kd
                prefs[KEY_RATE_YAW_KP] = settings.rateYaw.kp
                prefs[KEY_RATE_YAW_KI] = settings.rateYaw.ki
                prefs[KEY_RATE_YAW_KD] = settings.rateYaw.kd
                // 姿态环
                prefs[KEY_ATT_ROLL_KP] = settings.attitudeRoll.kp
                prefs[KEY_ATT_ROLL_KI] = settings.attitudeRoll.ki
                prefs[KEY_ATT_ROLL_KD] = settings.attitudeRoll.kd
                prefs[KEY_ATT_PITCH_KP] = settings.attitudePitch.kp
                prefs[KEY_ATT_PITCH_KI] = settings.attitudePitch.ki
                prefs[KEY_ATT_PITCH_KD] = settings.attitudePitch.kd
                prefs[KEY_ATT_YAW_KP] = settings.attitudeYaw.kp
                prefs[KEY_ATT_YAW_KI] = settings.attitudeYaw.ki
                prefs[KEY_ATT_YAW_KD] = settings.attitudeYaw.kd
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
                    rateRoll = PidParams(
                        prefs[KEY_RATE_ROLL_KP] ?: 250f,
                        prefs[KEY_RATE_ROLL_KI] ?: 500f,
                        prefs[KEY_RATE_ROLL_KD] ?: 2.5f
                    ),
                    ratePitch = PidParams(
                        prefs[KEY_RATE_PITCH_KP] ?: 250f,
                        prefs[KEY_RATE_PITCH_KI] ?: 500f,
                        prefs[KEY_RATE_PITCH_KD] ?: 2.5f
                    ),
                    rateYaw = PidParams(
                        prefs[KEY_RATE_YAW_KP] ?: 120f,
                        prefs[KEY_RATE_YAW_KI] ?: 16.7f,
                        prefs[KEY_RATE_YAW_KD] ?: 0f
                    ),
                    attitudeRoll = PidParams(
                        prefs[KEY_ATT_ROLL_KP] ?: 5.9f,
                        prefs[KEY_ATT_ROLL_KI] ?: 2.9f,
                        prefs[KEY_ATT_ROLL_KD] ?: 0f
                    ),
                    attitudePitch = PidParams(
                        prefs[KEY_ATT_PITCH_KP] ?: 5.9f,
                        prefs[KEY_ATT_PITCH_KI] ?: 2.9f,
                        prefs[KEY_ATT_PITCH_KD] ?: 0f
                    ),
                    attitudeYaw = PidParams(
                        prefs[KEY_ATT_YAW_KP] ?: 6f,
                        prefs[KEY_ATT_YAW_KI] ?: 1f,
                        prefs[KEY_ATT_YAW_KD] ?: 0.35f
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

