import asyncio
from datetime import datetime
from typing import Awaitable, Callable

from croniter import croniter


async def run_cron(task: Callable[[], Awaitable[None]] | Callable[[], None], cron_expr: str) -> None:
    """Run a task forever following a cron expression.

    Accepts async or sync callables. Uses croniter to compute the next fire time.
    """
    base = datetime.now()
    itr = croniter(cron_expr, base)
    while True:
        next_dt = itr.get_next(datetime)
        delay = (next_dt - datetime.now()).total_seconds()
        await asyncio.sleep(max(0, int(delay)))
        result = task()
        if asyncio.iscoroutine(result):
            try:
                await result
            except Exception as e:  # pragma: no cover
                print(f"[Cron] Task error: {e}")