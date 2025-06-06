import inspect
import logging
import loguru

__all__ = [
    "PropagateFromLoguruHandler",
    "InterceptToLoguruHandler",
    "ColoredStreamHandler",
]


class PropagateFromLoguruHandler(logging.Handler):
    """Propagate loguru messages to logging

    Usage:
        logger.add(PropagateHandler(), format="{message}")
    """
    def emit(self, record: logging.LogRecord) -> None:
        logging.getLogger(record.name).handle(record)


class InterceptToLoguruHandler(logging.Handler):
    """Intercept all logging calls and redirect them to Loguru
    
    Usage:
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

class ColoredStreamHandler(logging.StreamHandler):
    """Colored stream handler
    
    """
    def __init__(self):
        super().__init__()

        from colorlog import ColoredFormatter

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