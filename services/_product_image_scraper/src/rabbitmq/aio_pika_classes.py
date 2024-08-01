from aio_pika.abc import ExchangeParamType, ExchangeType, TimeoutType
from attrs import define, field
from pamqp.common import Arguments

all_aio_pika_data: list["AIOPikaData"] = []


@define
class AIOPikaChannelData:
    channel_number: int | None = None
    publisher_confirms: bool = True
    on_return_raises: bool = False


@define
class SetQOSData:
    prefetch_count: int = 0
    prefetch_size: int = 0
    global_: bool = False
    timeout: TimeoutType = None
    all_channels: bool | None = None


@define
class AIOPikaExchangeData:
    name: str
    type: ExchangeType | str = ExchangeType.DIRECT
    durable: bool = False
    auto_delete: bool = False
    internal: bool = False
    passive: bool = False
    arguments: Arguments = None


@define
class AIOPikaQueueData:
    name: str | None = None
    durable: bool = False
    exclusive: bool = False
    passive: bool = False
    auto_delete: bool = False
    arguments: Arguments = None


@define
class AIOPikaQueueBindData:
    exchange: ExchangeParamType
    routing_key: str | None = None
    # arguments: Arguments = None
    # timeout: TimeoutType = None


@define
class AIOPikaData:
    # channel_name: str
    queue: AIOPikaQueueData
    # channel: AIOPikaChannelData | None = None
    unique_id: str = field(init=False)
    set_qos: SetQOSData | None = None
    exchange: AIOPikaExchangeData | None = None
    queue_bind: AIOPikaQueueBindData | None = None
    dl_queue: AIOPikaQueueData | None = None
    dl_exchange: AIOPikaExchangeData | None = None
    dl_queue_bind: AIOPikaQueueBindData | None = None

    def __attrs_post_init__(self):
        all_aio_pika_data.append(self)
        self.unique_id = self.queue.name
