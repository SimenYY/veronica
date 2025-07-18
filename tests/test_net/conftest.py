import asyncio
import pytest

@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def mock_tcp_server():

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.read(2**10)
            if data:
                writer.write(data)  # 回声响应
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()
    print(f"Server started at {host}:{port}")

    async with server:
        task = asyncio.create_task(server.serve_forever())
        yield host, port
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)