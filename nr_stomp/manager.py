"""Manage the appropriate client and store classes."""

from getpass import getpass
import Queue

from .client import NetworkRailClient
from .store import DummyFrameStore


FRAMES = Queue.Queue()


def create(args):
    """Create the producer and consumer from arguments."""
    producer = NetworkRailClient(
        frame_count=getattr(args, 'frames', None),
        frame_queue=FRAMES,
        password=args.password,
        queues=getattr(args, 'queues', []),
        username=args.username,
        verbose=getattr(args, 'verbose', False),
    )
    consumer = DummyFrameStore(FRAMES)
    return producer, consumer


def process(producer, consumer):
    """Run the threaded processes."""
    print 'Starting process...'
    producer.start()
    consumer.start()
    while producer.is_alive() or not FRAMES.empty():
        pass
    consumer.stop()
    print 'Process complete.'


def run_demo(username):
    """Default settings for testing."""
    process(
        producer=NetworkRailClient(
            username,
            frame_count=10,
            frame_queue=FRAMES,
            password=getpass('Enter password: '),
            queues='TRAIN_MVT_ALL_TOC',
        ),
        consumer=DummyFrameStore(FRAMES),
    )
