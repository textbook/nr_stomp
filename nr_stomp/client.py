"""The client object for accessing Network Rail's data feeds."""

from datetime import datetime
from itertools import count
import Queue
from textwrap import dedent
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


class NetworkRailClient(threading.Thread):
    """Client for Network Rail's STOMP feeds.

    Arguments:
      username (str): The username to log in with.
      password (str): The password to log in with (optional).
      **config (dict): The configuration options.

    Attributes:
      BEAT (tuple): The default heartbeat settings.
      COUNT (int): The default number of frames to collect.
      TEMPLATE (str): The template for verbose logging.
      URI (str): The Network Rail feed location.

    """

    BEAT = (1000, 1000)
    COUNT = 10
    TEMPLATE = dedent(
        """
        Frame number: {number}
        Time: {time}
        Frame info: {info}
        """
    )
    URI = 'tcp://datafeeds.networkrail.co.uk:61618'

    def __init__(self, username, password, **config):
        super(NetworkRailClient, self).__init__()
        self.beat = config.get('beat', self.BEAT)
        self.client = Stomp(
            StompConfig(
                self.URI,
                username,
                password,
                version=StompSpec.VERSION_1_1,
            )
        )
        self.timeout = config.get(
            'timeout',
            0.8 * self.beat[0] / 1000.0,
        )
        self.topics = config.get('topics', [])
        if isinstance(self.topics, basestring):
            self.topics = [self.topics]
        if not self.topics:
            raise AttributeError('No valid subscriptions.')
        self.username = username
        self.verbose = config.get('verbose', False)
        if self.verbose:
            print 'Attempting to connect (username: {}, timeout: {}s).'.format(
                self.username,
                self.timeout,
            )
        self._count = config.get('frame_count', self.COUNT)
        self._queue = config.get('frame_queue', Queue.Queue())
        self._subscriptions = {}

    def run(self):
        """Monitor the feed."""
        self._connect()
        self._subscribe()
        if self.verbose:
            print 'Monitoring...'
        frame_count = count() if not self._count else xrange(self._count)
        for frame_number in frame_count:
            while True:
                self.client.beat()
                try:
                    ready = self.client.canRead(timeout=self.timeout)
                except StompConnectionError:
                    self._connect()
                    continue
                else:
                    if ready:
                        break
            frame = self.client.receiveFrame()
            if frame.command == 'ERROR':
                print frame.info()
                break
            self.client.ack(frame)
            self._queue.put_nowait(frame)
            if self.verbose:
                self._log_frame(frame_number+1, frame)
        try:
            self.client.disconnect()
        except StompConnectionError:
            pass

    def _connect(self):
        """Connect to the data feeds."""
        wait_time = 1
        if self.verbose:
            print 'Connecting...'
        while True:
            try:
                self.client.connect(
                    connectedTimeout=self.timeout,
                    connectTimeout=self.timeout,
                    headers={StompSpec.ACK_CLIENT: self.username},
                    heartBeats=self.beat,
                )
            except (StompConnectionError, StompConnectTimeout):
                pass
            except StompProtocolError:
                raise ValueError('Invalid credentials.')
            else:
                if self.verbose:
                    print 'Connection made.'
                break
            if self.verbose:
                print 'Connection unavailable, waiting {}s.'.format(wait_time)
            time.sleep(wait_time)
            wait_time *= 2

    def _log_frame(self, frame_number, frame):
        """Log the received frame."""
        print self.TEMPLATE.format(
            number=frame_number,
            time=str(datetime.now()),
            info=frame.info(),
        )

    def _subscribe(self):
        """Subscribe the client to the specified topics."""
        for topic in self.topics:
            try:
                token = self.client.subscribe(
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
                if self.verbose:
                    print 'Subscription skipped: {!r}.'.format(topic)
            else:
                self._subscriptions[topic] = token
                if self.verbose:
                    print 'Subscribed to: {!r}.'.format(topic)
