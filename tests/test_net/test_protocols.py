import pytest

import asyncio
from unittest.mock import MagicMock, patch, call

from veronica.net.protocols import (
    ClientProtocol,
    RetryClientProtocol,
    Connector,
    RetryConnector,
    
)

class MockRetryProtocol(RetryClientProtocol):
    pass

@pytest.mark.asyncio
async def test_retry_on_connection_failed(mock_tcp_server):
    #? type_error
    # host, port = mock_tcp_server
    
    connector = RetryConnector("127.0.0.5", 6666, MockRetryProtocol)
    
    await connector.connect()
    assert connector.is_connected() is False

    
