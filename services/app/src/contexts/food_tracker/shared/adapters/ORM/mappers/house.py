from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.associations_tables import (
    HousesMembersAssociation,
    HousesNutritionistsAssociation,
    HousesReceiptsAssociation,
)
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.houses import HouseSaModel
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.receipts import (
    ReceiptSaModel,
)
from src.contexts.food_tracker.shared.domain.entities.house import House
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt
from src.contexts.seedwork.shared.adapters import utils
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class HouseMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: House
    ) -> HouseSaModel:
        receipts = []
        for receipt in domain_obj.pending_receipts:
            a = HousesReceiptsAssociation(state="pending")
            a.receipt = ReceiptSaModel(id=receipt.cfe_key, qrcode=receipt.qrcode)
            receipts.append(a)
        for receipt in domain_obj.added_receipts:
            a = HousesReceiptsAssociation(state="added")
            a.receipt = ReceiptSaModel(id=receipt.cfe_key, qrcode=receipt.qrcode)
            receipts.append(a)
        tasks = [session.merge(i) for i in receipts]
        receipts = await utils.gather_results_with_timeout(
            tasks,
            timeout=5,
            timeout_message="Timeout merging receipts in HouseMapper.map_domain_to_sa",
        )
        sa_obj = HouseSaModel(
            id=domain_obj.id,
            owner_id=domain_obj.owner_id,
            name=domain_obj.name,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            # relationships
            members=[
                HousesMembersAssociation(house_id=domain_obj.id, user_id=i)
                for i in domain_obj.members_ids
            ],
            nutritionists=[
                HousesNutritionistsAssociation(house_id=domain_obj.id, user_id=i)
                for i in domain_obj.nutritionists_ids
            ],
            receipts=receipts,
        )
        return sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: HouseSaModel) -> House:
        house = House(
            id=sa_obj.id,
            owner_id=sa_obj.owner_id,
            name=sa_obj.name,
            members_ids=set([i.user_id for i in sa_obj.members]),
            nutritionists_ids=set([i.user_id for i in sa_obj.nutritionists]),
            pending_receipts=set(
                Receipt(
                    cfe_key=assoc.receipt.id,
                    qrcode=assoc.receipt.qrcode,
                )
                for assoc in sa_obj.receipts
                if assoc.state == "pending"
            ),
            added_receipts=set(
                Receipt(
                    cfe_key=assoc.receipt.id,
                    qrcode=assoc.receipt.qrcode,
                )
                for assoc in sa_obj.receipts
                if assoc.state == "added"
            ),
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
        return house
