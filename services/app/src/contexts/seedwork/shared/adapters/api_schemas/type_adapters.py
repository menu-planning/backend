from pydantic import TypeAdapter

from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole

# Create type adapter for roles collection
RoleSetAdapter = TypeAdapter(set[ApiSeedRole])