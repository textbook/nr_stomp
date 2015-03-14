"""Handle command line and config file arguments."""

import argparse
from ast import literal_eval
from ConfigParser import ConfigParser
from getpass import getpass
from textwrap import dedent

from nr_stomp.manager import create, process

SETTINGS = {
    'beat': (literal_eval, None),
    'frames': (int, None),
    'topics': (literal_eval, []),
}

TEMPLATE = dedent(
    """
    [credentials]
    username:
    # leave password blank to enter on command line
    password:

    [settings]
    # note that you must _subscribe to the topics you enter
    topics: [
       'TRAIN_MVT_ALL_TOC',
    #   'RTPPM_ALL',
       ]
    # number of frames to monitor (leave blank for unlimited)
    frames: 10
    """
)


def cli(args):
    """Overall interface for command line."""
    args = parse_args(args)
    if hasattr(args, 'location'):
        create_config(args.location)
        return
    parse_config(args)
    if not args.password:
        args.password = getpass('Enter password: ')
    process(*create(args))


def create_config(location):
    """Create a blank configuration file."""
    with open(location, 'w') as file_:
        file_.write(TEMPLATE)


def parse_args(args):
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        description='STOMP client for Network Rail\'s public data.'
    )
    subparsers = parser.add_subparsers()
    # Creation of new configuration files
    create_parser = subparsers.add_parser(
        'create',
        description='Create a new, empty configuration file.'
    )
    create_parser.add_argument(
        'location',
        help='The location for the new configuration file.'
    )
    # Running the client
    run_parser = subparsers.add_parser(
        'run',
        description='Run the client'
    )
    run_parser.add_argument(
        'config',
        help='The configuration file to use for setup.'
    )
    return parser.parse_args(args)


def parse_config(args):
    """Parse the configuration file."""
    config = ConfigParser()
    config.read(args.config)
    args.username = config.get('credentials', 'username')
    args.password = config.get('credentials', 'password')
    args.config = {}
    for option in config.options('settings'):
        opt = config.get('settings', option)
        if option in SETTINGS:
            func, default = SETTINGS[option]
            try:
                setattr(args, option, func(opt))
            except ValueError:
                setattr(args, option, default)
        else:
            args.config[option] = opt
