#include "hal/debug.h"

#include <string.h>

#include "usart.h"

void debug_print(const char *text)
{
    if (text == NULL)
    {
        return;
    }

    HAL_UART_Transmit(&huart1,
                      (uint8_t *)text,
                      (uint16_t)strlen(text),
                      HAL_MAX_DELAY);
}
