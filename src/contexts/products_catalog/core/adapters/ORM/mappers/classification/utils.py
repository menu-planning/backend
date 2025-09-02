"""Shared helpers to map classification domain entities to/from SA models.

Provides generic mapping functions for classification entities that follow
the same pattern for domain-to-SA and SA-to-domain conversions.
"""
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)


def classification_map_domain_to_sa[S: ClassificationSaModel](
    domain_obj: Classification,
    sa_model_type: type[S],
    polymorphic_identity: str,
) -> S:
    """Map classification domain object to SQLAlchemy model.
    
    Args:
        domain_obj: Domain classification object.
        sa_model_type: SQLAlchemy model type to create.
        polymorphic_identity: Polymorphic identity for the model.
        
    Returns:
        SQLAlchemy model instance.
    """
    return sa_model_type(
        type=polymorphic_identity,
        id=domain_obj.id,
        name=domain_obj.name,
        author_id=domain_obj.author_id,
        description=domain_obj.description,
        created_at=domain_obj.created_at,
        updated_at=domain_obj.updated_at,
        discarded=domain_obj.discarded,
        version=domain_obj.version,
    )


def classification_map_sa_to_domain[C: Classification](
    sa_obj: ClassificationSaModel,
    domain_obj_type: type[C],
) -> C:
    """Map SQLAlchemy classification model to domain object.
    
    Args:
        sa_obj: SQLAlchemy classification model instance.
        domain_obj_type: Domain object type to create.
        
    Returns:
        Domain classification object.
    """
    return domain_obj_type(
        entity_id=sa_obj.id,
        name=sa_obj.name,
        author_id=sa_obj.author_id,
        description=sa_obj.description,
        created_at=sa_obj.created_at,
        updated_at=sa_obj.updated_at,
        discarded=sa_obj.discarded,
        version=sa_obj.version,
    )
