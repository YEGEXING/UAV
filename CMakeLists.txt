cmake_minimum_required(VERSION 3.22)

set(FIRMWARE_BOARD "stm32h743" CACHE STRING "Hardware package to build")
set_property(CACHE FIRMWARE_BOARD PROPERTY STRINGS stm32h743 stm32f103 x7)

if(NOT FIRMWARE_BOARD STREQUAL "stm32h743" AND
   NOT FIRMWARE_BOARD STREQUAL "stm32f103" AND
   NOT FIRMWARE_BOARD STREQUAL "x7")
    message(FATAL_ERROR
        "Unsupported FIRMWARE_BOARD='${FIRMWARE_BOARD}'. "
        "Supported boards: stm32h743, stm32f103, x7")
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

project(firmware LANGUAGES C ASM)

add_executable(firmware)
set_target_properties(firmware PROPERTIES OUTPUT_NAME "${FIRMWARE_BOARD}")

# A CubeMX project is an indivisible HW package. Only the selected package is
# added, so its generated target names cannot collide with another board.
if(FIRMWARE_BOARD STREQUAL "x7")
    set(CUBEMX_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/hw/X7")
else()
    set(CUBEMX_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/hw/${FIRMWARE_BOARD}/cubemx")
endif()
if(NOT EXISTS "${CUBEMX_ROOT}/cmake/stm32cubemx/CMakeLists.txt")
    message(FATAL_ERROR
        "Missing CubeMX CMake output for ${FIRMWARE_BOARD}: ${CUBEMX_ROOT}")
endif()
add_subdirectory(
    "${CUBEMX_ROOT}/cmake/stm32cubemx"
    "${CMAKE_CURRENT_BINARY_DIR}/cubemx"
)

if(FIRMWARE_BOARD STREQUAL "x7")
    target_compile_definitions(stm32cubemx INTERFACE
        USER_VECT_TAB_ADDRESS
        VECT_TAB_OFFSET=0x00020000U
    )
endif()

add_subdirectory(common)
add_subdirectory(utils)
add_subdirectory(hal)
add_subdirectory(framework)
add_subdirectory(app)

target_link_libraries(firmware
    firmware_app
    stm32cubemx
)

if(CMAKE_OBJCOPY)
    add_custom_command(TARGET firmware POST_BUILD
        COMMAND ${CMAKE_OBJCOPY} -O binary
            $<TARGET_FILE:firmware>
            $<TARGET_FILE_DIR:firmware>/${FIRMWARE_BOARD}.bin
        COMMENT "Generating ${FIRMWARE_BOARD}.bin"
    )
endif()

message(STATUS "Firmware board: ${FIRMWARE_BOARD}")
message(STATUS "CubeMX package: ${CUBEMX_ROOT}")
