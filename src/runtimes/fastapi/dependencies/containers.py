from dependency_injector import containers, providers
from src.contexts.recipes_catalog.core.bootstrap.container import Container as RecipesCatalogContainer
from src.contexts.iam.core.bootstrap.container import Container as IAMContainer
from src.contexts.products_catalog.core.bootstrap.container import Container as ProductsCatalogContainer
from src.contexts.client_onboarding.core.bootstrap.container import Container as ClientOnboardingContainer

class AppContainer(containers.DeclarativeContainer):
    iam = providers.Container(IAMContainer)
    recipes = providers.Container(RecipesCatalogContainer)
    products = providers.Container(ProductsCatalogContainer)
    clients = providers.Container(ClientOnboardingContainer)