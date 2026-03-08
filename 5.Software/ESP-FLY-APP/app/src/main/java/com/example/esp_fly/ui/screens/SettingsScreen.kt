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
 * 设置页面（双环PID：角度环 + 角速度环，两个页签切换）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    pidSettings: PidSettings,
    isConnected: Boolean,
    onBack: () -> Unit,
    onPidSettingsChanged: (PidSettings) -> Unit,
    onSendAllPid: () -> Unit
) {
    val colorScheme = MaterialTheme.colorScheme
    var selectedTabIndex by remember { mutableIntStateOf(0) }

    val tabs = listOf("角度环（外环）", "角速度环（内环）")

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
                    FilledTonalButton(
                        onClick = {
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

            // 页签栏
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = colorScheme.surfaceVariant.copy(alpha = 0.5f),
                contentColor = colorScheme.primary
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTabIndex == index,
                        onClick = { selectedTabIndex = index },
                        text = {
                            Text(
                                text = title,
                                style = MaterialTheme.typography.labelLarge,
                                fontWeight = if (selectedTabIndex == index) FontWeight.Bold else FontWeight.Normal
                            )
                        }
                    )
                }
            }

            // 内容区域
            when (selectedTabIndex) {
                0 -> {
                    // 角度环（外环）
                    PidLoopContent(
                        rollParams = pidSettings.angleRoll,
                        pitchParams = pidSettings.anglePitch,
                        yawParams = pidSettings.angleYaw,
                        labelPrefix = "角度",
                        onRollChanged = { onPidSettingsChanged(pidSettings.copy(angleRoll = it)) },
                        onPitchChanged = { onPidSettingsChanged(pidSettings.copy(anglePitch = it)) },
                        onYawChanged = { onPidSettingsChanged(pidSettings.copy(angleYaw = it)) }
                    )
                }
                1 -> {
                    // 角速度环（内环）
                    PidLoopContent(
                        rollParams = pidSettings.rateRoll,
                        pitchParams = pidSettings.ratePitch,
                        yawParams = pidSettings.rateYaw,
                        labelPrefix = "角速度",
                        onRollChanged = { onPidSettingsChanged(pidSettings.copy(rateRoll = it)) },
                        onPitchChanged = { onPidSettingsChanged(pidSettings.copy(ratePitch = it)) },
                        onYawChanged = { onPidSettingsChanged(pidSettings.copy(rateYaw = it)) }
                    )
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
 * 单个PID环的内容（Roll/Pitch/Yaw 三列卡片）
 */
@Composable
private fun PidLoopContent(
    rollParams: PidParams,
    pitchParams: PidParams,
    yawParams: PidParams,
    labelPrefix: String,
    onRollChanged: (PidParams) -> Unit,
    onPitchChanged: (PidParams) -> Unit,
    onYawChanged: (PidParams) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        PidCard(
            title = "Roll $labelPrefix",
            params = rollParams,
            onParamsChanged = onRollChanged,
            modifier = Modifier.weight(1f)
        )
        PidCard(
            title = "Pitch $labelPrefix",
            params = pitchParams,
            onParamsChanged = onPitchChanged,
            modifier = Modifier.weight(1f)
        )
        PidCard(
            title = "Yaw $labelPrefix",
            params = yawParams,
            onParamsChanged = onYawChanged,
            modifier = Modifier.weight(1f)
        )
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
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = colorScheme.primary
            )

            HorizontalDivider(color = colorScheme.outlineVariant)

            PidInputField(
                label = "P (比例)",
                value = params.kp,
                onValueChanged = { onParamsChanged(params.copy(kp = it)) },
                description = "响应速度，值越大响应越快"
            )

            PidInputField(
                label = "I (积分)",
                value = params.ki,
                onValueChanged = { onParamsChanged(params.copy(ki = it)) },
                description = "消除稳态误差"
            )

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
    var textValue by remember { mutableStateOf(value.toString()) }
    var lastSyncedValue by remember { mutableFloatStateOf(value) }

    // 仅当外部值被其他来源修改时（非本输入框触发）才同步文本
    if (value != lastSyncedValue && value != textValue.toFloatOrNull()) {
        textValue = value.toString()
        lastSyncedValue = value
    }

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
                newValue.toFloatOrNull()?.let {
                    lastSyncedValue = it
                    onValueChanged(it)
                }
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
