# /usr/bin/env python
"""Command line interface for running the Network Rail STOMP client."""

import sys

from nr_stomp.config import cli

if __name__ == '__main__':
    cli(sys.argv[1:])
