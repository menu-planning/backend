import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.shared.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class IsFoodVotesMapper(ModelMapper):

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: IsFoodVotes, prodcut_id: int
    ) -> IsFoodVotesSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. The user
        can create a new vote, so we need to check if the product
        vote for that house already exists in the database. If it
        does, we update
        the existing object. If it doesn't, we create a new object.

        """
        tasks = [
            utils.get_sa_entity(
                session=session,
                sa_model_type=IsFoodVotesSaModel,
                filter={"house_id": i, "product_id": prodcut_id},
            )
            for i in domain_obj.house_ids
        ]
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=IsFoodVotesSaModel,
            filter={"house_id": domain_obj.id},
        )
        if existing_sa_obj:
            new_sa_obj = DietTypeSaModel(
                id=domain_obj.id,
                name=domain_obj.name,
                author_id=domain_obj.author_id,
                description=domain_obj.description,
                privacy=domain_obj.privacy.value,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
            await session.merge(new_sa_obj)
            return new_sa_obj
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: IsFoodVotesSaModel) -> IsFoodVotes:
        return IsFoodVotes(
            id=sa_obj.id,
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            description=sa_obj.description,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
