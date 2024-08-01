from aio_pika import RobustConnection, connect_robust
from src.rabbitmq.config import rabbitmq_settings


class RobustConnectionMaker:
    _connection: RobustConnection = None

    def __init__(self, rabbitmq_url: str = str(rabbitmq_settings.rabbitmq_url)) -> None:
        self.rabbitmq_url = rabbitmq_url

    async def get_connection(self):
        if not self._connection or self._connection.is_closed:
            self._connection = await connect_robust(self.rabbitmq_url)
            return self._connection
        return self._connection

    async def close_connection(self):
        if self._connection:
            await self._connection.close()


aio_pika_connection = RobustConnectionMaker()
