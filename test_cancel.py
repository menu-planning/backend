from contextlib import asynccontextmanager
import anyio

global_list = []

@asynccontextmanager
async def test_cancel():
    print("Starting test_cancel")
    yield global_list
    await anyio.sleep(3)
    global_list.append("test_cancel")
    print("Ending test_cancel")

async def long_running_task(i):
    print("Starting long_running_task %s" % i)
    try:
        async with test_cancel() as global_list:
            await anyio.sleep(10)
            global_list.append("long_running_task %s" % i)
    except anyio.get_cancelled_exc_class():
        print("Cancelled")
        global_list.append("long_running_task %s cancelled" % i)
        raise
    except Exception:
        global_list.append("long_running_task %s exception" % i)
        raise
    print("Ending long_running_task %s" % i)

async def main():
    with anyio.move_on_after(4) as scope:
        async with anyio.create_task_group() as tg:
            tg.start_soon(long_running_task, 1)
            tg.start_soon(long_running_task, 2)
            tg.start_soon(long_running_task, 3)
    if scope.cancel_called:
        print("Timeout")
        print(global_list)


if __name__ == "__main__":
    anyio.run(main)