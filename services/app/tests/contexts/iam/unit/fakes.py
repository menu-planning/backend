from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.iam.core.services.uow import UnitOfWork


class FakeGenericRepo:
    def __init__(self):
        self.seen = set()
        self._obj = set()

    async def add(self, obj):
        self._obj.add(obj)
        self.seen.add(obj)

    async def get(self, id):
        for i in self._obj:
            if hasattr(i, "id") and i.id == id:
                self.seen.add(i)
                return i
        else:
            raise EntityNotFoundException(entity_id=id, repository=self) # type: ignore

    async def query(self, filter=None):
        if filter is None:
            return list(self._obj)
        result = []
        for i in self._obj:
            for k, v in filter.items():
                if k not in dir(i):
                    break
                elif getattr(i, k) != v:
                    break
            else:
                result.append(i)
                self.seen.add(i)
        return result

    async def persist(self, obj):
        assert (
            obj in self.seen
        ), "Cannon persist entity which is unknown to the repo. Did you forget to call repo.add() for this entity?"


class FakeUnitOfWork(UnitOfWork):
    def __init__(self):
        self.committed = False
        self.users = FakeGenericRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    async def commit(self):
        await self._commit()

    def collect_new_events(self):
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if hasattr(attr, "seen"):
                for obj in getattr(attr, "seen"):
                    if hasattr(obj, "events"):
                        while getattr(obj, "events"):
                            yield getattr(obj, "events").pop(0)

    async def _commit(self):
        self.committed = True

    async def rollback(self):
        pass
