from abc import ABC, abstractmethod
from typing import Any, Iterator, Generator

__all__ = [
    "DelimiterBuffer",
    "HeaderFooterBuffer",
    "HeaderFooterExtraBuffer",
    "HeaderLengthBuffer",
]

class BaseBuffer(ABC):
    """缓冲区基类

    用于字节流缓冲区管理
    
    Attributes:
        max_length (int): _description_. Defaults to 16384.
    
    Raises:
        NotImplementedError: _description_
    """
    
    max_length: int = 16384

    def __init__(self) -> None:
        
        self._buffer: bytearray = bytearray()
    
    @abstractmethod
    def recv(self, data: bytes) -> Generator[bytes, None, None]:
        """接受数据

        Args:
            data (bytes): 字节流

        Yields:
            Generator[bytes, None, None]: _description_
        """
        raise NotImplementedError
    
    def try_to_buffer(self, data: bytes) -> None:
        """尝试缓存数据

        Args:
            data (bytes): 字节流

        Raises:
            ValueError: data长度超出缓冲区限制
            ValueError: data无法放入缓冲区
        """
        data_len = len(data)
        if data_len > self.max_length:
            raise ValueError(f"Data is too long, length is {data_len}, max length is {self.max_length}")
        
        buffer_len = len(self._buffer)
        total_length = data_len + buffer_len
        if total_length > self.max_length:
            raise ValueError(f"Buffer is exceeded, total length is {total_length}")
        
        if buffer_len > self.max_length:
            self._buffer.clear()
            
        self._buffer.extend(data)
    
class DelimiterBuffer(BaseBuffer):
    """按分隔符的缓冲区

    Attributes:
        delimiter (bytes): 分隔符
    """
    def __init__(self, delimiter: bytes = b'\r\n'):
        super().__init__()
        
        if not delimiter:
            raise ValueError("Delimiter cannot be empty")
        
        self.delimiter = delimiter
    
    def recv(self, data: bytes) -> Generator[bytes, None, None]:
        
        self.try_to_buffer(data)
        
        while self._buffer:
            try:
                target, self._buffer = self._buffer.split(self.delimiter, maxsplit=1)
                yield bytes(target)
            except ValueError:
                break

class HeaderFooterBuffer(BaseBuffer):
    """按头和尾的缓冲区

    Attributes:
        header (bytes): 头
        footer (bytes): 尾
    """
    def __init__(self, header: bytes, footer: bytes) -> None:
        super().__init__()

        if not header:
            raise ValueError("header cannot be empty")
        if not footer:
            raise ValueError("footer cannot be empty")
        
        self.header = header
        self.footer = footer
        
    def recv(self, data: bytes) -> Generator[bytes, None, None]:
    

        self.try_to_buffer(data)
        
        while True:
            start = self._buffer.find(self.header)
            if start == -1:
                # 未找到
                break
            end = self._buffer.find(self.footer, start + len(self.header))
            if end == -1:
                break
            target = self._buffer[start:end + len(self.footer)]
            yield bytes(target)
            self._buffer = self._buffer[end + len(self.footer):]
            
            

        

class HeaderFooterExtraBuffer(BaseBuffer):
    """按头和尾，以及带有额外长度的缓冲区

    Attributes:
        header (bytes): 头
        footer (bytes): 尾
        extra_length (int): 额外的长度
    """
    
    def __init__(self, header: bytes, footer: bytes, extra_len: int) -> None:
        super().__init__()
        
        if extra_len < 0:
            raise ValueError("extra_len must be greater than 0")
        if not header:
            raise ValueError("header cannot be empty")
        if not footer:
            raise ValueError("footer cannot be empty")
        
        self.header = header
        self.footer = footer
        self.extra_len = extra_len
        
    
    def recv(self, data: bytes) -> Generator[bytes, None, None]:
        
        self.try_to_buffer(data)
        
        while True:
            start = self._buffer.find(self.header)
            if start == -1:
                break
            end = self._buffer.find(self.footer, start + len(self.header))
            if end == -1:
                break
            extra = self._buffer[end + len(self.footer):]
            if len(extra) < self.extra_len:
                break
            target = self._buffer[start: end + len(self.footer) + self.extra_len]
            yield bytes(target)
            self._buffer = self._buffer[end + len(self.footer) + self.extra_len:]


class HeaderLengthBuffer(BaseBuffer):
    """按头和整体长度的缓冲区

    Attributes:
        header (bytes): 头
        length (int): 整体长度
    """    
    def __init__(self, header: bytes, length: int) -> None:
        super().__init__()
        
        if length <= 0:
            raise ValueError("extra_len must be greater than 0")
        if not header:
            raise ValueError("header cannot be empty")
        
        self.header = header
        self.length = length
        
    def recv(self, data: bytes) -> Generator[bytes, None, None]:
        
        self.try_to_buffer(data)
        
        while True:
            start = self._buffer.find(self.header)
            if start == -1:
                break
            if len(self._buffer[start:]) < self.length:
                break
            target = self._buffer[start:start + self.length]
            yield bytes(target)
            self._buffer = self._buffer[start + self.length:]
            

