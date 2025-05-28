import sys
import logging
import inspect
from pathlib import Path

import loguru

__all__ = [
    "InterceptHandler",
    "ColoredStreamHandler",
    "LoguruManager",
]


class InterceptHandler(logging.Handler):
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

class LoguruManager:
    """loguru manager
    
    Settings:
        log_level: str = "DEBUG"
        log_dir: str = "logs"
        log_rotation: str = "00:00"
        log_retention: str = "3 days"
        log_compression: str = "zip"
        log_enqueue: bool = True
    
    """

    def __init__(self, name: str, level: str = "DEBUG"):
        loguru.logger.remove()

        self.name = name
        self.level = level

    def include_logging_namespace(self, namespace: str) -> None:
        
        logging_logger = logging.getLogger(namespace)
        self.include_logging_logger(logging_logger)

    def include_logging_logger(self, logging_logger: logging.Logger) -> None:
        
        logging_logger.setLevel(self.level)
        logging_logger.handlers.clear()
        logging_logger.addHandler(InterceptHandler())
        logging_logger.propagate = False

    def setup_console(self) -> None:

        loguru.logger.add(
            sys.stdout,
            level=self.level
        )

    def setup_file(
            self,
            log_dir: str = 'logs',
            *,
            rotation: str = '00:00',
            retention: str = '3 days',
            compression: str = 'zip',
            enqueue: bool = True,
    ):

        _log_dir = Path(log_dir)
        _log_dir.mkdir(parents=True, exist_ok=True)
        log_file = _log_dir / self.name / (f"{self.name}" + "_{time: YYYY-MM-DD}.log")
        loguru.logger.add(
            str(log_file),
            level=self.level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            enqueue=enqueue
        )
