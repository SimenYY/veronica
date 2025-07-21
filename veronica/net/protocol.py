import logging
import asyncio
from typing import final, cast

logger = logging.getLogger(__name__)

class TcpClientProtocol(asyncio.Protocol):

    def __init__(self, on_lost_fut: asyncio.Future) -> None:
        self.on_lost_fut = on_lost_fut
        self._transport: asyncio.Transport | None = None
        self._loop = asyncio.get_running_loop()
    
    @final
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """连接建立时回调

        Args:
            transport (asyncio.BaseTransport): 传输对象

        """
        logger.info("connection made")
        self._transport = cast(asyncio.Transport, transport)
        return self.on_connection_made()
    
    @final
    def data_received(self, data: bytes) -> None:
        """数据接收时回调

        Args:
            data (bytes): 接收到的数据
        """
        pass
    
    @final
    def connection_lost(self, exc: Exception | None) -> None:
        """连接丢失时回调

        Args:
            exc (Exception | None): 如果时None，则表示主动断开，否则含有异常信息
        """
        logger.debug("connection lost")
        # 主动调用transport.close()时，也会调用connection_lost, 此时exc为None，该
        # 情况下，不触发重连
        self._transport = None
        
        if exc is not None:
            self.on_lost_fut.set_result(True)
        
        return self.on_connection_lost()
    
    @property
    def is_connected(self) -> bool:
        """判断是否连接

        Returns:
            bool: 连接状态
        """
        return self._transport is not None and not self._transport.is_closing()

    def transmit_data(self, data: bytes) -> None:
        """发送数据

        Args:
            data (bytes): 需要发送的数据

        Raises:
            ConnectionError: transpost 不存在或者正在关闭
        """
        if self.is_connected:
            self._transport.write(data)
        else:
            raise ConnectionError("Transport can't be used")

    def on_connection_made(self) -> None:
        """连接建立时回调，用户调用
        """
        pass
    
    def on_data_received(self, data: bytes) -> None:
        """数据接收时回调，用户调用

        Args:
            data (bytes): _description_
        """
        pass
    
    def on_connection_lost(self) -> None:
        """连接丢失时回调，用户调用
        """
        pass