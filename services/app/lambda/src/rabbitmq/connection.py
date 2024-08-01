from aio_pika import RobustConnection, connect_robust
from src.rabbitmq.config import rabbitmq_settings

# class _AIOPikaRobustConnection:
#     def __init__(self, rabbitmq_url: str = rabbitmq_settings.rabbitmq_url) -> None:
#         self.rabbitmq_url = rabbitmq_url

#     async def _init(self):
#         self.connection = await connect_robust(self.rabbitmq_url)


# class AIOPikaRobustConnection(_AIOPikaRobustConnection, metaclass=Singleton):
#     pass


# async_db = AsyncDatabase()


# async def create_connection(rabbitmq_url: str = rabbitmq_settings.rabbitmq_url):
#     conn = AIOPikaRobustConnection(rabbitmq_url)
#     await conn._init()
#     return conn


# class RobustConnectionMaker:
#     def __init__(self, rabbitmq_url: str = str(rabbitmq_settings.rabbitmq_url)):
#         self.rabbitmq_url = rabbitmq_url
#         self._connection: RobustConnection | None = None

#     async def __aenter__(self):
#         if not self._connection or self._connection.is_closed:
#             self._connection = await connect_robust(self.rabbitmq_url)
#         return self._connection

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if self._connection:
#             await self._connection.close()
#             self._connection = None


class RobustConnectionMaker:
    _connection: RobustConnection = None
    # event: Event = None

    def __init__(self, rabbitmq_url: str = str(rabbitmq_settings.rabbitmq_url)) -> None:
        self.rabbitmq_url = rabbitmq_url

    # def reconnection_callback(self, *_):
    #     self.event.set()
    #     self.event = Event()

    async def get_connection(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await connect_robust(self.rabbitmq_url)
            return self._connection
        return self._connection
        # if self._connection and self._connection.reconnecting:
        #     await self.event.wait()
        #     assert self._connection.is_closed is False
        #     return self._connection
        # else:
        #     self._connection = await connect_robust(self.rabbitmq_url)
        #     self.event = Event()
        #     self._connection.reconnect_callbacks.add(self.reconnection_callback)
        #     return self._connection

    async def close_connection(self):
        if self._connection:
            await self._connection.close()


aio_pika_connection = RobustConnectionMaker()
