import pytest

from veronica.net.buffer import (
    HeaderFooterBuffer,
    HeaderFooterExtraBuffer,
    HeaderLengthBuffer,
    DelimiterBuffer
)


class TestDelimiterBuffer:
    
    def setup_method(self):
        self.buffer = DelimiterBuffer(delimiter=b"\r\n")
    
    def test_single_message(self):
        
        data = b"hello\r\nworld"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"hello"]
    
    def test_multiple_messages(self):

        data = b"hello\r\nworld\r\n"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"hello", b"world"]
    
    def test_no_messages(self):
        
        data = b"hello"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == []
    
    def test_delimiter_empty(self):
        
        with pytest.raises(ValueError):
            DelimiterBuffer(b"")
        
    def test_data_too_long(self):
        with pytest.raises(ValueError):
            data = b"1" * (self.buffer.size + 1)
            self.buffer.try_to_buffer(data)
    
    def test_buffer_overflow(self):
        with pytest.raises(ValueError):
            data = b"1" * 11
            self.buffer._buffer = bytearray(b"1" * (self.buffer.size - 10))
            self.buffer.try_to_buffer(data)


class TestHeaderFooterBuffer:
    
    def setup_method(self):
        self.buffer = HeaderFooterBuffer(b"<", b">")
    
    def test_single_mssage(self):
        
        data = b"<1>"
        targets = list(self.buffer.recv(data))

        assert targets == [b"<1>"]

    def test_multiple_messages(self):
        data = b"<1><2><3>"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"<1>", b"<2>", b"<3>"]
        
    def test_no_header(self):
        data = b"1>"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == []
    
    def test_no_footer(self):
        data = b"1>"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == []

    
class TestHeaderFooterExtraBuffer:
    
    def setup_method(self):
        self.buffer = HeaderFooterExtraBuffer(b"<", b">", 1)
    
    
    def test_single_message(self):
        data = b"<1>2"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"<1>2"]
    
    def test_multiple_messages(self):
        data = b"<1>2<3>4"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"<1>2", b"<3>4"]
    
    
    def test_no_header(self):
        data = b"1>2"

        targets = list(self.buffer.recv(data))

        assert targets == []
        
    def test_no_footer(self):
        
        data = b"<12"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == []
        
    def test_no_extra(self):
        
        data = b"<1>"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == []
        
class TestHeaderLengthBuffer:
    
    def setup_method(self):
        self.buffer = HeaderLengthBuffer(b"<", 2)
        
        
    def test_single_message(self):
        data = b"<1"
        targets = list(self.buffer.recv(data))
        assert targets == [b"<1"]
        
    def test_multiple_messages(self):
        data = b"<22<333<4444"
        
        targets = list(self.buffer.recv(data))
        
        assert targets == [b"<2", b"<3", b"<4"]
        
    def test_no_header(self):
        data = b"12"

        targets = list(self.buffer.recv(data))
        
        assert targets == []
