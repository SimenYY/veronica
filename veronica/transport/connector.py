import logging
import asyncio
import random
from typing import Type, Self
from veronica.transport.protocol import TCPClientProtocol

logger = logging.getLogger(__name__)

__all__ = [
    "TCPConnector"
]

class TCPConnector:
     """TCP连接类

     Attributes:
          host (str): 服务器地址
          port (int): 服务器端口
          auto_reconnect (bool): 是否自动重连. Defaults to True.
          use_jitter (bool): 是否使用重连抖动. Defaults to False.
          protocol_class (Type[TcpClientProtocol], optional): 协议类. Defaults to TcpClientProtocol.
          _loop (asyncio.AbstractEventLoop): 事件循环
          _retry_delay (float): 重连延迟
          _continue_trying (bool): 是否继续尝试连接
          _on_lost_fut (asyncio.Future): 非正常连接丢失回调Future
          
     Example:
     >>> connector = TcpConnector.create("127.0.0.1", 8000, protocol_class=YourProtocol)
     
     """
     
     min_delay: float = 1.0
     max_delay: float = 60.0

     factor: float = 1.6180339887498948
     jitter: float = 0.119626565582 

     def __init__(
          self, 
          host: str,
          port: int,
          auto_reconnect: bool,
          use_jitter: bool,
          protocol_class: Type[TCPClientProtocol],
          loop: asyncio.AbstractEventLoop | None = None
     ):
          self.host = host
          self.port = port
          self.auto_reconnect = auto_reconnect
          self.protocol_class = protocol_class
          self.use_jitter = use_jitter
          
          self._loop = loop or asyncio.get_running_loop()
          self._retry_delay = self.min_delay
          self._continue_trying = True
          self._on_lost_fut = self._loop.create_future()
          
     @classmethod
     async def create(
          cls,
          host: str,
          port: int,
          *,
          auto_reconnect: bool = True,
          use_jitter: bool = False,
          protocol_class: Type[TCPClientProtocol] = TCPClientProtocol,
          loop: asyncio.AbstractEventLoop | None = None
     ) -> Self:
          """创建连接

          Args:
               host (str): 服务器地址
               port (int): 服务器端口
               auto_reconnect (bool): 是否自动重连. Defaults to True.
               use_jitter (bool): 是否使用重连抖动. Defaults to False.
               protocol_class (Type[TcpClientProtocol], optional): 协议类. Defaults to TcpClientProtocol.

          Returns:
               Self: 连接实例
          """
          connector = cls(
               host,
               port,
               auto_reconnect,
               use_jitter,
               protocol_class,
               loop
          )
          
          if connector.auto_reconnect:
               await connector._reconnect()
          else:
               await connector._connect()
     
          return connector
     
     
     def close(self) -> None:
          """关闭连接
          """
          if not self.is_connected():
               assert self._transport is not None, (
                    "transport is None"
               )
               self._transport.close()
               self._transport = None
     async def _connect(self) -> None:
          """连接
          """
          transport, protocol = await self._loop.create_connection(
               lambda: self.protocol_class(self._on_lost_fut, self._loop),
               self.host, self.port   
          )
          self._transport = transport
          self._protocol = protocol
     async def _reconnect(self) -> None:
          """重连
          
          Note:
               实现说明，连接成功后，因为等待`self._on_lost_fut`的结果，当前函数会被暂时搁置，
               当`self._on_lost_fut`结果返回时，当前函数会继续执行，并重新连接。
          """
          while self._continue_trying:
               try:
                    await self._connect()
                    self._reset_delay()
                    on_lost_fut = self._on_lost_fut
                    if await on_lost_fut:
                         self._on_lost_fut = self._loop.create_future()
                         continue
                    break 
               except OSError as e:
                    self._increase_delay()
                    logger.info(f"Failed to connect to {self.log_address()}: {e} Reconnecting...(after {self._retry_delay: 0.2f} s)")
                    await asyncio.sleep(self._retry_delay)

     def stop_retry(self) -> None:
          """停止重连
          """
          if self._continue_trying:
               self._continue_trying = False
          
     def _reset_delay(self) -> None:
          """重置重连时延
          """
          self._retry_delay = self.min_delay
     
     def _increase_delay(self) -> None:
          """增加重连时延
          
          Note:
               时延抖动是根据正态分布计算
          """
          self._retry_delay = min(self._retry_delay * self.factor, self.max_delay)
          if self.use_jitter:
               self._retry_delay = random.normalvariate(self._retry_delay, self.jitter * self._retry_delay)
     
     def is_connected(self) -> bool:
          return self._transport is not None and not self._transport.is_closing()
     
     def __repr__(self) -> str:
          return f"{self.__class__.__name__}(host={self.host}, port={self.port})"
     
     
     def log_address(self) -> str:
          return f"{self.host}:{self.port}"