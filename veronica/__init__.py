import logging
from importlib.metadata import version

__version__ = version(__name__)

logger = logging.getLogger(__name__)

