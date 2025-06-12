"""
> https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/asyncio_example.py
"""


import uuid
import logging
import asyncio
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

try:
    import confluent_kafka
except ImportError:
    raise ImportError("confluent_kafka is not installed., Please install it using pip insall veronica[kafka]")

from veronica.base.models import DataModel

logger = logging.getLogger(__name__)

__all__ = [
    "AsyncProducer",
    "Producer"
]

@dataclass
class BaseProducer(DataModel):
    """Base producer

    """
    bootstrap_servers: str = "localhost:9092"
    client_id: Optional[str] = None
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = field(default=None, repr=False)


    def  __post_init__(self) -> None:
        if self.client_id is None:
            self.client_id = f"{self.__class__.__name__}_{uuid.uuid4()}"
    
        self._producer = confluent_kafka.Producer(self.to_configs())
        self._cancelled: bool = False
        self._loop:  asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._poll_thread: threading.Thread = threading.Thread(target=self._poll_loop)
        self._poll_thread.start()


    def _poll_loop(self) -> None:
        while not self._cancelled:
            self._producer.poll(timeout=0.1)
            
            
    def close(self) -> None:
        self._cancelled = True
        self._poll_thread.join()
    
    
    @staticmethod
    def on_delivery(
        err: confluent_kafka.KafkaError, 
        msg: confluent_kafka.Message
    ) -> None:
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    

    def to_configs(self) -> dict:
        """Formatting fields to build config for kafka producer

        :return dict: _description_
        """
        return {k.replace("_", "."): v for k, v in self.to_dict(exclude_none=True).items()}
    
    
    def produce(
        self, 
        topic: str, 
        value: str, 
        on_delivery: Optional[Callable[[Any, Any], None]] = None
    ) -> Any:
        raise NotImplementedError


@dataclass
class AsyncProducer(BaseProducer):
    """_summary_

    Notes:
        A produce method in which delivery notifications are made available
        via both the returned future and on_delivery callback (if specified).
    
    :param _type_ BaseProducer: _description_
    """
    def __post_init__(self) -> None:
        super().__post_init__()
        
        self._loop:  asyncio.AbstractEventLoop = asyncio.get_event_loop()
        

    def produce(
        self, 
        topic: str, 
        value: str, 
        on_delivery: Optional[Callable[[Optional[confluent_kafka.KafkaError], Optional[confluent_kafka.Message]], None]] = None
    ):
        """Produces a message to the given topic with a callback
        
        :param str topic: _description_
        :param str value: _description_
        :param Optional[Callable[[Any, Any], None]] on_delivery: _description_, defaults to None
        """
        result = self._loop.create_future()
        def ack(err, msg) -> None:
            if err:
                self._loop.call_soon_threadsafe(
                    result.set_exception, 
                    confluent_kafka.KafkaException(err),
                )
            else:
                self._loop.call_soon_threadsafe(
                    result.set_result,
                    msg,
                )
            if on_delivery:
                self._loop.call_soon_threadsafe(
                    on_delivery,
                    err,
                    msg,
                )
        self._producer.produce(topic, value, on_delivery=ack)
        return result
        
        
@dataclass
class Producer(BaseProducer):
    
    def produce(
        self,
        topic: str,
        value: Any,
        on_delivery: Optional[Callable[[Optional[confluent_kafka.KafkaError], Optional[confluent_kafka.Message]], None]] = None
    ) -> None:
        self._producer.produce(topic, value, on_delivery=on_delivery)