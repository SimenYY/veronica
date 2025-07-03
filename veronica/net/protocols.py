import asyncio.trsock
import logging
import asyncio
from functools import cached_property
from typing import (
    Optional,
    Tuple,
    final,
    Self,
    Type
)

logger = logging.getLogger(__name__)

__all__ = [
    "ClientProtocol",
    "RetryClientProtocol",
    "Connector",
    "RetryConnector"
]

Address = Tuple[str, int]

class ClientProtocol(asyncio.Protocol):
    """Interface for stream protocol

    Args:
        asyncio (_type_): _description_

    Returns:
        _type_: _description_
    """   
    transport: Optional[asyncio.Transport] = None
    connector: Optional["Connector"] = None
    
    @cached_property
    def socket(self) -> asyncio.trsock.TransportSocket:
        if self.transport is None:
            raise RuntimeError("transport is None")
        
        return self.transport.get_extra_info("socket")
    
    @cached_property
    def local_address(self) -> Address:
        """local address

        Returns:
            Address: _description_
        """
        if self.transport is None:
            raise RuntimeError("transport is None")
        return self.transport.get_extra_info("sockname")
    
    @cached_property
    def remote_address(self) -> Address:
        """remote address

        Returns:
            Tuple[str, int]: _description_
        """
        if self.transport is None:
            raise RuntimeError("transport is None")
        
        return self.transport.get_extra_info("peername")

    @final
    def connection_made(self, transport: asyncio.Transport) -> None:
        """ Callback when connection is made
        
        #*User should not override this method directly, use `on_connection_made` instead
        
        :param transport:
        :return:
        """
        self.transport = transport
        logger.debug(f"Successfully connected to {self.remote_address}")
        return self.on_connection_made(transport)

    @final
    def data_received(self, data: bytes) -> None:
        """Callback when data is received
        
        #*User should not override this method directly, use `on_data_received` instead

        :param data:
        :return:
        """
        logger.debug(f"Received data from {self.remote_address}: {data.hex(' ')}")
        return self.on_data_received(data)

    @final
    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Callback when connection is lost
        
        #*User should not override this method directly, use `on_connection_lost` instead
 
        :param exc:
        :return:
        """
        assert self.transport is not None
        
        logger.error(f"Disconnected from {self.remote_address}")
        self.transport = None    
        return self.on_connection_lost(exc)
    
    def send(self, data: bytes) -> None:
        """Send data

        :param bytes data: _description_
        :raises RuntimeError: _description_
        """
        if self.transport is None:
            raise RuntimeError("transport is None")
        logger.debug(f"Send data to {self.remote_address}: {data.hex(' ')}")
        self.transport.write(data)
    
    @classmethod
    def build(cls, connector: "Connector") -> Self:
        p = cls()
        p.connector = connector
        return p
    
    def on_connection_made(self, transport: asyncio.Transport) -> None:
        """callback when connection is made

        Args:
            transport (asyncio.Transport): _description_
        """


    def on_data_received(self, data: bytes) -> None:
        """callback when data is received

        Args:
            data (bytes): _description_
        """


    def on_connection_lost(self, exc: Optional[Exception]) -> None:
        """callback when connection is lost

        Args:
            exc (Optional[Exception]): _description_

        Raises:
            e: _description_
            RuntimeError: _description_

        Returns:
            _type_: _description_s
        """
            
class RetryClientProtocol(ClientProtocol):
    """Support for retrying connection

    Args:
        ClientProtocol (_type_): _description_
    """
    
    def on_connection_lost(self, exc: Exception | None) -> None:
        assert isinstance(self.connector, RetryConnector)
        if self.connector.continue_trying:
            self.connector.retry()


class Connector:
    def __init__(
        self,
        host: str,
        port: int,
        protocol: Type[ClientProtocol],
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

        self.transport: Optional[asyncio.Transport] = None

    async def connect(self, *, timeout: float | None = None, **kwargs) -> None:
        
        if self.is_connected():
            logger.warning("Already connected.")
            return
        
        assert self.loop is not None
        
        try:
            transport, protocol = await asyncio.wait_for(
                self.loop.create_connection(
                    lambda: self.protocol.build(self),
                    self.host,
                    self.port,
                    **kwargs,
                ), 
                timeout
            )
            self.transport = transport
        except ConnectionRefusedError as e:
            logger.error(f"Failed to connect to {self.remote_address}: {e}")
            raise e
    @cached_property
    def remote_address(self) -> Address:
        return (self.host, self.port)
    
    def is_connected(self) -> bool:
        if self.transport is None:
            return False
        elif self.transport.is_closing():
            return False
        else:
            return True

    def disconnect(self) -> None:
        
        if not self.is_connected():
            raise RuntimeError("no connection")
        elif self.transport is not None:
            self.transport.close()
            self.transport = None
            logger.info(f"Successfully disconnected from {self.remote_address}")


class RetryConnector(Connector):
    
    max_delay: float= 3600.0
    max_retries: Optional[int] = None
    initial_delay: float = 1.0
    
    factor: float = 1.6180339887498948
    jitter: float = 0.119626565582 
    
    def __init__(
        self,
        host: str,
        port: int,
        protocol: Type[ClientProtocol],
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        super().__init__(host, port, protocol, loop)
        
        self.delay: float = self.initial_delay
        self.retries: int = 0
        self.continue_trying: bool = True
    
    async def connect(self, *, timeout: float | None = None, **kwargs) -> None:
        try:
            await super().connect(timeout=timeout, **kwargs)
            self.retdelay()
        except ConnectionRefusedError:
            self.retry()
            
    def retdelay(self) -> None:
        self.delay = self.initial_delay
    def disconnect(self) -> None:
        
        if not self.is_connected():
            raise RuntimeError("no connection")
        elif self.transport is not None:
            self.transport.close()
            self.transport = None
            logger.info(f"Successfully disconnected from {self.remote_address}")
    
    def retry(self) -> None:
        
        if not self.continue_trying:
            logger.info(f"Abandoning {self.remote_address} on explicit request")
            return
        
        self.retries += 1
        if self.max_retries is not None and (self.retries > self.max_retries):
            logger.warning(f"Abandoning {self.remote_address} after {self.retries} retries")
            return
        
        self.delay = min(self.delay * self.factor, self.max_delay)
        if self.jitter is not None:
            import random
            self.delay = random.normalvariate(self.delay, self.delay * self.jitter)
        
        self.loop.call_later(
            self.delay,
            lambda: asyncio.create_task(self.connect())
        )    
        logger.debug(f"Server{self.remote_address} will retried in {self.delay} s")
    