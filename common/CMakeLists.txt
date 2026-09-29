add_library(firmware_common INTERFACE)
target_include_directories(firmware_common INTERFACE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

