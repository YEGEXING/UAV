#include "framework/scheduler.h"

#include <stdbool.h>
#include <stddef.h>

typedef struct
{
    scheduler_task_id_t id;
    scheduler_task_config_t config;
    uint32_t next_run_ms;
} scheduler_task_t;

static scheduler_task_t tasks[SCHEDULER_MAX_TASKS];
static uint16_t task_count;
static scheduler_now_fn_t now_fn;

static bool time_reached(uint32_t now, uint32_t deadline)
{
    return (int32_t)(now - deadline) >= 0;
}

void scheduler_init(scheduler_now_fn_t now)
{
    task_count = 0U;
    now_fn = now;
}

status_t scheduler_register(scheduler_task_id_t id,
                            const scheduler_task_config_t *config)
{
    uint16_t index;
    uint16_t insert_at;

    if ((now_fn == NULL) || (config == NULL) || (config->name == NULL) ||
        (config->run == NULL) || (config->period_ms == 0U))
    {
        return STATUS_INVALID_ARGUMENT;
    }

    if (task_count >= SCHEDULER_MAX_TASKS)
    {
        return STATUS_FULL;
    }

    for (index = 0U; index < task_count; ++index)
    {
        if ((tasks[index].id == id) ||
            (tasks[index].config.priority == config->priority))
        {
            return STATUS_ALREADY_REGISTERED;
        }
    }

    insert_at = task_count;
    while ((insert_at > 0U) &&
           (tasks[insert_at - 1U].config.priority > config->priority))
    {
        tasks[insert_at] = tasks[insert_at - 1U];
        --insert_at;
    }

    tasks[insert_at].id = id;
    tasks[insert_at].config = *config;
    tasks[insert_at].next_run_ms = now_fn() + config->start_delay_ms;
    ++task_count;

    return STATUS_OK;
}

void scheduler_run_once(void)
{
    uint16_t index;

    if (now_fn == NULL)
    {
        return;
    }

    for (index = 0U; index < task_count; ++index)
    {
        scheduler_task_t *task = &tasks[index];
        uint32_t now = now_fn();

        if (!time_reached(now, task->next_run_ms))
        {
            continue;
        }

        task->config.run();

        now = now_fn();
        task->next_run_ms +=
            ((now - task->next_run_ms) / task->config.period_ms + 1U) *
            task->config.period_ms;
    }
}
