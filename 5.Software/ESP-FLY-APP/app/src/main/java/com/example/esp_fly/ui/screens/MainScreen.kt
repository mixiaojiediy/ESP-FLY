package com.example.esp_fly.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.esp_fly.ui.components.JoystickType
import com.example.esp_fly.ui.components.JoystickView
import com.example.esp_fly.viewmodel.DroneUiState

/**
 * 主控制界面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    uiState: DroneUiState,
    onConnectClick: () -> Unit,
    onSettingsClick: () -> Unit,
    onEmergencyStop: () -> Unit,
    onLeftJoystickChange: (com.example.esp_fly.ui.components.JoystickPosition) -> Unit,
    onRightJoystickChange: (com.example.esp_fly.ui.components.JoystickPosition) -> Unit,
    onClearConsole: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(colorScheme.background)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            // 顶部状态栏
            TopStatusBar(
                isConnected = uiState.isConnected,
                batteryLevel = uiState.batteryLevel,
                batteryVoltage = uiState.batteryVoltage,
                flightData = uiState.flightData,
                thrust = uiState.flightData.thrust,
                onConnectClick = onConnectClick,
                onSettingsClick = onSettingsClick
            )

            // 主体内容区
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 左摇杆 - 油门控制(仅上半区域有效，自动回中)
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "油门",
                        style = MaterialTheme.typography.labelMedium,
                        color = colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    JoystickView(
                        size = 180.dp,
                        type = JoystickType.THROTTLE,
                        onPositionChanged = onLeftJoystickChange
                    )
                }

                // 中间区域 - 调试日志 + 紧急停止
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .padding(horizontal = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // 调试日志区域
                    ConsoleLogArea(
                        messages = uiState.consoleMessages,
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxWidth(),
                        onClear = onClearConsole
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // 紧急停止按钮
                    EmergencyStopButton(
                        onClick = onEmergencyStop
                    )
                }

                // 右摇杆 - Pitch/Roll控制
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "姿态",
                        style = MaterialTheme.typography.labelMedium,
                        color = colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    JoystickView(
                        size = 180.dp,
                        type = JoystickType.FULL,
                        onPositionChanged = onRightJoystickChange
                    )
                }
            }
        }
    }
}

/**
 * 顶部状态栏
 */
