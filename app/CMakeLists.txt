add_library(firmware_app STATIC
    src/app.c
    src/tasks/print_num_task.c
    src/tasks/print_string_task.c
)
target_include_directories(firmware_app PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
target_link_libraries(firmware_app PUBLIC
    firmware_framework
    firmware_hal
    firmware_common
    firmware_utils
)
