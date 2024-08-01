from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.base_class import (
    TagSaModel,
)


class ProcessTypeSaModel(TagSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "process_type",
    }
