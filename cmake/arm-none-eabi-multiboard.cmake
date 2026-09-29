set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_SIZE arm-none-eabi-size)
set(CMAKE_EXECUTABLE_SUFFIX_C ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_ASM ".elf")

if(NOT DEFINED FIRMWARE_BOARD)
    set(FIRMWARE_BOARD "stm32h743" CACHE STRING "Hardware package to build")
endif()

if(FIRMWARE_BOARD STREQUAL "stm32h743")
    set(MCU_FLAGS "-mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard")
    set(LINKER_SCRIPT
        "${CMAKE_SOURCE_DIR}/hw/stm32h743/cubemx/STM32H743xx_FLASH.ld")
elseif(FIRMWARE_BOARD STREQUAL "stm32f103")
    set(MCU_FLAGS "-mcpu=cortex-m3")
    set(LINKER_SCRIPT
        "${CMAKE_SOURCE_DIR}/hw/stm32f103/cubemx/STM32F103xx_FLASH.ld")
elseif(FIRMWARE_BOARD STREQUAL "x7")
    set(MCU_FLAGS "-mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard")
    set(LINKER_SCRIPT
        "${CMAKE_SOURCE_DIR}/hw/X7/STM32H743xx_FLASH.ld")
else()
    message(FATAL_ERROR "No toolchain settings for FIRMWARE_BOARD=${FIRMWARE_BOARD}")
endif()

set(COMMON_FLAGS
    "${MCU_FLAGS} -Wall -Wextra -fdata-sections -ffunction-sections -fstack-usage")
set(CMAKE_C_FLAGS_INIT "${COMMON_FLAGS}")
set(CMAKE_ASM_FLAGS_INIT "${MCU_FLAGS} -x assembler-with-cpp -MMD -MP")
set(CMAKE_C_FLAGS_DEBUG_INIT "-O0 -g3")
set(CMAKE_C_FLAGS_RELEASE_INIT "-Os -g0")
set(CMAKE_EXE_LINKER_FLAGS_INIT
    "${MCU_FLAGS} -T\"${LINKER_SCRIPT}\" --specs=nano.specs -Wl,-Map=firmware.map -Wl,--gc-sections -Wl,--print-memory-usage")

set(TOOLCHAIN_LINK_LIBRARIES m)
