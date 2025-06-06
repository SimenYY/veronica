import sys
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Union,
    TextIO,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    pass 

from veronica.base.models import DataModel


__all__ = [
    "BaseHandler",
    "SimpleFileHandler",
    "ConsoleHandler",
]



@dataclass
class BaseHandler(DataModel):
    """Base handler
    """
    pass



@dataclass
class SimpleFileHandler(BaseHandler):
    """default file handler

    :param _type_ DataModel: _description_
    """
    sink: Union[str, Path]
    level: Union[int, str] = "DEBUG"
    rotation: str = "00:00"
    retention: str = "3 days"
    compression: str = "zip"
    enqueue: bool = True
    encoding: str = "utf-8"

@dataclass
class ConsoleHandler(BaseHandler):
    """
    # * Can't pickle "TextIO" instances

    :param _type_ DataModel: _description_
    """
    sink: TextIO = sys.stdout
    level: Union[int, str] = "DEBUG"
    
    
    def to_dict(self, *, exclude_none: bool = False) -> dict:
        if exclude_none:
            return {k: v for k, v in self.__dict__.items() if v is not None}
        
        return self.__dict__