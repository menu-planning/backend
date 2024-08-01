from src.contexts.nutrition_assessment_and_planning.modules.common.value_objects import (
    Contact,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper

from ..domain.entities import Nutritionist
from ..domain.value_objects import CRN, CRNRegion
from .nutritionist_repository import NutritionistSaModel


class NutritionistMapper(ModelMapper):
    def map_domain_to_sa(self, domain_obj: Nutritionist) -> NutritionistSaModel:
        return NutritionistSaModel(
            id=domain_obj.id,
            login_email=domain_obj.email,
            full_name=domain_obj.full_name,
            default_email=domain_obj.contact.default_email,
            emails=domain_obj.contact.emails,
            default_phone=domain_obj.contact.default_phone,
            phones=domain_obj.contact.phones,
            default_address=domain_obj.contact.default_address,
            addresses=domain_obj.contact.addresses,
            crn_number=domain_obj.crn.number,
            crn_state=domain_obj.crn.region,
            patients=domain_obj.patients,
            houses=domain_obj.houses,
            pending_house_invitations=domain_obj.house_invitations,
            products_notes=domain_obj.products_notes.values(),
            brands_notes=domain_obj.brands_notes.values(),
        )

    def map_sa_to_domain(self, sa_obj: NutritionistSaModel) -> Nutritionist:
        return Nutritionist(
            id=sa_obj.id,
            email=sa_obj.login_email,
            full_name=sa_obj.full_name,
            contact=Contact(
                default_email=sa_obj.default_email,
                emails=sa_obj.emails,
                default_phone=sa_obj.default_phone,
                phones=sa_obj.phones,
                default_address=sa_obj.default_address,
                addresses=sa_obj.addresses,
            ),
            crn=CRN(number=sa_obj.crn_number, region=CRNRegion(sa_obj.crn_state)),
            patients=sa_obj.patients,
            houses=sa_obj.houses,
            house_invitations=sa_obj.pending_house_invitations,
            products_notes={note.product_id: note for note in sa_obj.products_notes},
            brands_notes={note.brand: note for note in sa_obj.brands_notes},
        )
