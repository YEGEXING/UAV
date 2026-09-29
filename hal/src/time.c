#include "hal/time.h"

#include "main.h"

uint32_t hal_time_now_ms(void)
{
    return HAL_GetTick();
}

void hal_idle(void)
{
}
