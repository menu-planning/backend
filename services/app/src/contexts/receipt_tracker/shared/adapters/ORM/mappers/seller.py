from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.seller import (
    SellerSaModel,
)
from src.contexts.receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.domain.value_objects.address import Address


class SellerMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Seller) -> SellerSaModel:
        return SellerSaModel(
            id=str(domain_obj.cnpj),
            name=domain_obj.name,
            state_registration=domain_obj.state_registration,
            street=domain_obj.address.street,
            number=domain_obj.address.number,
            zip_code=domain_obj.address.zip_code,
            district=domain_obj.address.district,
            city=domain_obj.address.city,
            state=domain_obj.address.state,
            complement=domain_obj.address.complement,
            note=domain_obj.address.note,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: SellerSaModel) -> Seller:
        return Seller(
            cnpj=sa_obj.id,
            name=sa_obj.name,
            state_registration=sa_obj.state_registration,
            address=Address(
                street=sa_obj.street,
                number=sa_obj.number,
                zip_code=sa_obj.zip_code,
                district=sa_obj.district,
                city=sa_obj.city,
                state=sa_obj.state,
                complement=sa_obj.complement,
                note=sa_obj.note,
            ),
        )
