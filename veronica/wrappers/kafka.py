import uuid
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field, asdict

try:
    from confluent_kafka import Producer
except ImportError:
    raise ImportError("confluent_kafka is not installed., Please install it using pip insall veronica[kafka]")

logger = logging.getLogger(__name__)

__all__ = [
    "KafkaProducer"
]

@dataclass
class KafkaProducer:
    """kafka producer
    
    Notes:
        bootstrap_servers format: host1:port1,host2:port2,host3:port3
    """
    bootstrap_servers: str = "localhost:9092"
    client_id: Optional[str] = None
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = field(default=None, repr=False)
    def __post_init__(self) -> None:
        if self.client_id is None:
            self.client_id = f"{self.__class__.__name__}_{uuid.uuid4()}"
        
        self.producer = Producer(self._Format_fields(), logger=logger)
    def produce(
        self, 
        topic: str, 
        value: str, 
        callback: Optional[Callable[[Any, Any], None]] = None
    ) -> None:
        """Produces a message to the given topic

        :param str topic: _description_
        :param str value: _description_
        :param Optional[Callable[[Any, Any], None]] callback: _description_, defaults to None
        """
        _callback = callback
        if callback is None:
            def delivery_report(err, msg):
                if err is not None:
                    logger.error(f"Message delivery failed: {err}")
                else:
                    logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
            _callback = delivery_report   
            
        self.producer.produce(topic, value, callback=_callback)
        self.producer.poll(0)
    
    def to_dict(self, exclude_none: bool = False) -> dict:
        if exclude_none:
            return {k: v for k, v in asdict(self).items() if v is not None}
        return asdict(self)

    def _Format_fields(self) -> dict:
        """Formatting fields to build config for kafka producer

        :return dict: _description_
        """
        return {k.replace("_", "."): v for k, v in self.to_dict(exclude_none=True).items()}