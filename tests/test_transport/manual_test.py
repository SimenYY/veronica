"""手动测试
"""
import sys
sys.path.append(".")
import asyncio
import functools
from typing import Callable, Any
from veronica.transport.connector import TCPConnector
from veronica.transport.protocol import TCPClientProtocol
from veronica.core.log import intercept_logging

intercept_logging()

class EchoProtocol(TCPClientProtocol):
    def on_data_received(self, data: bytes) -> None:
        self.transmit_data(data)


def call_timed(
    interval: float,
    soon: bool = False
):

    def decorate(func: Callable[..., Any]):
        loop = asyncio.get_event_loop()
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            if soon:
                loop.call_soon(partial)
            else:
                loop.call_later(interval, partial)
                
            return loop.call_later(interval, func)
        return wrapper
    return decorate

class TimerProtocol(TCPClientProtocol):
    
    
    def on_connection_made(self) -> None:
    
        self.task_send_hello()
    
    def task_send_hello(self) -> None:
        self.transmit_data(b"Hello")
        
        self._loop.call_later(1, self.task_send_hello)

async def test_reconnect():
    ip_list = [
        "127.0.0.1",
    ]

    coro_list = [TCPConnector.create(ip, 8888, protocol_class=EchoProtocol) for ip in ip_list]
    
    await asyncio.gather(*coro_list)
async def test_multiple_connector():

    ip_list = [f"127.0.0.{i}" for i in range(1, 100)]
    
    coro_list = [TCPConnector.create(ip, 8888, protocol_class=EchoProtocol) for ip in ip_list]
    
    await asyncio.gather(*coro_list)
        
    # async with asyncio.TaskGroup() as tg:
    #     for ip in ip_list:
    #         tg.create_task(TCPConnector.create(ip, 8888, protocol_class=EchoProtocol))


async def test_timer():
    ip_list = [
        "127.0.0.1",
    ]

    coro_list = [TCPConnector.create(ip, 8888, protocol_class=TimerProtocol) for ip in ip_list]
    
    await asyncio.gather(*coro_list)

async def test_timer_multiple():
    ip_list = [f"127.0.0.{i}" for i in range(1, 100)]

    coro_list = [TCPConnector.create(ip, 8888, protocol_class=TimerProtocol) for ip in ip_list]
    
    await asyncio.gather(*coro_list)

async def main():
    # await test_multiple_connector()
    # await test_reconnect()
    await test_timer()
    # await test_timer_multiple()
    
if __name__ == "__main__":
    asyncio.run(main())
    