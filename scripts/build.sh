#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
cd -- "${PROJECT_ROOT}"

BOARD="${1:-h743}"
CONFIG="debug"
DO_CLEAN=false
RUN_TESTS=false

if [[ $# -gt 0 ]]; then
    shift
fi

for argument in "$@"; do
    case "${argument,,}" in
        debug|release)
            CONFIG="${argument,,}"
            ;;
        clean)
            DO_CLEAN=true
            ;;
        test)
            RUN_TESTS=true
            ;;
        *)
            echo "Usage: ./scripts/build.sh <h743|f103|x7> [debug|release] [clean] [test]" >&2
            exit 2
            ;;
    esac
done

case "${BOARD,,}" in
    h743|stm32h743)
        BOARD="stm32h743"
        PRESET_BOARD="h743"
        ;;
    f103|stm32f103)
        BOARD="stm32f103"
        PRESET_BOARD="f103"
        ;;
    x7)
        BOARD="x7"
        PRESET_BOARD="x7"
        ;;
    *)
        echo "Supported boards: h743, f103, x7" >&2
        exit 2
        ;;
esac

case "${CONFIG,,}" in
    debug)
        CONFIG="debug"
        BUILD_TYPE="Debug"
        ;;
    release)
        CONFIG="release"
        BUILD_TYPE="Release"
        ;;
    *)
        echo "Supported configurations: debug, release" >&2
        exit 2
        ;;
esac

command -v cmake >/dev/null 2>&1 || {
    echo "cmake was not found in PATH" >&2
    exit 3
}
command -v arm-none-eabi-gcc >/dev/null 2>&1 || {
    echo "arm-none-eabi-gcc was not found in PATH" >&2
    exit 3
}

PRESET="${PRESET_BOARD}-${CONFIG}"
BUILD_DIR="${PROJECT_ROOT}/build/${PRESET}"

case "$(uname -s)" in
    Linux*)
        if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
            BUILD_ENVIRONMENT="wsl"
        else
            BUILD_ENVIRONMENT="linux"
        fi
        ;;
    MINGW*|MSYS*|CYGWIN*)
        BUILD_ENVIRONMENT="windows"
        ;;
    *)
        BUILD_ENVIRONMENT="$(uname -s)"
        ;;
esac

BUILD_ENVIRONMENT_FILE="${BUILD_DIR}/.build-environment"
if [[ -d "${BUILD_DIR}" ]] && ! ${DO_CLEAN}; then
    PREVIOUS_BUILD_ENVIRONMENT=""
    if [[ -f "${BUILD_ENVIRONMENT_FILE}" ]]; then
        PREVIOUS_BUILD_ENVIRONMENT="$(<"${BUILD_ENVIRONMENT_FILE}")"
    fi
    if [[ "${PREVIOUS_BUILD_ENVIRONMENT}" != "${BUILD_ENVIRONMENT}" ]]; then
        echo "Build environment changed; cleaning ${BUILD_DIR}"
        case "${BUILD_DIR}" in
            "${PROJECT_ROOT}"/build/*)
                rm -rf -- "${BUILD_DIR}"
                ;;
            *)
                echo "Refusing to clean unexpected path: ${BUILD_DIR}" >&2
                exit 3
                ;;
        esac
    fi
fi

if ${DO_CLEAN}; then
    case "${BUILD_DIR}" in
        "${PROJECT_ROOT}"/build/*)
            rm -rf -- "${BUILD_DIR}"
            ;;
        *)
            echo "Refusing to clean unexpected path: ${BUILD_DIR}" >&2
            exit 3
            ;;
    esac
fi

if command -v ninja >/dev/null 2>&1; then
    GENERATOR="Ninja"
    cmake --preset "${PRESET}"
    cmake --build --preset "${PRESET}" --parallel
else
    if command -v mingw32-make >/dev/null 2>&1; then
        GENERATOR="MinGW Makefiles"
    elif command -v make >/dev/null 2>&1; then
        GENERATOR="Unix Makefiles"
    elif command -v nmake >/dev/null 2>&1; then
        GENERATOR="NMake Makefiles"
    else
        echo "Install Ninja or expose make/nmake in PATH." >&2
        exit 3
    fi

    cmake --fresh \
        -S "${PROJECT_ROOT}" \
        -B "${BUILD_DIR}" \
        -G "${GENERATOR}" \
        -DCMAKE_TOOLCHAIN_FILE="${PROJECT_ROOT}/cmake/arm-none-eabi-multiboard.cmake" \
        -DFIRMWARE_BOARD="${BOARD}" \
        -DCMAKE_BUILD_TYPE="${BUILD_TYPE}"
    cmake --build "${BUILD_DIR}" --parallel
fi

printf '%s\n' "${BUILD_ENVIRONMENT}" > "${BUILD_ENVIRONMENT_FILE}"

if ${RUN_TESTS}; then
    TEST_BUILD_DIR="${PROJECT_ROOT}/build/test"
    if ${DO_CLEAN}; then
        rm -rf -- "${TEST_BUILD_DIR}"
    fi

    HOST_COMPILER=()
    HOST_PLATFORM_ARGS=()
    if command -v clang >/dev/null 2>&1; then
        HOST_COMPILER=(-DCMAKE_C_COMPILER=clang)
        if command -v llvm-rc >/dev/null 2>&1; then
            HOST_PLATFORM_ARGS=(-DCMAKE_RC_COMPILER=llvm-rc)
        fi
    elif [[ -x "/c/Program Files/LLVM/bin/clang.exe" ]]; then
        HOST_COMPILER=(-DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe")
        HOST_PLATFORM_ARGS=(-DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe")
    elif command -v gcc >/dev/null 2>&1; then
        HOST_COMPILER=(-DCMAKE_C_COMPILER=gcc)
    fi

    cmake --fresh \
        -S "${PROJECT_ROOT}/test" \
        -B "${TEST_BUILD_DIR}" \
        -G "${GENERATOR}" \
        "${HOST_COMPILER[@]}" \
        "${HOST_PLATFORM_ARGS[@]}"
    cmake --build "${TEST_BUILD_DIR}" --parallel
    ctest --test-dir "${TEST_BUILD_DIR}" --output-on-failure
fi

echo "${BUILD_DIR}/${BOARD}.elf"
echo "${BUILD_DIR}/${BOARD}.bin"
