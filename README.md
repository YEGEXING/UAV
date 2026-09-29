# STM32 多板级固件框架

本仓库把 STM32CubeMX 生成工程整体作为 `hw` 层，同时把业务代码、通用框架和硬件接口移到稳定的公共层。当前同一套公共代码可构建：

- STM32H743：`hw/stm32h743`
- STM32F103：`hw/stm32f103`
- X7（STM32H743）：`hw/X7`

设计借鉴了 `D:/swordfish` 的分层思想，但没有复制其中的实现代码。两个 HW 包来自原有的 H743、F103 CubeMX 工程。

## 目录

```text
app/                         产品业务层骨架
framework/                   可复用框架层骨架
hal/                         公共硬件接口及 HAL 实现
common/                      跨层基础类型层骨架
utils/                       无硬件依赖的通用工具层骨架
test/                        测试层骨架
hw/
  stm32h743/
    cubemx/                  完整 CubeMX 工程和 .ioc
  stm32f103/
    cubemx/                  完整 CubeMX 工程和 .ioc
  X7/                        完整 X7 CubeMX 工程和 .ioc
cmake/                       多板级工具链选择
docs/architecture.md         依赖规则和换芯片流程
```

CubeMX 代码只负责芯片初始化与驱动，公共层保存可跨芯片复用的接口、调度器和应用任务。

当前 `framework` 提供固定容量的单线程协作式调度器，最多注册256个周期任务，不使用动态内存。`app` 已注册两个任务：`app_print_num()` 每2秒打印 `123456`，`app_print_string()` 错开1秒、每2秒打印 `Hi!`。

## 构建

需要 `arm-none-eabi-gcc`、CMake 和 Ninja 在 `PATH` 中。

推荐在 Git Bash、MSYS2、Cygwin、WSL 或 Linux 中使用统一脚本：

```bash
./scripts/build.sh h743
./scripts/build.sh f103
./scripts/build.sh x7
./scripts/build_all.sh

# 清理后重新构建
./scripts/build.sh h743 clean

# 构建并运行测试
./scripts/build.sh h743 test
```

默认构建 Debug。需要 Release 时增加 `release`，参数可以组合，例如 `./scripts/build.sh h743 release clean test`。脚本优先使用 Ninja，也会自动检测 `mingw32-make`、`make` 或 `nmake`。STM32 裸机固件需要通过下载器烧录后运行。

也可以直接使用 CMake Preset：

```powershell
cmake --preset h743-debug
cmake --build --preset h743-debug

cmake --preset f103-debug
cmake --build --preset f103-debug

cmake --preset x7-debug
cmake --build --preset x7-debug
```

输出位于 `build/<preset>/`，固件包括板名对应的 `.elf` 和 `.bin`。

## X7 Type-C 烧录

X7 固件从 `0x08020000` 开始链接，为已有的 FMT/ArduPilot Bootloader 保留前 128 KiB。首次使用先安装串口依赖：

```powershell
python -m pip install -r tools/x7_uploader/requirements.txt
```

先单独编译 X7 固件：

```bash
./scripts/build.sh x7
```

编译与烧录互不绑定。生成固件后，由用户根据实际连接方式选择烧录工具。

使用已有 FMT/ArduPilot Type-C Bootloader 时，可以选择项目提供的 Python 上传器：

```powershell
python tools/x7_uploader/uploader.py --firmware build/x7-debug/x7.bin --yes --wait 60
```

也可以使用 STM32CubeProgrammer、ST-Link 或其他烧录工具。通过 SWD 使用 STM32CubeProgrammer 时，可直接选择 `build/x7-debug/x7.elf`；使用 `.bin` 时，X7 应用下载地址为 `0x08020000`。构建脚本不调用任何烧录程序。

烧录器只接受 Board ID `1010`、应用区大小 `1966080` 字节的目标。命令等待期间可重新插拔 Type-C。只检查目标、不写入时使用：

```powershell
python tools/x7_uploader/uploader.py --identify --verbose --wait 60
```

如果本机没有 Ninja，也可以选择任意可用的 CMake Makefile 生成器。例如在 Visual Studio Developer PowerShell 中：

```powershell
cmake -S . -B build/h743 -G "NMake Makefiles" `
  -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi-multiboard.cmake `
  -DFIRMWARE_BOARD=stm32h743 -DCMAKE_BUILD_TYPE=Debug
cmake --build build/h743
```
