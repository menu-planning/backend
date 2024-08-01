from __future__ import annotations

from src.config.app_config import app_settings
from src.db.base import Database

from ..adapters.nutritionist_repository import NutritionistRepo

db_url = app_settings.sqlalchemy_db_uri

db = Database(db_url)
session_factory = db.session_factory


class UnitOfWork:
    def __init__(self, session_factory=session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.nutritionists = NutritionistRepo(self.session)
        return self

    def __exit__(self, *args):
        self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def collect_new_events(self):
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if hasattr(attr, "seen"):
                for obj in getattr(attr, "seen"):
                    if hasattr(obj, "events"):
                        while getattr(obj, "events"):
                            yield getattr(obj, "events").pop(0)

    def rollback(self):
        self.session.rollback()
