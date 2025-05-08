from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException


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
            if hasattr(i, "cfe_key") and i.cfe_key == id:
                self.seen.add(i)
                return i
            if hasattr(i, "cnpj") and (i.cnpj == id or str(i.cnpj) == id):
                self.seen.add(i)
                return i
        else:
            raise EntityNotFoundException(entity_id=id, repository=self)

    async def get_by_cfe_key_and_house(self, cfe_key, house_id):
        for i in self._obj:
            if (
                hasattr(i, "cfe_key")
                and i.cfe_key == cfe_key
                and hasattr(i, "house_id")
                and i.house_id == house_id
            ):
                self.seen.add(i)
                return i
        else:
            raise EntityNotFoundException(entity_id=cfe_key, repository=self)

    async def query(self, filter=None):
        if filter is None:
            return list(self._obj)
        result = []
        for i in self._obj:
            if getattr(i, "discarded", False):
                continue
            for k, v in filter.items():
                if k == "id":
                    if hasattr(i, "cfe_key") and getattr(i, "cfe_key") != v:
                        break
                    elif hasattr(i, "cnpj") and not (
                        getattr(i, "cnpj") == v or str(getattr(i, "cnpj")) == v
                    ):
                        break
                elif k.replace("_gte", "").replace("_lte", "") not in dir(i):
                    break
                elif "_gte" in k and getattr(i, k.replace("_gte", "")) < v:
                    break
                elif "_lte" in k and getattr(i, k.replace("_gte", "")) > v:
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

    async def persist_all(self, domain_entities: list | None = None):
        for obj in self.seen:
            await self.persist(obj)


class FakeUnitOfWork:
    def __init__(self):
        self.committed = False
        self.receipts = FakeGenericRepo()
        self.sellers = FakeGenericRepo()

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
