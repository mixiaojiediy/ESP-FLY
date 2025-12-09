idf_component_register(SRCS "wifi_esp32.c" "config_receiver.c"
                      INCLUDE_DIRS "." "include"
                      REQUIRES crazyflie platform config esp_wifi)