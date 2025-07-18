import asyncio
import logging
from typing import Self, final
from veronica.core.log import PrefixLoggerAdapter

logger = logging.getLogger(__name__)


Address = tuple[str, int]


class TcpProtocol(asyncio.Protocol):
    """Tcp protocol

    为了给回调事件增加固定的处理以及日志的记录，使用`on_xxx`开头的方法来解耦，处理回调事件
    
    在协议活动中记录日志，建议使用协议自带的`protocol_logger`记录，自带远端地址
    
    Args:
        transport: (asyncio.Transport): 传输对象
    

    """
    
    transport: asyncio.Transport | None
    local_address: Address | None 
    remote_address: Address | None
    protocol_logger: logging.Logger | logging.LoggerAdapter
    def __init__(self):
        self.transport = None
        self.local_address = None
        self.remote_address = None
        self.protocol_logger = logger
    @final
    def connection_made(self, transport: asyncio.Transport) -> None:
        """ Callback when connection is made
        
        #* 用户须使用`on_connection_made`方法代替本方法
        
        Args:
            transport (asyncio.Transport): _description_
        """
        self.transport = transport
        self.local_address = transport.get_extra_info("sockname")
        self.remote_address = transport.get_extra_info("peername")
        global logger
        self.protocol_logger=PrefixLoggerAdapter(logger, prefix=str(self.remote_address))
        self.protocol_logger.info("Connection made")
        return self.on_connection_made()

    @final
    def data_received(self, data: bytes) -> None:
        """Callback when data is received
        
        #* 用户须用`on_data_received`方法代替本方法

        Returns:
            _type_: _description_
        """
        self.protocol_logger.debug(f"RXD < {data.hex(' ')}")
        
        return self.on_data_received(data)
    
    @final
    def connection_lost(self, exc: Exception | None) -> None:
        """Callback when connection is lost
        
        #* 用户须用`on_connection_lost`方法代替本方法
 

        Returns:
            _type_: _description_
        """
        self.protocol_logger.error(f"Connection lost, exc: {exc}")
        
        self.transport = None
        
        return self.on_connection_lost(exc)
    
    def on_data_received(self, data: bytes) -> None:
        """Callback when data is received

        Args:
            data (bytes): _description_
        """
        pass
    
    def on_connection_lost(self, exc: Exception | None) -> None:
        """Callback when connection is lost

        Args:
            exc (Exception | None): _description_
        """
        pass
    
    def on_connection_made(self) -> None:
        """Callback when connection is made
        """
        pass
    
    def transmit_data(self, data: bytes) -> None:
        """主动发送数据

        Args:
            data (bytes): 需要发送的数据
        """
        assert self.transport is not None, (
            "transport is None"
        )
        self.transport.write(data)
        self.protocol_logger.debug(f"TXD > {data.hex(' ')}")
        
    @classmethod
    def build(cls) -> Self:
        
        p = cls()
        
        return p
    

