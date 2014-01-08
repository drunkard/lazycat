#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program is a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""
import logging
import sys

try:
    from cli import PROMPT
    from lib import color, history
except ImportError as e:
    raise ImportError(e + """\033[05;37;41m

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.\033[0m""")


__author__ = "Drunkard Zhang"
__email__ = "gongfan193@gmail.com"
__version__ = "0.2"
__productname__ = "lazycat"
__description__ = "A pseudo shell with restricted capability for AAA purpose."

# DEBUG, FATAL
DEBUG_LEVEL = logging.FATAL
DEBUG_FORMAT = color.GREY_DARK + 'DEBUG: %(message)s' + color.OFF


if __name__ == "__main__":
    history.load()
    history.save()
    logging.basicConfig(format=DEBUG_FORMAT, level=DEBUG_LEVEL)
    try:
        from lib import TUI
        TUI(PROMPT)
    except (Exception, SystemExit) as e:
        # After TUI() exit, we get SystemExit exception here
        sys.exit(e)
