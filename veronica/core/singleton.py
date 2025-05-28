import sys
from pathlib import Path
from typing import Union, Optional
import logging
from dataclasses import dataclass

from filelock import FileLock, AsyncFileLock, BaseAsyncFileLock, BaseFileLock


logger = logging.getLogger(__name__)

__all__ = ["SingleAppGuard"]

@dataclass
class SingleAppGuard:
    """App guard

    Usage:
        with SingleAppGuard():
            print("your func")

    """
    app_name: str = "app.lock"
    def __post_init__(self) -> None:
        self.lock_file: Path = Path.cwd() / f"{self.app_name}.lock"
        self.lock: Optional[Union[BaseAsyncFileLock, BaseFileLock]] = None
        logger.info(f"lock file path: {str(self.lock_file)}")
    def __enter__(self):
        try:
            self.lock = FileLock(self.lock_file)
            self.lock.acquire(timeout=0)
            logger.info("The program is started successfully")
        except TimeoutError:
            logger.warning("The program is already running")
            sys.exit(0)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.lock, BaseFileLock):
            self.lock.release()
            self.lock = None
        else:
            raise  TypeError("elf.lock is not an instance of FileLock")
        logger.info("The program is exited successfully")

        if exc_type is not None:
            logger.error(f"Exception in context: {exc_val}")
            
    async def __aenter__(self):
        try:
            self.lock = AsyncFileLock(self.lock_file)
            await self.lock.acquire(timeout=0)
            logger.info("The program is started successfully")
        except TimeoutError:
            logger.warning("The program is already running")
            sys.exit(0)
    
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.lock, BaseAsyncFileLock):
            await self.lock.release()
            self.lock = None
        else:
            raise TypeError("self.lock is not an instance of AsyncFileLock")
        logger.info("The program is exited successfully")

        if exc_type is not None:
            logger.error(f"Exception in context: {exc_val}")