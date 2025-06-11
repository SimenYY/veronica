import logging
from dataclasses import dataclass, field
from typing import (
    Type,
    Dict, 
    Any,
    List,
    Optional,
    Self,
    TYPE_CHECKING
)
from pathlib import Path
import loguru


if TYPE_CHECKING:
    pass

from veronica.core.log.logging_handlers import InterceptToLoguruHandler
from veronica.core.log.loguru_handlers import BaseHandler

__all__ = [
    "LoguruConfig"
]

@dataclass
class LoguruConfig():
    """loguru configuration
    """
    handlers: List[BaseHandler] = field(default_factory=list)
    
    @classmethod
    def load(
        cls, 
        source: Dict[str, Any], 
        is_configured: bool = True
    ) -> Optional[Self]:
        """load  a config from a dict
        
        Usage:
            config = {
                "handlers": [
                    BaseHandler1(),
                    BaseHandler2().
                ]
            }        

        :param dict source: _description_
        :param bool is_configured: _description_, defaults to True
        :return Optional[Self]: _description_
        """
        config = cls(**source)
        if is_configured:
            config.configure()
            return None
        
        return config
    def configure(self) -> List[int]:
        config: Dict[str, Any] = {
            "handlers": [handler.to_dict() for handler in self.handlers ]
        }
        return loguru.logger.configure(**config)
    
    @classmethod
    def clear(cls) -> None:
        loguru.logger.remove()

    def add_handler(self, handler: BaseHandler) -> int:        
        self.handlers.append(handler)
        
        return loguru.logger.add(**handler.to_dict())

    @classmethod
    def intercept_logging(
        cls,
        namespace: str, 
        level: str = "DEBUG"
    ) -> None:
        """Redirect logging to loguru

        :param str namespace: _description_
        :param str level: _description_, defaults to "DEBUG"
        """
        logging_logger = logging.getLogger(namespace)
        logging_logger.propagate = False
        logging_logger.setLevel(level)
        logging_logger.handlers.clear()
        logging_logger.addHandler(InterceptToLoguruHandler())
    
    
    
    