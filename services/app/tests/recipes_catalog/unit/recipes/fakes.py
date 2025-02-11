from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class FakeRecipeRepo:

    _filter_tag = ["tags"]

    _filter_tag_not_exists = ["tags_not_exists"]

    _filter_equal = [
        "id",
        "name",
        "meal_id",
        "author_id",
        "total_time",
        "weight_in_grams",
        "privacy",
        "created_at",
        "average_taste_rating",
        "average_convenience_rating",
        "calories",
        "protein",
        "carbohydrate",
        "total_fat",
        "saturated_fat",
        "trans_fat",
        "sugar",
        "sodium",
        "calorie_density",
        "carbo_percentage",
        "protein_percentage",
        "total_fat_percentage",
    ]

    _allowed_filter = _filter_equal + _filter_tag + _filter_tag_not_exists

    def __init__(self):
        self.seen: set[Recipe] = set()
        self._obj: set[Recipe] = set()

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

    async def query(self, filter=None, starting_stmt=None):
        if filter is None:
            return list(self._obj)
        result = []
        filter_tags = filter.pop("tags", None)
        if filter_tags:
            filter_tags = [ApiTag(**tag).to_domain() for tag in filter_tags]
        filter_tags_not_exists = filter.pop("tags_not_exists", None)
        if filter_tags_not_exists:
            filter_tags_not_exists = [
                ApiTag(**tag).to_domain() for tag in filter_tags_not_exists
            ]
        for i in self._obj:
            if getattr(i, "discarded", False):
                continue
            for k, v in filter.items():
                if (
                    k != "author_id"
                    and k.replace("_gte", "").replace("_lte", "")
                    not in FakeRecipeRepo._allowed_filter
                ):
                    break
                # elif k.replace("_gte", "").replace("_lte", "") not in dir(i):
                #     break
                elif k == "author_id":
                    if i.author_id != v:
                        break
                else:
                    if (
                        k.replace("_gte", "").replace("_lte", "")
                        in FakeRecipeRepo._filter_equal
                    ):
                        if "_gte" in k and getattr(i, k.replace("_gte", "")) < v:
                            break
                        elif "_lte" in k and getattr(i, k.replace("_gte", "")) > v:
                            break
                        elif getattr(i, k) != v:
                            break
                    elif k == "tags":
                        if getattr(i, k) is None:
                            break
                        for tag in filter_tags:
                            if tag not in getattr(i, k):
                                break
                    elif k == "tags_not_exists":
                        if getattr(i, k) is None:
                            break
                        for tag in filter_tags_not_exists:
                            if tag in getattr(i, k):
                                break
                    else:
                        if getattr(i, k) is None:
                            break
                        elif v not in getattr(i, k):
                            break
            else:
                result.append(i)
                self.seen.add(i)
        return result

    async def persist(self, obj):
        assert (
            obj in self.seen
        ), "Cannon persist entity which is unknown to the repo. Did you forget to call repo.add() for this entity?"

    async def persist_all(self):
        for obj in self.seen:
            await self.persist(obj)


class FakeTagRepo:
    _filter_equal = [
        "id",
        "key",
        "value",
        "author_id",
        "type",
    ]

    _allowed_filter = _filter_equal

    def __init__(self):
        self.seen: set[Tag] = set()
        self._obj: set[Tag] = set()

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

    async def query(self, filter=None, starting_stmt=None):
        if filter is None:
            return list(self._obj)
        result = []
        for i in self._obj:
            if getattr(i, "discarded", False):
                continue
            for k, v in filter.items():
                if k not in FakeTagRepo._allowed_filter:
                    break
                else:
                    if getattr(i, k) != v:
                        break
            else:
                result.append(i)
                self.seen.add(i)
        return result

    async def persist(self, obj):
        assert (
            obj in self.seen
        ), "Cannon persist entity which is unknown to the repo. Did you forget to call repo.add() for this entity?"

    async def persist_all(self):
        for obj in self.seen:
            await self.persist(obj)


class FakeUnitOfWork:
    def __init__(self):
        self.committed = False
        self.recipes = FakeRecipeRepo()
        self.recipe_tags = FakeTagRepo()

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
