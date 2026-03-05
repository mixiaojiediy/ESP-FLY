# The following five lines of boilerplate have to be in your project's
# CMakeLists in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.5)

set(__PROJECT_GROUP_LINK_COMPONENTS ON)

# 设置额外的组件搜索目录（ESP-IDF 会递归搜索包含 CMakeLists.txt 的子目录）
set(EXTRA_COMPONENT_DIRS 
    "./components/core/crazyflie"
    "./components/config"
    "./components/platform"
    "./components/protocol"
    "./components/lib/dsp_lib"
    "./components/drivers/i2c_bus"
    "./components/drivers/adc"
    "./components/drivers/motors"
    "./components/drivers/status_led"
    "./components/drivers/wifi"
    "./components/drivers/mpu6050"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(ESPDrone)
