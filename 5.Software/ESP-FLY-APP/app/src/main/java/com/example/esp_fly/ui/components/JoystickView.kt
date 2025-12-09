package com.example.esp_fly.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlin.math.sqrt

/**
 * 摇杆类型
 */
enum class JoystickType {
    FULL,           // 全方向摇杆(上下左右)
    VERTICAL_ONLY,  // 仅垂直方向(上下)
    THROTTLE        // 油门模式: 仅上半区域有效，自动回中
}

/**
 * 摇杆回调数据
 * @param x 水平方向值 (-1.0 ~ 1.0)
 * @param y 垂直方向值 (-1.0 ~ 1.0), 向上为正
 */
data class JoystickPosition(
    val x: Float = 0f,
    val y: Float = 0f
)

/**
 * 自定义摇杆组件 - 简洁线条风格
 * 
 * @param modifier 修饰符
 * @param size 摇杆整体大小
 * @param type 摇杆类型
 * @param onPositionChanged 位置变化回调
 */
@Composable
fun JoystickView(
    modifier: Modifier = Modifier,
    size: Dp = 200.dp,
    type: JoystickType = JoystickType.FULL,
    onPositionChanged: (JoystickPosition) -> Unit = {}
) {
    val primaryColor = MaterialTheme.colorScheme.primary
    val outlineColor = MaterialTheme.colorScheme.outline
    val surfaceColor = MaterialTheme.colorScheme.surfaceVariant

    // 摇杆手柄位置 (相对于中心的偏移)
    var handleOffset by remember { mutableStateOf(Offset.Zero) }
    
    // 当前输出值
    var currentPosition by remember { mutableStateOf(JoystickPosition()) }

    Box(
        modifier = modifier.size(size)
    ) {
        Canvas(
            modifier = Modifier
                .size(size)
                .pointerInput(Unit) {
                    detectDragGestures(
                        onDragStart = { offset ->
                            val center = Offset(
                                this.size.width / 2f,
                                this.size.height / 2f
                            )
                            val maxRadius = this.size.width / 2f * 0.7f
                            handleOffset = constrainOffset(
                                offset - center,
                                maxRadius,
                                type
                            )
                            updatePosition(handleOffset, maxRadius, type) { pos ->
                                currentPosition = pos
                                onPositionChanged(pos)
                            }
                        },
                        onDrag = { change, _ ->
                            change.consume()
                            val center = Offset(
                                this.size.width / 2f,
                                this.size.height / 2f
                            )
                            val maxRadius = this.size.width / 2f * 0.7f
                            handleOffset = constrainOffset(
                                change.position - center,
                                maxRadius,
                                type
                            )
                            updatePosition(handleOffset, maxRadius, type) { pos ->
                                currentPosition = pos
                                onPositionChanged(pos)
                            }
                        },
                        onDragEnd = {
                            // 所有模式都自动回中
                            handleOffset = Offset.Zero
                            currentPosition = JoystickPosition(0f, 0f)
                            onPositionChanged(currentPosition)
                        }
                    )
                }
        ) {
            val canvasSize = size.toPx()
            val center = Offset(canvasSize / 2f, canvasSize / 2f)
            val bgRadius = canvasSize / 2f - 8f
            val handleRadius = canvasSize * 0.12f
            val movementRadius = bgRadius * 0.7f

            // 绘制背景圆(简洁线条)
            drawCircle(
                color = surfaceColor,
                radius = bgRadius,
                center = center
            )
            
            // 绘制外圈边框
            drawCircle(
                color = outlineColor,
                radius = bgRadius,
                center = center,
                style = Stroke(width = 2f)
            )

            // 绘制十字准线
            val crossSize = movementRadius * 0.4f
            drawLine(
                color = outlineColor.copy(alpha = 0.5f),
                start = Offset(center.x - crossSize, center.y),
                end = Offset(center.x + crossSize, center.y),
                strokeWidth = 1.5f
            )
            drawLine(
                color = outlineColor.copy(alpha = 0.5f),
                start = Offset(center.x, center.y - crossSize),
                end = Offset(center.x, center.y + crossSize),
                strokeWidth = 1.5f
            )

            // 绘制移动范围圆
            drawCircle(
                color = outlineColor.copy(alpha = 0.3f),
                radius = movementRadius,
                center = center,
                style = Stroke(width = 1.5f)
            )

            // 油门模式特殊标记：上半区域指示
            if (type == JoystickType.THROTTLE) {
                // 绘制上半区域指示箭头
                val arrowY = center.y - movementRadius - 15f
                drawLine(
                    color = primaryColor.copy(alpha = 0.6f),
                    start = Offset(center.x - 10f, arrowY + 8f),
                    end = Offset(center.x, arrowY),
                    strokeWidth = 2f
                )
                drawLine(
                    color = primaryColor.copy(alpha = 0.6f),
                    start = Offset(center.x + 10f, arrowY + 8f),
                    end = Offset(center.x, arrowY),
                    strokeWidth = 2f
                )
            }

            // 绘制摇杆手柄
            val handleCenter = center + handleOffset
            
            // 手柄主体(简洁圆形)
            drawCircle(
                color = primaryColor,
                radius = handleRadius,
                center = handleCenter
            )

            // 手柄边框
            drawCircle(
                color = primaryColor.copy(alpha = 0.8f),
                radius = handleRadius,
                center = handleCenter,
                style = Stroke(width = 2f)
            )
            
            // 手柄中心点
            drawCircle(
                color = Color.White,
                radius = handleRadius * 0.3f,
                center = handleCenter
            )
        }
    }
}

/**
 * 约束偏移量在有效范围内
 */
private fun constrainOffset(
    offset: Offset,
    maxRadius: Float,
    type: JoystickType
): Offset {
    val x = when (type) {
        JoystickType.VERTICAL_ONLY, JoystickType.THROTTLE -> 0f
        JoystickType.FULL -> offset.x
    }
    
    var y = offset.y
    
    // 油门模式：只允许向上(y为负值表示向上)
    if (type == JoystickType.THROTTLE) {
        y = y.coerceAtMost(0f)  // 只允许负值(向上)
    }

    val distance = sqrt(x * x + y * y)
    return if (distance > maxRadius) {
        val ratio = maxRadius / distance
        Offset(x * ratio, y * ratio)
    } else {
        Offset(x, y)
    }
}

/**
 * 更新归一化位置
 */
private inline fun updatePosition(
    offset: Offset,
    maxRadius: Float,
    type: JoystickType,
    onUpdate: (JoystickPosition) -> Unit
) {
    val x = when (type) {
        JoystickType.VERTICAL_ONLY, JoystickType.THROTTLE -> 0f
        JoystickType.FULL -> (offset.x / maxRadius).coerceIn(-1f, 1f)
    }
    
    // Y轴向上为正
    var y = (-offset.y / maxRadius).coerceIn(-1f, 1f)
    
    // 油门模式：只有正值(向上)，负值返回0
    if (type == JoystickType.THROTTLE) {
        y = y.coerceAtLeast(0f)
    }
    
    onUpdate(JoystickPosition(x, y))
}
