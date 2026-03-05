idf_component_register(SRCS "packet_codec.c"
                             "command_receiver.c"
                             "protocol_dispatcher.c"
                             "data_sender.c"
                             "config_receiver.c"
                       INCLUDE_DIRS "include"
                       REQUIRES crazyflie motors wifi)
