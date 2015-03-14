"""STOMP client for Network Rail's public data."""

__version__ = '0.0.1'

from datetime import datetime
import logging

from .client import NetworkRailClient
from .manager import process, run_demo
from .store import DummyFrameStore


now = datetime.now().strftime('%Y%m%d_%H%M%S')
handler = logging.FileHandler('stomp_{}.log'.format(now))
handler.setLevel(logging.INFO)
format_ = '%(asctime)s - %(levelname)s - %(name)s: %(message)s'
handler.setFormatter(logging.Formatter(format_))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
