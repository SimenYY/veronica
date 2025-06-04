from typing import (
    Optional, 
    Dict, 
    Any, 
    ClassVar, 
    List, 
    Self, 
    Sequence,
    Type,
)
from functools import reduce
from abc import ABC
from dataclasses import dataclass, field
from enum import StrEnum

__all__ = [
    "JsonLoader",
    "YamlLoader",
    "TomlLoader",
    "LoaderManager",
]



@dataclass
class _LoaderContext:
    content: Any = None
    loader_errors: Dict[str, Exception] = field(default_factory=dict)

    def format_errors(self) -> str:
        """
        Notes:
            import traceback
            "".join(traceback.format_exception(type(e), e, e.__traceback__))
        
        :return str: _description_
        """
        formatted_exceptions = '\n'.join(
            f'  - {loader_name}: {str(e)}'
            for loader_name, e in self.loader_errors.items())
        return (f'Could not load config file "{self.content}" '
                f'with any of the following loaders:\n{formatted_exceptions}')

@dataclass
class BaseLoader(ABC):
    _successor: Optional["BaseLoader"] = None
    @property
    def successor(self) -> Optional["BaseLoader"]:
        return self._successor
    
    @property
    def class_name(self) -> str:
        return self.__class__.__name__
    
    @successor.setter
    def successor(self, loader: "BaseLoader") -> None:
        if not isinstance(loader, BaseLoader):
            raise TypeError(f"The loader must be an instance of Loader: {type(loader)}")
        self._successor = loader
    
    def load(self, content: Any) -> Any:
        """

        :param Any content: _description_
        :raises NotImplementedError: _description_
        :return Any: _description_
        """
        raise NotImplementedError
    
    def load_chain(self, content: Any) -> Any:
        """

        :param Any content: _description_
        :raises NotImplementedError: _description_
        :return Any: _description_
        """
        raise NotImplementedError
    

    
@dataclass
class Loader(BaseLoader):
    
    _context: ClassVar[_LoaderContext] = _LoaderContext()
    def load_chain(self, content: str) -> Any:
        """

        :param str content: _description_
        :return Any: _description_
        """
        try:
            return self.load(content)
        except Exception as e:
            if self._context.content is None:
                self._context.content = content
            self._context.loader_errors[self.class_name] = e
            return self._load_next()
    
    def _load_next(self) -> Any:
        """
        
        :raises RuntimeError: _description_
        :return Any: _description_
        """
        if self.successor is not None:
            return self.successor.load_chain(self._context.content)
        else:
            raise SyntaxError(self._context.format_errors())
    
    def __str__(self) -> str:
        
        parts = []
        current = self
        
        while current is not None:
            parts.append(current.class_name)
            current = current.successor
            
        return " --> ".join(parts)
    
    def __or__(self, other: "Loader") -> "Loader":
        """
        Usage:
            chain =  loader1 | loader2 | loader3

        :param Loader other: _description_
        :raises TypeError: _description_
        :return Loader: _description_
        """
        if not isinstance(other, Loader):
            raise TypeError(f"Can only chain Loaders: {type(other)}")
        
        current = self
        
        while current.successor is not None:
            current = current.successor
    
        current.successor = other
        
        return self
    
    
@dataclass    
class JsonLoader(Loader):
    def load(self, content: str) -> dict:
        import json
        return json.loads(content)
    
    
@dataclass
class YamlLoader(Loader):
    def load(self, content: str) -> dict:
        import yaml
        return yaml.safe_load(content)


@dataclass
class TomlLoader(Loader):
    
    def load(self, content: str) -> dict:
        import toml
        return toml.loads(content)


class _SupportedFormatEnum(StrEnum):
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class LoaderManager:
    """
    >>> loader_manager = LoaderManager()
    >>> _ = loader_manager.add_loader_by_format("json")
    >>> _ = loader_manager.add_loader_by_format("yaml").add_loader_by_format("toml")
    >>> print(loader_manager.get_chain())
    JsonLoader --> YamlLoader --> TomlLoader

    :raises TypeError: _description_
    :raises ValueError: _description_
    :raises ValueError: _description_
    :raises ValueError: _description_
    :return _type_: _description_
    """
    _loaders: List[Loader] = field(default_factory=list)
    
    @property
    def loaders(self) -> Sequence[Loader]:
        return tuple(self._loaders)
    
    
    def add_loader(self, loader: Loader) -> Self:
        if not isinstance(loader, Loader):
            raise TypeError("The loader must be an instance of Loader")
        
        self._loaders.append(loader)

        return self
    
    def add_loader_by_format(self, fmt: str) -> Self:
        """ fmt e.g. "json", "yaml" 

        :param _SupportedFormatEnum string_format: _description_
        :raises ValueError: _description_
        :return Self: _description_
        """

        if not isinstance(fmt, str):
            raise ValueError(f"Invalid format type: {type(fmt)}")
            
        fmt = fmt.lower()
        match fmt:
            case _SupportedFormatEnum.JSON:
                self.add_loader(JsonLoader())
            case _SupportedFormatEnum.YAML:
                self.add_loader(YamlLoader()) 
            case _SupportedFormatEnum.TOML:
                self.add_loader(TomlLoader())
            case _:
                raise ValueError(f"This format is not supported: {fmt}")
        
        return self
    
    def clear(self) -> None:
        
        self._loaders.clear()
        
    
    def get_chain(self) -> Loader:
        if not self.loaders:
            raise ValueError("No loaders have been added to the chain.")
        
        return reduce(lambda loader, next_loader: loader | next_loader, self._loaders)
    
    @classmethod
    def get_default_chain(cls) -> Loader:
        lm = cls()
        for fmt in _SupportedFormatEnum:
            lm.add_loader_by_format(fmt)
        
        return lm.get_chain()
        

if __name__ == "__main__":
    import doctest
    doctest.testmod()
