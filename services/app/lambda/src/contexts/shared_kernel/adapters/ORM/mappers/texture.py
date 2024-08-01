from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.texture import TextureSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


class TextureMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Texture) -> TextureSaModel:
        return TextureSaModel(
            id=domain_obj.name,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: TextureSaModel) -> Texture:
        return Texture(
            name=sa_obj.id,
        )
