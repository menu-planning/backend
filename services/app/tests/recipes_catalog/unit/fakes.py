from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.entities.tags import (
    Category,
    MealPlanning,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


class FakeRecipeRepo:
    _referenced_by_id = {
        "diet_types": "diet_types_ids",
        "categories": "categories_ids",
        "cuisine": "cuisine_id",
        "flavor": "flavor",
        "texture": "texture",
        "meal_planning": "meal_planning_ids",
    }

    _filter_in = ["diet_types", "categories", "meal_planning", "season"]

    _filter_equal = [
        "id",
        "name",
        "author_id",
        "total_time",
        "is_reheatable",
        "privacy",
        "created_at",
        "average_taste_rating",
        "average_convenience_rating",
        "cuisine",
        "flavor_profile",
        "texture_profile",
    ]

    _allowed_filter = _filter_equal + _filter_in

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
                    else:
                        key = FakeRecipeRepo._referenced_by_id.get(k, k)
                        if getattr(i, key) is None:
                            break
                        elif v not in getattr(i, key):
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
        "name",
        "author_id",
        "privacy",
    ]

    _allowed_filter = _filter_equal

    def __init__(self, domain_model_type: type[Tag]):
        self.seen: set[domain_model_type] = set()
        self._obj: set[domain_model_type] = set()

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
        self.diet_types = FakeTagRepo(DietType)
        self.categories = FakeTagRepo(Category)
        self.cuisine = FakeTagRepo(Cuisine)
        self.flavor = FakeTagRepo(Flavor)
        self.texture = FakeTagRepo(Texture)
        self.meal_planning = FakeTagRepo(MealPlanning)

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
