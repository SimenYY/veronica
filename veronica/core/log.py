import logging
import inspect
from dataclasses import dataclass
try:
    from loguru import logger
except ImportError:
    raise ImportError("loguru is not installed., Please install it using pip insall loguru")

__all__ = [
    "PrefixLoggerAdapter",
    "PropagateFromLoguruHandler",
    "ColoredStreamHandler",
    "InterceptHandler",
    "intercept_logging",
]


####################################################################################################
#                                        logger adapter                                            #
####################################################################################################


class PrefixLoggerAdapter(logging.LoggerAdapter):
    """Add external prefix to log messages.

    Args:
        logging (logging.Logger): _description_
        
    Examples:
    >>> logger = logger.getLogger(__name__)
    ... logger = PrefixLoggerAdapter(logger, prefix="your prefix")
    """
    def __init__(self, logger, *, prefix: str | None = None):
        if prefix:
            extra = {"prefix": prefix}
        else:
            extra = None
        super().__init__(logger, extra)
    def process(self, msg, kwargs):
        if self.extra and "prefix" in self.extra:
            return f"{self.extra['prefix']} - {msg}", kwargs
        
        return super().process(msg, kwargs)

####################################################################################################
#                                        logging handler                                           #
####################################################################################################
    
    
class PropagateFromLoguruHandler(logging.Handler):
    """Propagate loguru messages to logging

    Usage:
        logger.add(PropagateHandler(), format="{message}")
    """
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.

    This handler intercepts all log requests and
    passes them to loguru.

    For more info see:
    https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
        
        
        
class ColoredStreamHandler(logging.StreamHandler):
    """Colored stream handler
    
    """
    def __init__(self):
        super().__init__()
        try:
            from colorlog import ColoredFormatter
        except ImportError:
            raise ImportError("colorlog is not installed")

        self.setFormatter(ColoredFormatter(
            "%(green)s%(asctime)s.%(msecs)03d"
            "%(red)s | "
            "%(log_color)s%(levelname)-8s"
            "%(red)s | "
            "%(cyan)s%(name)s"
            "%(red)s:"
            "%(cyan)s%(module)s"
            "%(red)s:"
            "%(cyan)s%(funcName)s"
            "%(red)s:"
            "%(cyan)s%(lineno)d"
            "%(red)s - "
            "%(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG': 'blue',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'white,bg_red',
            },
            style='%'
        ))


####################################################################################################
#                                        logging utils                                             #
####################################################################################################


def intercept_logging() -> None:
    """intercept all logging to loguru"""
    intercept_handler = InterceptHandler()
    # Configuares global logging
    logging.basicConfig(handlers=[intercept_handler], level=0, force=True)
    
    
####################################################################################################
#                                        logging config                                             #
####################################################################################################


@dataclass(frozen=True)
class loguru_defaults:
    FORMAT: str = (
        "<level>{level: <8}</level> | "
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
