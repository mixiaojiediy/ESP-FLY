idf_component_register(SRCS "main.c"
                       INCLUDE_DIRS "."
                       REQUIRES status_led nvs_flash platform
                       LDFRAGMENTS linker_fragment.lf)