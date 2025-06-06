import logging
from typing import (
    Type,
    TYPE_CHECKING
)
import loguru

if TYPE_CHECKING:
    pass

from veronica.core.log.logging_handlers import InterceptToLoguruHandler
from veronica.core.log.loguru_handlers import BaseHandler


__all__ = [
    "LoguruConfig"
]


class LoguruConfig:
    """loguru configuration
    """
    loguru.logger.remove()
    
    @staticmethod
    def add_handler(handler: Type[BaseHandler]) -> None:
        loguru.logger.add(**handler().to_dict())
            
    @staticmethod
    def intercept_logging(
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
        
    @staticmethod
    def get_logger():
        return loguru.logger