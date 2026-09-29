cmake_minimum_required(VERSION 3.22)

project(firmware_tests LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

enable_testing()

add_executable(scheduler_test
    scheduler_test.c
    ../framework/src/scheduler.c
)
target_include_directories(scheduler_test PRIVATE
    ../common/include
    ../framework/include
)

if(MSVC)
    target_compile_options(scheduler_test PRIVATE /W4 /WX)
else()
    target_compile_options(scheduler_test PRIVATE -Wall -Wextra -Werror)
endif()

add_test(NAME scheduler_test COMMAND scheduler_test)
