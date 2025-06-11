import asyncio
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import (
    Optional,
    Tuple,
    final,
    Callable,
    Dict,
    Final,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BaseFactory",
    "ClientFactory",
    "ClientProtocol",
    "Connector",
]


Address = Tuple[str, int]

@dataclass
class Connector:
    """connect and disconnect

    :raises RuntimeError: _description_
    :return _type_: _description_
    """
    
    host: str
    port: int
    factory: "BaseFactory"
    loop: Optional[asyncio.AbstractEventLoop] = None

    _transport: Optional[asyncio.Transport] = None
    
    def __post_init__(self) -> None:
        
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
    @property
    def address(self) -> Address:
        return (self.host, self.port)
    
    async def connect(self, retry: bool = False, **kwargs) -> None:
        
        if self.is_connected():
            logger.warning("Already connected.")
            return
        
        if self._transport is not None:
            print(self._transport.is_closing())
        
        if self.loop is None:
            raise RuntimeError("Event loop is not available")
        
        try:
            self._transport, _ = await self.loop.create_connection(
                lambda: self.factory.build_protocol(self),
                self.host,
                self.port,
                **kwargs,
            )
        except ConnectionRefusedError as e:
            logger.error(f"Failed to connect to {self.address}: {e}")
            if retry:
                self.factory.retry(self)
            else:
                raise e
    def disconnect(self) -> None:
        
        if not self.is_connected():
            raise RuntimeError("no connection")
        elif self._transport is not None:
            self._transport.close()
            self._transport = None
            logger.info(f"Successfully disconnected from {self.address}")

    def is_connected(self) -> bool:
        if self._transport is None:
            return False
        elif self._transport.is_closing():
            return False
        else:
            return True
    
    
    def connect_later(
        self, 
        *, 
        delay: float, 
        retry: bool = False, 
        **kwargs
    ) -> asyncio.TimerHandle:
        
        assert self.loop is not None
        return self.loop.call_later(delay, lambda: asyncio.create_task(self.connect(retry, **kwargs)))
    
    def disconnect_later(self, delay: float) -> asyncio.TimerHandle:
        assert self.loop is not None
        return self.loop.call_later(delay, self.disconnect)
    
    
@dataclass
class ClientProtocol(asyncio.Protocol):
    """Communication and exchange for Tcp

    :param _type_ asyncio: _description_
    :raises RuntimeError: _description_
    :raises RuntimeError: _description_
    :raises NotImplementedError: _description_
    :raises NotImplementedError: _description_
    :raises NotImplementedError: _description_
    :return _type_: _description_
    """

    transport: Optional[asyncio.Transport] = None
    connector: Optional[Connector] = None
    @final
    def connection_made(self, transport: asyncio.Transport) -> None:
        """ Callback when connection is made
        
        #*User should not override this method directly, use `on_connection_made` instead
        
        :param transport:
        :return:
        """
        self.transport = transport
        logger.debug(f"Successfully connected to {self.transport.get_extra_info("peername")}")
        return self.on_connection_made(transport)

    @final
    def data_received(self, data: bytes) -> None:
        """Callback when data is received
        
        #*User should not override this method directly, use `on_data_received` instead

        :param data:
        :return:
        """
        return self.on_data_received(data)

    @final
    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Callback when connection is lost
        
        #*User should not override this method directly, use `on_connection_lost` instead
 
        :param exc:
        :return:
        """
        assert self.transport is not None
        logger.error(f"Disconnected from {self.transport.get_extra_info("peername")}")
        self.transport = None        
        self.on_connection_lost(exc)

        assert self.connector is not None
        self.connector.factory.on_connection_lost(self.connector, exc)
        
    def send(self, data: bytes) -> None:
        """Send data

        :param bytes data: _description_
        :raises RuntimeError: _description_
        """
        if self.transport is None:
            raise RuntimeError("transport is None")
        
        self.transport.write(data)
    
    
    def on_connection_made(self, transport: asyncio.Transport) -> None:
        raise NotImplementedError


    def on_data_received(self, data: bytes) -> None:
        raise NotImplementedError


    def on_connection_lost(self, exc: Optional[Exception]) -> None:
        raise NotImplementedError
    
    
class BaseFactory(ABC):
    """abstract factory
    """
    protocol: Optional[Callable[[], asyncio.Protocol]] = None
    
    @classmethod
    def for_protocol(cls, protocol: Callable[[], asyncio.Protocol], *args, **kwargs):
        """Create a factory for the given protocol

        :param Callable[[], asyncio.Protocol] protocol: _description_
        :return _type_: _description_
        """
        factory = cls(*args, **kwargs)
        factory.protocol = protocol
        return factory

    @abstractmethod
    def build_protocol(self, connector: Connector) -> asyncio.Protocol:
        """build a protocol instance
        
        :param Connector connector: _description_
        :return asyncio.Protocol: _description_
        """
        ...
    @abstractmethod
    def retry(self, connector: Connector) -> None:
        """retry  to connect

        :param Connector connector: _description_
        """
        ...
        
    @abstractmethod
    def on_connection_lost(self, connector: Connector, exc: Optional[Exception]) -> None:
        """callback when connect lost

        :param Connector connector: _description_
        :param Optional[Exception] exc: _description_
        """
        ...
        

    


@dataclass
class _RetryState:

    delay: float
    retries: int
    continue_trying: bool
        

class ClientFactory(BaseFactory):
    
    protocol: Optional[Callable[[], ClientProtocol]] = None
    registry: Dict[Address, _RetryState] = {}
    

    max_delay: float= 3600.0
    max_retries: Optional[int] = None
    initial_delay: float = 1.0
    
    factor: Final[float] = 1.6180339887498948
    jitter: Final[float] = 0.119626565582 
 
    def build_protocol(self, connector: Connector) -> ClientProtocol:

        assert self.protocol is not None
        logger.debug(f"Building protocol for {connector.address}")
        p = self.protocol()
        p.connector = connector
        self.registor(connector.address, reset=True)
        return p
    
    def registor(self, address: Address, *, reset: bool = False) -> None:
        """registor address to registry

        :param Address address: _description_
        :param bool reset: _description_, defaults to False
        """
        
        if not self.is_registored(address): 
            self.registry[address] = _RetryState(
                delay=self.initial_delay,
                retries=0,
                continue_trying=True
            )
        else:
            if reset:
                self.registry[address].continue_trying = True
                self.registry[address].retries = 0
                self.registry[address].delay = self.initial_delay
        

    def is_registored(self, address: Address) -> bool:
        return address in self.registry
    
    def on_connection_lost(self, connector: Connector, exc: Optional[Exception]) -> None:

        assert self.is_registored(connector.address)
        
        retry_state = self.registry[connector.address]
        if retry_state.continue_trying:
            self.retry(connector)
    def retry(self, connector: Connector) -> None:
        
        # First connection
        self.registor(connector.address)    
        
        retry_state = self.registry[connector.address]
        
        if not retry_state.continue_trying: 
            logger.info(f"Abandoning {connector.address} on explicit request")
            return
        
        retry_state.retries += 1
        if self.max_retries is not None and (retry_state.retries > self.max_retries):
            logger.warning(f"Abandoning {connector.address} after {retry_state.retries} retries.")
            return
        
        retry_state.delay = min(retry_state.delay * self.factor, self.max_delay)
        if self.jitter is not None:
            import random
            retry_state.delay = random.normalvariate(retry_state.delay, retry_state.delay * self.jitter)
        
        connector.connect_later(delay=retry_state.delay, retry=True)
        logger.debug(f"Server{connector.address} will retried in {retry_state.delay} s")    

