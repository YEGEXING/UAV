# Public interfaces and their HAL implementations.
add_library(firmware_hal STATIC
    src/debug.c
    src/time.c
)
target_include_directories(firmware_hal PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
target_link_libraries(firmware_hal
    PUBLIC firmware_common
    PRIVATE stm32cubemx
)
