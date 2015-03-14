"""The client object for accessing Network Rail's data feeds."""

from itertools import count
import logging
import Queue
import threading
import time

from stompest.config import StompConfig
from stompest.error import (
    StompConnectionError,
    StompConnectTimeout,
    StompProtocolError,
)
from stompest.protocol import StompSpec
from stompest.sync import Stomp


logger = logging.getLogger(__name__)


class NetworkRailClient(threading.Thread):
    """Client for Network Rail's STOMP feeds.

    Notes:
      Supported ``**config`` options:

       - 'beat' (tuple): heartbeat time ``(client, server)``.
       - 'frame_count' (int): number of frames to get.
       - 'frame_queue' (Queue): queue to send frames to.
       - 'topics' (seq): topics to subscribe to.

    Arguments:
      username (str): The username to log in with.
      password (str): The password to log in with.
      **config (dict): The configuration options.

    Attributes:
      topics (list): The subscribed topics.
      BEAT (tuple): The default heartbeat settings.
      COUNT (int): The default number of frames to collect.
      URI (str): The Network Rail feed location.

    """

    BEAT = (10000, 10000)
    COUNT = 10
    URI = 'tcp://datafeeds.networkrail.co.uk:61618'

    def __init__(self, username, password, **config):
        super(NetworkRailClient, self).__init__()
        self._beat = config.get('beat', self.BEAT)
        self._client = Stomp(
            StompConfig(
                self.URI,
                username,
                password,
                version=StompSpec.VERSION_1_1,
            )
        )
        self._timeout = 0.8 * self._beat[0] / 1000.0  # 80% of own heartbeat
        self.topics = config.get('topics', [])
        if isinstance(self.topics, basestring):
            self.topics = [self.topics]
        if not self.topics:
            raise AttributeError('No valid subscriptions.')
        self.username = username
        logger.info(
            'Attempting to connect (username: %s, timeout: %ds).',
            self.username,
            self._timeout,
        )
        self._count = config.get('frame_count', self.COUNT)
        self._queue = config.get('frame_queue', Queue.Queue())
        self._subscriptions = {}
        self._connected = threading.Event()

    def is_connected(self):
        """Whether the client is currently connected."""
        return self._connected.is_set() and not self.__stopped

    def run(self):
        """Monitor the feed."""
        self._connect()
        self._subscribe()
        logger.debug('Monitoring...')
        frame_count = count() if not self._count else xrange(self._count)
        for frame_number in frame_count:
            while True:
                self._client.beat()
                try:
                    ready = self._client.canRead(timeout=self._timeout)
                except StompConnectionError:
                    logger.warning('Client disconnected.')
                    self._connect()
                    continue
                else:
                    if ready:
                        break
            if frame_number and not frame_number % 500:
                logger.info('Processed %s frames.', frame_number)
            frame = self._client.receiveFrame()
            if frame.command == 'ERROR':
                logger.error(frame.info())
                break
            self._client.ack(frame)
            self._queue.put_nowait(frame)
            logger.debug('%d: %s', frame_number+1, frame.info())
        try:
            self._client.disconnect()
        except StompConnectionError:
            pass
        logger.debug('Monitoring ended.')

    def _connect(self):
        """Connect to the data feeds.

        Notes:
          If the connection is unavailable, the attempts to reconnect
          will back off exponentially to avoid overwhelming the server.

        """
        self._connected.clear()
        wait_time = 1
        logger.debug('Connecting...')
        while True:
            try:
                self._client.connect(
                    connectedTimeout=self._timeout,
                    connectTimeout=self._timeout,
                    headers={StompSpec.ACK_CLIENT: self.username},
                    heartBeats=self._beat,
                )
            except (StompConnectionError, StompConnectTimeout):
                pass
            except StompProtocolError:
                msg = 'Invalid credentials.'
                logger.error(msg)
                raise ValueError(msg)
            except Exception:  # pylint: disable=broad-except
                logger.exception('Connection failed.')
                break
            else:
                logger.info('Connection made.')
                self._connected.set()
                break
            logger.warning('No connection, waiting %ds.', wait_time)
            time.sleep(wait_time)
            wait_time *= 2

    def _subscribe(self):
        """Subscribe the client to the specified topics."""
        for topic in self.topics:
            try:
                token = self._client.subscribe(
                    '/topic/{}'.format(topic),
                    headers={
                        StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                        StompSpec.ID_HEADER: '{}-{}'.format(
                            self.username.partition('@')[0],
                            topic,
                        ),
                    },
                )
            except StompProtocolError:
                logger.warning('Subscription skipped: %s.', repr(topic))
            else:
                self._subscriptions[topic] = token
                logger.info('Subscribed to: %s.', repr(topic))
        self.topics = self._subscriptions.keys()
