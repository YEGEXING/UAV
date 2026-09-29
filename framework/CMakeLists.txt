add_library(firmware_framework STATIC
    src/scheduler.c
)
target_include_directories(firmware_framework PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
target_link_libraries(firmware_framework PUBLIC
    firmware_common
    firmware_utils
)
