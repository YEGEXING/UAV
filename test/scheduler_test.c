#include "framework/scheduler.h"

#include <assert.h>
#include <stdint.h>

static uint32_t fake_time_ms;
static uint8_t call_log[16];
static uint8_t call_count;

static uint32_t fake_now(void)
{
    return fake_time_ms;
}

static void task_one(void)
{
    call_log[call_count++] = 1U;
}

static void task_two(void)
{
    call_log[call_count++] = 2U;
}

static void reset_test(uint32_t now)
{
    fake_time_ms = now;
    call_count = 0U;
    scheduler_init(fake_now);
}

static void test_priority_order(void)
{
    const scheduler_task_config_t low = {"low", task_two, 10U, 0U, 2U};
    const scheduler_task_config_t high = {"high", task_one, 10U, 0U, 1U};

    reset_test(0U);
    assert(scheduler_register(2U, &low) == STATUS_OK);
    assert(scheduler_register(1U, &high) == STATUS_OK);
    scheduler_run_once();

    assert(call_count == 2U);
    assert(call_log[0] == 1U);
    assert(call_log[1] == 2U);
}

static void test_staggered_periods(void)
{
    const scheduler_task_config_t number = {"number", task_one, 2000U, 0U, 0U};
    const scheduler_task_config_t text = {"text", task_two, 2000U, 1000U, 1U};

    reset_test(0U);
    assert(scheduler_register(1U, &number) == STATUS_OK);
    assert(scheduler_register(2U, &text) == STATUS_OK);

    scheduler_run_once();
    assert(call_count == 1U && call_log[0] == 1U);

    fake_time_ms = 1000U;
    scheduler_run_once();
    assert(call_count == 2U && call_log[1] == 2U);

    fake_time_ms = 2000U;
    scheduler_run_once();
    assert(call_count == 3U && call_log[2] == 1U);
}

static void test_duplicate_and_invalid_registration(void)
{
    const scheduler_task_config_t valid = {"valid", task_one, 10U, 0U, 0U};
    const scheduler_task_config_t invalid = {"invalid", task_one, 0U, 0U, 1U};

    reset_test(0U);
    assert(scheduler_register(1U, &valid) == STATUS_OK);
    assert(scheduler_register(1U, &valid) == STATUS_ALREADY_REGISTERED);
    assert(scheduler_register(2U, &invalid) == STATUS_INVALID_ARGUMENT);
}

static void test_tick_rollover(void)
{
    const scheduler_task_config_t task = {"rollover", task_one, 1000U, 1000U, 0U};

    reset_test(UINT32_MAX - 500U);
    assert(scheduler_register(1U, &task) == STATUS_OK);

    scheduler_run_once();
    assert(call_count == 0U);

    fake_time_ms = 499U;
    scheduler_run_once();
    assert(call_count == 1U);
}

static void test_missed_period_is_not_replayed(void)
{
    const scheduler_task_config_t task = {"periodic", task_one, 2000U, 0U, 0U};

    reset_test(0U);
    assert(scheduler_register(1U, &task) == STATUS_OK);
    scheduler_run_once();
    assert(call_count == 1U);

    fake_time_ms = 5500U;
    scheduler_run_once();
    scheduler_run_once();
    assert(call_count == 2U);

    fake_time_ms = 6000U;
    scheduler_run_once();
    assert(call_count == 3U);
}

int main(void)
{
    test_priority_order();
    test_staggered_periods();
    test_duplicate_and_invalid_registration();
    test_tick_rollover();
    test_missed_period_is_not_replayed();
    return 0;
}
