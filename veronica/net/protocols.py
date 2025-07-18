from __future__ import annotations
import asyncio.trsock
import logging
import asyncio
from functools import cached_property
from typing import (
    final,
    Self,
    Type,
    Callable,
    Optional
)

logger = logging.getLogger(__name__)

__all__ = [
    "ClientProtocol",
    "RetryClientProtocol",
    "Connector",
    "RetryConnector"
]

Address = tuple[str, int]

class ClientProtocol(asyncio.Protocol):
    """Tcp client protocol

    
    """   
    transport: asyncio.Transport | None = None
    connector: Optional["Connector"] = None
    
    @cached_property
    def socket(self) -> asyncio.trsock.TransportSocket:
        """socket

        Raises:
            RuntimeError: _description_

        Returns:
            asyncio.trsock.TransportSocket: _description_
        """
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
        logger.debug(f"{self.remote_address} - Connection made")
        return self.on_connection_made(transport)

    @final
    def data_received(self, data: bytes) -> None:
        """Callback when data is received
        
        #*User should not override this method directly, use `on_data_received` instead

        :param data:
        :return:
        """
        logger.debug(f"{self.remote_address} - RXD < {data.hex(' ')}")
        return self.on_data_received(data)

    @final
    def connection_lost(self, exc: Exception | None) -> None:
        """Callback when connection is lost
        
        #*User should not override this method directly, use `on_connection_lost` instead
 
        :param exc:
        :return:
        """
        assert self.transport is not None
        
        logger.error(f"{self.remote_address} - Connection lost")
        self.transport = None    
        return self.on_connection_lost(exc)
    
    def send(self, data: bytes) -> None:
        """Send data

        :param bytes data: _description_
        :raises RuntimeError: _description_
        """
        if self.transport is None:
            raise RuntimeError("transport is None")
        logger.debug(f"{self.remote_address} - TXD > {data.hex(' ')}")
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


    def on_connection_lost(self, exc: Exception | None) -> None:
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
        loop: asyncio.AbstractEventLoop | None = None
    ) -> None:
        self.host = host
        self.port = port
        self.protocol = protocol
        self.loop = loop or asyncio.get_event_loop()

        self.transport: asyncio.Transport | None = None

    async def connect(self, *, timeout: float | None = None, **kwargs) -> None:
        
        if self.is_connected():
            logger.warning(f"{self.remote_address} - Already connected.")
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
            logger.error(f"{self.remote_address} - Connection refused: {e}")
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
            logger.info(f"{self.remote_address} - Disconnected")


class RetryConnector(Connector):
    
    max_delay: float= 3600.0
    max_retries: int | None = None
    initial_delay: float = 1.0
    
    factor: float = 1.6180339887498948
    jitter: float = 0.119626565582 
    
    delay: float = initial_delay
    retries: int = 0
    continue_trying: bool = True
    
    async def connect(self, *, timeout: float | None = None, **kwargs) -> None:
        try:
            await super().connect(timeout=timeout, **kwargs)
            self.retdelay()
        except ConnectionRefusedError:
            self.retry()
            
    def retdelay(self) -> None:
        self.delay = self.initial_delay
        self.retries = 0
        self.continue_trying = True
    def disconnect(self) -> None:
        
        if not self.is_connected():
            raise RuntimeError("no connection")
        elif self.transport is not None:
            self.transport.close()
            self.transport = None
            logger.info(f"{self.remote_address} - Disconnected")
    
    def retry(self) -> None:
        
        if not self.continue_trying:
            logger.info(f"{self.remote_address} - Abandoning on explicit request")
            return
        
        self.retries += 1
        if self.max_retries is not None and (self.retries > self.max_retries):
            logger.warning(f"{self.remote_address} - Abandoning after {self.retries} retries")
            return
        
        self.delay = min(self.delay * self.factor, self.max_delay)
        if self.jitter is not None:
            import random
            self.delay = random.normalvariate(self.delay, self.delay * self.jitter)
        
        self.loop.call_later(
            self.delay,
            lambda: asyncio.create_task(self.connect())
        )    
        logger.debug(f"{self.remote_address} - will retried in {self.delay} s")
    
    