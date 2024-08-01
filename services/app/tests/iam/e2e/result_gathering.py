import anyio
from anyio import TASK_STATUS_IGNORED
from anyio.abc import TaskStatus


class NotYet(RuntimeError):
    pass


class ResultGatheringTaskgroup:
    def __init__(self):
        self.result = []

    async def __aenter__(self):
        self._taskgroup = tg = anyio.create_task_group()
        await tg.__aenter__()
        return self

    async def __aexit__(self, *tb):
        try:
            res = await self._taskgroup.__aexit__(*tb)
            return res
        finally:
            del self._taskgroup

    async def _run_one(
        self, pos, proc, a, *, task_status: TaskStatus[None] = TASK_STATUS_IGNORED
    ):
        self.result[pos] = await proc(*a)
        task_status.started()

    async def start(self, proc, *a):
        pos = len(self.result)
        self.result.append(NotYet)
        await self._taskgroup.start(self._run_one, pos, proc, a)
        return pos

    def get_result(self, pos):
        res = self.result[pos]
        if res is NotYet:
            raise NotYet()
        return res
