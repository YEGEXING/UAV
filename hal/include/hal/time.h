#ifndef HAL_TIME_H
#define HAL_TIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint32_t hal_time_now_ms(void);
void hal_idle(void);

#ifdef __cplusplus
}
#endif

#endif
