import time

import pytest
from unittest.mock import patch

# 导入被测模块
from veronica.utils.decorator import time_this

@time_this
def func(x: int, y: int) -> int:
    time.sleep(0.001)
    return x + y

@pytest.fixture
def mock_logger():
    with patch("veronica.utils.decorators.logger") as mock:
        yield mock


@pytest.mark.usefixtures("mock_logger")
class TestTimeThis:
    
    def test_timethis_returns_correct_result(self):
        """TC01: 测试装饰器是否保留原始函数的返回值，以及位置参数
        """
        result = func(1, 2)
        assert result == 3

    def test_timethis_with_keyword_arguments(self):
        """TC02: 测试带关键字参数的函数是否能正确传递参数"""
        result = func(x=10, y=20)
        assert result == 30