@Composable
private fun TopStatusBar(
    isConnected: Boolean,
    batteryLevel: Int,
    batteryVoltage: Float,
    flightData: com.example.esp_fly.viewmodel.FlightData,
    thrust: Int,
    onConnectClick: () -> Unit,
    onSettingsClick: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme
    
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = colorScheme.surfaceVariant.copy(alpha = 0.8f),
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 左侧 - 飞行数据（油门 + 姿态）
            FlightDataDisplay(
                flightData = flightData,
                thrust = thrust
            )

            // 右侧 - 连接按钮 + 电池 + 设置按钮
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // 连接按钮（仅图标）
                IconButton(
                    onClick = onConnectClick,
                    modifier = Modifier
                        .background(
                            color = if (isConnected) 
                                colorScheme.primaryContainer 
                            else 
                                colorScheme.errorContainer,
                            shape = RoundedCornerShape(12.dp)
                        )
                        .size(40.dp)
                ) {
                    Icon(
                        imageVector = if (isConnected) Icons.Default.Wifi else Icons.Default.WifiOff,
                        contentDescription = if (isConnected) "已连接" else "未连接",
                        modifier = Modifier.size(20.dp),
                        tint = if (isConnected) 
                            colorScheme.onPrimaryContainer 
                        else 
                            colorScheme.onErrorContainer
                    )
                }

                // 电池信息
                BatteryIndicator(
                    level = batteryLevel,
                    voltage = batteryVoltage
                )

                // 设置按钮
                IconButton(onClick = onSettingsClick) {
                    Icon(
                        imageVector = Icons.Default.Settings,
                        contentDescription = "设置",
                        tint = colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

/**
 * 电池指示器
 */
@Composable
private fun BatteryIndicator(
    level: Int,
    voltage: Float
) {
    val colorScheme = MaterialTheme.colorScheme
    val batteryColor = when {
        level > 60 -> Color(0xFF4CAF50)  // 绿色
        level > 30 -> Color(0xFFFFC107)  // 黄色
        else -> Color(0xFFF44336)         // 红色
    }

    Row(
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = when {
                level > 80 -> Icons.Default.BatteryFull
                level > 50 -> Icons.Default.Battery5Bar
                level > 20 -> Icons.Default.Battery3Bar
                else -> Icons.Default.Battery1Bar
            },
            contentDescription = "电池",
            tint = batteryColor,
            modifier = Modifier.size(24.dp)
        )
        Spacer(modifier = Modifier.width(4.dp))
        Column {
            Text(
                text = "${level}%",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = batteryColor
            )
            Text(
                text = String.format("%.2fV", voltage),
                style = MaterialTheme.typography.labelSmall,
                color = colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * 飞行数据显示（油门 + 姿态）
 */
@Composable
private fun FlightDataDisplay(
    flightData: com.example.esp_fly.viewmodel.FlightData,
    thrust: Int
) {
    val colorScheme = MaterialTheme.colorScheme
    // 计算油门百分比 (thrust/65535*100)
    val throttlePercent = (thrust / 65535f * 100f).toInt()

    Surface(
        color = colorScheme.surface,
        shape = RoundedCornerShape(8.dp),
        tonalElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            ThrottleItem(throttlePercent)
            DataItem("R", flightData.roll, "°")
            DataItem("P", flightData.pitch, "°")
            DataItem("Y", flightData.yaw, "°")
        }
    }
}

/**
 * 油门数据项
 */
@Composable
private fun ThrottleItem(percent: Int) {
    val colorScheme = MaterialTheme.colorScheme
    
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            text = "T:",
            style = MaterialTheme.typography.labelSmall,
            color = colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(2.dp))
        Text(
            text = "${percent}%",
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace,
            color = colorScheme.primary
        )
    }
}

@Composable
private fun DataItem(label: String, value: Float, unit: String) {
    val colorScheme = MaterialTheme.colorScheme
    
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            text = "$label:",
            style = MaterialTheme.typography.labelSmall,
            color = colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.width(2.dp))
        Text(
            text = "${value.toInt()}$unit",
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace,
            color = colorScheme.primary
        )
    }
}

/**
 * 控制台日志区域
 */
@Composable
private fun ConsoleLogArea(
    messages: List<String>,
    modifier: Modifier = Modifier,
    onClear: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme
    val listState = rememberLazyListState()

    // 自动滚动到底部
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    Surface(
        modifier = modifier,
        color = colorScheme.surfaceContainerLowest,
        shape = RoundedCornerShape(12.dp),
        tonalElevation = 1.dp
    ) {
        Column {
            // 标题栏
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(colorScheme.surfaceContainerLow)
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.Terminal,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "控制台",
                        style = MaterialTheme.typography.labelMedium,
                        color = colorScheme.onSurfaceVariant
                    )
                }
                IconButton(
                    onClick = onClear,
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.DeleteOutline,
                        contentDescription = "清空",
                        modifier = Modifier.size(16.dp),
                        tint = colorScheme.onSurfaceVariant
                    )
                }
            }

            // 日志内容
            if (messages.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "暂无日志",
                        style = MaterialTheme.typography.bodySmall,
                        color = colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                    )
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(8.dp),
                    verticalArrangement = Arrangement.spacedBy(2.dp)
                ) {
                    items(messages) { message ->
                        Text(
                            text = message,
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = FontFamily.Monospace,
                            fontSize = 11.sp,
                            color = colorScheme.onSurface.copy(alpha = 0.9f),
                            lineHeight = 14.sp
                        )
                    }
                }
            }
        }
    }
}

/**
 * 紧急停止按钮
 */
@Composable
private fun EmergencyStopButton(
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(
            containerColor = Color(0xFFD32F2F)
        ),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier
            .height(48.dp)
            .width(160.dp)
    ) {
        Icon(
            imageVector = Icons.Default.Warning,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = "紧急停止",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold
        )
    }
}

