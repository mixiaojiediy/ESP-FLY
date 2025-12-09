package com.example.esp_fly.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.esp_fly.ui.screens.MainScreen
import com.example.esp_fly.ui.screens.SettingsScreen
import com.example.esp_fly.viewmodel.DroneViewModel

/**
 * 导航路由定义
 */
object NavRoutes {
    const val MAIN = "main"
    const val SETTINGS = "settings"
}

/**
 * 应用导航图
 */
@Composable
fun AppNavGraph(
    navController: NavHostController,
    viewModel: DroneViewModel
) {
    val uiState by viewModel.uiState.collectAsState()

    NavHost(
        navController = navController,
        startDestination = NavRoutes.MAIN
    ) {
        // 主控制界面
        composable(NavRoutes.MAIN) {
            MainScreen(
                uiState = uiState,
                onConnectClick = { viewModel.toggleConnection() },
                onSettingsClick = { navController.navigate(NavRoutes.SETTINGS) },
                onEmergencyStop = { viewModel.emergencyStop() },
                onLeftJoystickChange = { viewModel.updateLeftJoystick(it) },
                onRightJoystickChange = { viewModel.updateRightJoystick(it) },
                onClearConsole = { viewModel.clearConsoleMessages() }
            )
        }

        // 设置界面
        composable(NavRoutes.SETTINGS) {
            SettingsScreen(
                pidSettings = uiState.pidSettings,
                isConnected = uiState.isConnected,
                onBack = { navController.popBackStack() },
                onPidSettingsChanged = { viewModel.updatePidSettings(it) },
                onSendAllPid = { viewModel.sendAllPidToDevice() },
                onQueryPid = { viewModel.queryPidFromDevice() }
            )
        }
    }
}

