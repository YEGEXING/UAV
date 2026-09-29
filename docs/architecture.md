# 架构与移植约束

## 分层目标

依赖方向保持单向：

```text
                   +----------------------+
CubeMX main.c ---->|         app          |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   |      framework       |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   | hal 接口及 HAL 实现  |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   |  hw/<board>/cubemx   |
                   +----------------------+

common 和 utils 不依赖任何上层。
```

各层约束：

- `common`：跨层基础类型的预留位置，不包含 STM32 或板级头文件。
- `utils`：与业务和硬件无关的工具预留位置。
- `hal/include`：声明供上层使用的稳定硬件接口。
- `hal/src`：使用当前 CubeMX 工程提供的 HAL Handle 实现这些接口。
- `framework`：实现调度、协议、状态机等可复用机制，只依赖 `hal/common`。
- `app`：产品业务。允许依赖 `framework/hal/common`，禁止包含 CubeMX 头文件。
- `hw/<board>/cubemx`：CubeMX 管理的完整工程，包括 `.ioc`、Core、Drivers、启动文件和链接脚本。
- `test`：公共层单元测试和板级集成测试的预留位置。

禁止公共层反向依赖 `hw`。CMake 每次只加入一个 HW 包，因此不同 STM32 系列中名称相同的 HAL/CMSIS 符号不会冲突。

## 启动路径

CubeMX 完成 HAL、时钟和外设初始化后，在 `USER CODE` 区域调用 `app_init()` 注册任务。主循环只调用 `app_run()`；调度器执行到期任务后进入 `__WFI()`，由 SysTick 或其他中断唤醒。

当前调度器是单线程协作式调度器，不是抢占式 RTOS。它使用固定256任务数组、函数指针和 `HAL_GetTick()`，不使用动态内存。任务按优先级执行并按历史 deadline 推进；错过多个周期时只执行一次，再跳到未来周期。

## 修改 CubeMX 配置

以 H743 为例：

1. 用 STM32CubeMX 打开 `hw/stm32h743/cubemx/h743.ioc`。
2. 修改时钟、引脚和外设，保持 Toolchain 为 CMake、`Keep User Code` 开启。
3. 在该 `cubemx` 目录直接生成代码。
4. 如果已经接入业务入口，检查 `Core/Src/main.c` 对应的 `USER CODE` 区域。
5. 重新执行 H743 和 F103 构建，确认公共接口没有被板级变化污染。

根目录构建只读取 CubeMX 生成的 `cmake/stm32cubemx/CMakeLists.txt`，不会使用各 HW 包内 CubeMX 自带的顶层 CMake 配置。这样 CubeMX 可以继续维护自己的文件，仓库根目录负责组合公共层。

## 增加或更换芯片

新增例如 `stm32g4xx` 时：

1. 在 `hw/stm32g4xx/cubemx` 创建并生成完整 CubeMX CMake 工程。
2. 确认新 CubeMX 工程提供了 `hal/src` 所使用的外设 Handle；如果名称或外设不同，则调整对应 HAL 实现。
3. 在根 `CMakeLists.txt` 的受支持列表中加入板名。
4. 在 `cmake/arm-none-eabi-multiboard.cmake` 中加入 CPU/FPU 参数和链接脚本映射。
5. 在 `CMakePresets.json` 增加该板的 Debug/Release 预设。
6. 需要业务启动入口时，只在生成的 `main.c` 的 `USER CODE` 区域接入。

若新芯片需要新增能力（UART、SPI、Flash 等），先在 `hal/include` 定义公共接口，再在 `hal/src` 使用 CubeMX 生成的外设实现。不要让应用直接使用某一系列的 HAL 类型。

## CubeMX 能解决与不能解决的边界

CubeMX 可以重新生成芯片启动、时钟、外设初始化、HAL/LL 库和中断骨架；它不能自动理解产品板卡的器件连接和业务语义。因此换芯片时通常无需改 `app/framework`，但仍需检查：

- `hal/src` 中硬件能力的实现；
- 外部器件、引脚与 DMA/中断资源映射；
- 链接脚本中的存储布局；
- Cache/MPU、对齐和并发差异；
- 时钟频率变化带来的协议时序。

这些差异都应被限制在新的 HW 包内，而不是泄漏到业务代码中。
