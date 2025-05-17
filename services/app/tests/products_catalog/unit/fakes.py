from src.contexts.products_catalog.core.domain.entities.product import Product
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException


class FakeGenericRepo:
    def __init__(self):
        self.seen: set[Product] = set()
        self._obj: set[Product] = set()

    async def add(self, obj):
        self._obj.add(obj)
        self.seen.add(obj)

    async def get(self, id):
        for i in self._obj:
            if hasattr(i, "id") and i.id == id:
                self.seen.add(i)
                return i
        else:
            raise EntityNotFoundException(entity_id=id, repository=self)

    async def query(
        self, filter=None, starting_stmt=None, hide_undefined_auto_products: bool = True
    ):
        short_list = self._obj
        if hide_undefined_auto_products:
            short_list = set(
                [
                    i
                    for i in self._obj
                    if i.source_id != "auto" or i.is_food_houses_choice != None
                ]
            )
        if filter is None:
            return list(short_list)
        result = []
        for i in short_list:
            if getattr(i, "discarded", False):
                continue
            for k, v in filter.items():
                if k.replace("_gte", "").replace("_lte", "") not in dir(i):
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
        self.products = FakeGenericRepo()

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
