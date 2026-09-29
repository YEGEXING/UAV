#ifndef FRAMEWORK_SCHEDULER_H
#define FRAMEWORK_SCHEDULER_H

#include <stdint.h>

#include "common/status.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SCHEDULER_MAX_TASKS 256U

typedef uint8_t scheduler_task_id_t;
typedef void (*scheduler_task_fn_t)(void);
typedef uint32_t (*scheduler_now_fn_t)(void);

typedef struct
{
    const char *name;
    scheduler_task_fn_t run;
    uint32_t period_ms;
    uint32_t start_delay_ms;
    uint8_t priority;
} scheduler_task_config_t;

void scheduler_init(scheduler_now_fn_t now);
status_t scheduler_register(scheduler_task_id_t id,
                            const scheduler_task_config_t *config);
void scheduler_run_once(void);

#ifdef __cplusplus
}
#endif

#endif
