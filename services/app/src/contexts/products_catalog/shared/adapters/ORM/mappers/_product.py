# from src.contexts.products_catalog.shared.adapters.name_search import StrProcessor
# from src.contexts.products_catalog.shared.adapters.ORM.mappers.score import ScoreMapper
# from src.contexts.products_catalog.shared.adapters.ORM.sa_models.is_food_votes import (
#     IsFoodVotesSaModel,
# )
# from src.contexts.products_catalog.shared.adapters.ORM.sa_models.product import (
#     ProductSaModel,
# )
# from src.contexts.products_catalog.shared.domain.entities.product import Product
# from src.contexts.products_catalog.shared.domain.value_objects.is_food_votes import (
#     IsFoodVotes,
# )
# from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
# from src.contexts.shared_kernel.adapters.ORM.mappers.allergen import AllergenMapper
# from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper


# class ProductMapper(ModelMapper):
#     @staticmethod
#     def map_domain_to_sa(domain_obj: Product) -> ProductSaModel:
#         is_food_votes: list[IsFoodVotesSaModel] = []
#         if domain_obj.is_food_votes:
#             is_food_votes: list[IsFoodVotesSaModel] = []
#             for house_id in domain_obj.is_food_votes.is_food_houses:
#                 is_food_votes.append(
#                     IsFoodVotesSaModel(
#                         house_id=house_id,
#                         product_id=domain_obj.id,
#                         is_food=True,
#                     )
#                 )
#             for house_id in domain_obj.is_food_votes.is_not_food_houses:
#                 is_food_votes.append(
#                     IsFoodVotesSaModel(
#                         house_id=house_id,
#                         product_id=domain_obj.id,
#                         is_food=False,
#                     )
#                 )
#         return ProductSaModel(
#             id=domain_obj.id,
#             source_id=domain_obj.source_id,
#             name=domain_obj.name,
#             preprocessed_name=StrProcessor(domain_obj.name).output,
#             brand_id=domain_obj.brand_id,
#             barcode=domain_obj.barcode,
#             is_food=domain_obj.is_food,
#             is_food_houses_choice=domain_obj.is_food_houses_choice,
#             category_id=domain_obj.category_id,
#             parent_category_id=domain_obj.parent_category_id,
#             food_group_id=domain_obj.food_group_id,
#             process_type_id=domain_obj.process_type_id,
#             score=ScoreMapper.map_domain_to_sa(domain_obj.score),
#             ingredients=domain_obj.ingredients,
#             allergens=[
#                 AllergenMapper.map_domain_to_sa(i) for i in domain_obj.allergens
#             ],
#             package_size=domain_obj.package_size,
#             package_size_unit=domain_obj.package_size_unit,
#             image_url=domain_obj.image_url,
#             nutri_facts=NutriFactsMapper.map_domain_to_sa(domain_obj.nutri_facts),
#             json_data=domain_obj.json_data,
#             is_food_votes=is_food_votes,
#             discarded=domain_obj.discarded,
#             version=domain_obj.version,
#         )

#     @staticmethod
#     def map_sa_to_domain(sa_obj: ProductSaModel) -> Product:
#         is_food_votes = IsFoodVotes()
#         for i in sa_obj.is_food_votes:
#             if i.is_food:
#                 is_food_votes.is_food_houses.add(i.house_id)
#             else:
#                 is_food_votes.is_not_food_houses.add(i.house_id)

#         return Product(
#             id=sa_obj.id,
#             source_id=sa_obj.source_id,
#             name=sa_obj.name,
#             brand_id=sa_obj.brand_id,
#             barcode=sa_obj.barcode,
#             is_food=sa_obj.is_food,
#             category_id=sa_obj.category_id,
#             parent_category_id=sa_obj.parent_category_id,
#             food_group_id=sa_obj.food_group_id,
#             process_type_id=sa_obj.process_type_id,
#             diet_types_ids=(
#                 set([i.id for i in sa_obj.diet_types]) if sa_obj.diet_types else set()
#             ),
#             score=ScoreMapper.map_sa_to_domain(sa_obj.score),
#             ingredients=sa_obj.ingredients,
#             allergens=[AllergenMapper.map_sa_to_domain(i) for i in sa_obj.allergens],
#             package_size=sa_obj.package_size,
#             package_size_unit=sa_obj.package_size_unit,
#             image_url=sa_obj.image_url,
#             nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
#             json_data=sa_obj.json_data,
#             is_food_votes=is_food_votes,
#             discarded=sa_obj.discarded,
#             version=sa_obj.version,
#         )
