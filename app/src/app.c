#include "app/app.h"

#include "framework/scheduler.h"
#include "hal/time.h"

enum
{
    APP_TASK_PRINT_NUM = 0U,
    APP_TASK_PRINT_STRING = 1U
};

status_t app_init(void)
{
    static const scheduler_task_config_t print_num_task = {
        "print_num", app_print_num, 2000U, 0U, 0U};
    static const scheduler_task_config_t print_string_task = {
        "print_string", app_print_string, 2000U, 1000U, 1U};
    status_t status;

    scheduler_init(hal_time_now_ms);

    status = scheduler_register(APP_TASK_PRINT_NUM, &print_num_task);
    if (status != STATUS_OK)
    {
        return status;
    }

    status = scheduler_register(APP_TASK_PRINT_STRING, &print_string_task);
    if (status != STATUS_OK)
    {
        return status;
    }

    return STATUS_OK;
}

void app_run(void)
{
    scheduler_run_once();
    hal_idle();
}
