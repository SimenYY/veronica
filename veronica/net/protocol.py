import logging
import asyncio
from typing import final, cast
from veronica.core.log import PrefixLoggerAdapter

logger = logging.getLogger(__name__)

class TCPClientProtocol(asyncio.Protocol):
    """TCP 客户端协议类
    
    核心功能包括：自定义协议开发、自动重连机制、简单定时任务（使用call_later)

    Attributes:
        _on_lost_fut (asyncio.Future): 连接丢失的 Future 对象
        _loop (asyncio.AbstractEventLoop): 事件循环
        _transport (asyncio.Transport): 传输对象
        _peername (tuple[str, int] | None): 连接的远程地址
        log (PrefixLoggerAdapter): 日志适配器
    """
    def __init__(
        self, 
        on_lost_fut: asyncio.Future | None = None,
        loop: asyncio.AbstractEventLoop | None = None
    ) -> None:
        self._on_lost_fut = on_lost_fut
        self._transport: asyncio.Transport | None = None
        self._loop = loop or asyncio.get_running_loop()
        self._peername: tuple[str, int] | None = None 
        self.log: PrefixLoggerAdapter = PrefixLoggerAdapter(logger)
    @final
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """连接建立时回调

        Args:
            transport (asyncio.BaseTransport): 传输对象

        """

        self._transport = cast(asyncio.Transport, transport)
        self._peername = transport.get_extra_info("peername")
        assert self._peername is not None
        self.log = PrefixLoggerAdapter(logger, prefix=str(list(self._peername)))
        self.log.info("Connection made")
        return self.on_connection_made()
    
    @final
    def data_received(self, data: bytes) -> None:
        """数据接收时回调

        Args:
            data (bytes): 接收到的数据
        """
        self.log.debug(f"RXD << {data.hex(' ')}") 
        return self.on_data_received(data)
    
    @final
    def connection_lost(self, exc: Exception | None) -> None:
        """连接丢失时回调

        Args:
            exc (Exception | None): 如果时None，则表示主动断开，例如transport.close()，否则含有异常信息
        """
        # exc为None的三种情况：1. 主动断开，例如transport.close()，2. 对端关闭端口，3对端主动断开客户端
        self.log.error(f"Connection lost: {exc}")
        
        on_lost_fut = self._on_lost_fut
        if on_lost_fut is not None and not on_lost_fut.cancelled(): 
            on_lost_fut.set_result(True)
            self._on_lost_fut = None
            
        self._transport = None
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
            assert self._transport is not None
            self._transport.write(data)
            self.log.debug(f"TXD >> {data.hex(' ')}")
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