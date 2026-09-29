#ifndef APP_APP_H
#define APP_APP_H

#include "common/status.h"

#ifdef __cplusplus
extern "C" {
#endif

status_t app_init(void);
void app_run(void);
void app_print_num(void);
void app_print_string(void);

#ifdef __cplusplus
}
#endif

#endif
