"""Functionality for storing the frames downloaded by the client."""

import logging
import Queue
import threading


logger = logging.getLogger(__name__)


class BaseFrameStore(threading.Thread):
    """Abstract base class defining basic setup."""

    def __init__(self, queue):
        super(BaseFrameStore, self).__init__()
        self._queue = queue
        self._stop = threading.Event()

    def run(self):
        """Run the thread."""
        while not self._stop.is_set():
            try:
                frame = self._queue.get(timeout=5)
            except Queue.Empty:
                pass
            else:
                self.store(frame)

    def stop(self):
        """Stop the thread."""
        self._stop.set()

    def store(self, frame):
        """Handle the frames."""
        raise NotImplementedError


class DummyFrameStore(BaseFrameStore):
    """Just logs the frame information."""

    def store(self, frame):
        """Log frame information."""
        logger.debug(frame.info())
