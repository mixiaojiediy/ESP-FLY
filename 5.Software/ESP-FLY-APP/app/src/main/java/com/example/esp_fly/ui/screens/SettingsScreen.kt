package com.example.esp_fly.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.example.esp_fly.viewmodel.PidParams
import com.example.esp_fly.viewmodel.PidSettings

/**
 * 设置页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    pidSettings: PidSettings,
    isConnected: Boolean,
    onBack: () -> Unit,
    onPidSettingsChanged: (PidSettings) -> Unit,
    onSendAllPid: () -> Unit,
    onQueryPid: () -> Unit = {}
) {
    val colorScheme = MaterialTheme.colorScheme
    var currentSettings by remember(pidSettings) { mutableStateOf(pidSettings) }
    var selectedTab by remember { mutableStateOf(0) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(colorScheme.background)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            // 顶部栏
            TopAppBar(
                title = {
                    Text(
                        text = "PID 参数设置",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                },
                actions = {
                    // 读取按钮
                    OutlinedButton(
                        onClick = onQueryPid,
                        enabled = isConnected,
                        modifier = Modifier.padding(end = 4.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Download,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("读取")
                    }
                    // 发送按钮
                    FilledTonalButton(
                        onClick = {
                            onPidSettingsChanged(currentSettings)
                            onSendAllPid()
                        },
                        enabled = isConnected,
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Send,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("发送")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = colorScheme.surfaceVariant.copy(alpha = 0.8f)
                )
            )

            // Tab选择
            TabRow(
                selectedTabIndex = selectedTab,
                containerColor = colorScheme.surfaceVariant.copy(alpha = 0.5f)
            ) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("角速度环 (Rate)") },
                    icon = { Icon(Icons.Default.Speed, contentDescription = null) }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("姿态环 (Attitude)") },
                    icon = { Icon(Icons.Default.FlightTakeoff, contentDescription = null) }
                )
            }

            // 内容区域
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                when (selectedTab) {
                    0 -> {
                        // 角速度环 PID
                        PidCard(
                            title = "Roll 角速度",
                            params = currentSettings.rateRoll,
                            onParamsChanged = { 
                                currentSettings = currentSettings.copy(rateRoll = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                        PidCard(
                            title = "Pitch 角速度",
                            params = currentSettings.ratePitch,
                            onParamsChanged = {
                                currentSettings = currentSettings.copy(ratePitch = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                        PidCard(
                            title = "Yaw 角速度",
                            params = currentSettings.rateYaw,
                            onParamsChanged = {
                                currentSettings = currentSettings.copy(rateYaw = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    1 -> {
                        // 姿态环 PID
                        PidCard(
                            title = "Roll 姿态",
                            params = currentSettings.attitudeRoll,
                            onParamsChanged = {
                                currentSettings = currentSettings.copy(attitudeRoll = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                        PidCard(
                            title = "Pitch 姿态",
                            params = currentSettings.attitudePitch,
                            onParamsChanged = {
                                currentSettings = currentSettings.copy(attitudePitch = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                        PidCard(
                            title = "Yaw 姿态",
                            params = currentSettings.attitudeYaw,
                            onParamsChanged = {
                                currentSettings = currentSettings.copy(attitudeYaw = it)
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
        }

        // 连接状态提示
        if (!isConnected) {
            Surface(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(16.dp),
                color = colorScheme.errorContainer,
                shape = RoundedCornerShape(8.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.WifiOff,
                        contentDescription = null,
                        tint = colorScheme.onErrorContainer,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "未连接设备，请先连接后再发送参数",
                        style = MaterialTheme.typography.bodySmall,
                        color = colorScheme.onErrorContainer
                    )
                }
            }
        }
    }
}

/**
 * PID参数卡片
 */
@Composable
private fun PidCard(
    title: String,
    params: PidParams,
    onParamsChanged: (PidParams) -> Unit,
    modifier: Modifier = Modifier
) {
    val colorScheme = MaterialTheme.colorScheme

    Card(
        modifier = modifier.fillMaxHeight(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 标题
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = colorScheme.primary
            )

            Divider(color = colorScheme.outlineVariant)

            // P参数
            PidInputField(
                label = "P (比例)",
                value = params.kp,
                onValueChanged = { onParamsChanged(params.copy(kp = it)) },
                description = "响应速度，值越大响应越快"
            )

            // I参数
            PidInputField(
                label = "I (积分)",
                value = params.ki,
                onValueChanged = { onParamsChanged(params.copy(ki = it)) },
                description = "消除稳态误差"
            )

            // D参数
            PidInputField(
                label = "D (微分)",
                value = params.kd,
                onValueChanged = { onParamsChanged(params.copy(kd = it)) },
                description = "抑制超调，改善稳定性"
            )
        }
    }
}

/**
 * PID输入字段
 */
@Composable
private fun PidInputField(
    label: String,
    value: Float,
    onValueChanged: (Float) -> Unit,
    description: String
) {
    val colorScheme = MaterialTheme.colorScheme
    var textValue by remember(value) { mutableStateOf(value.toString()) }

    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Medium,
            color = colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(4.dp))
        
        OutlinedTextField(
            value = textValue,
            onValueChange = { newValue ->
                textValue = newValue
                newValue.toFloatOrNull()?.let { onValueChanged(it) }
            },
            modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            singleLine = true,
            shape = RoundedCornerShape(8.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = colorScheme.primary,
                unfocusedBorderColor = colorScheme.outline
            )
        )
        
        Spacer(modifier = Modifier.height(2.dp))
        
        Text(
            text = description,
            style = MaterialTheme.typography.bodySmall,
            color = colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
        )
    }
}

