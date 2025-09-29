from fastapi import Request
from src.contexts.shared_kernel.services.messagebus import MessageBus

def get_recipes_bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.container.recipes.bus_factory()  # new bus per request
    bus.spawn_fn = request.app.state.spawn
    if getattr(request.app.state, "bg_limiter", None):
        bus.handler_limiter = request.app.state.bg_limiter
    return bus
