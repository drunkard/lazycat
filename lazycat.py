#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This program is a pseudo-shell and gives the user interactive control.
The entire ssh/telnet session is logged to a file, others won't be logged.
"""
import logging
import readline
import sys

try:
    import cli
    from lib import history
except ImportError as e:
    raise ImportError(e + """\033[05;37;41m

A critical module was not found. Probably this operating system does not
support it. Pexpect is intended for UNIX-like operating systems.\033[0m""")


__author__ = "Drunkard Zhang"
__email__ = "gongfan193@gmail.com"
__version__ = "0.1"
__productname__ = "lazycat"
__description__ = "A pseudo shell with restricted capability for AAA purpose."

# DEBUG, FATAL
DEBUG_LEVEL = logging.FATAL


def ttywrapper():
    from cli import PROMPT
    try:
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims(' ')
    except Exception as e:
        print(e)
    # Start input loop
    while True:
        readline.set_completer(cli.MLCompleter().complete)
        # Get input, and deal with exceptions
        try:
            rawcmd = input(PROMPT)
        except KeyboardInterrupt:
            """Ctrl-C"""
            print ("^C")
            continue
        except EOFError:
            """Ctrl-D"""
            print('quit')
            cli.do_quit('quit')
        # Determine if the raw command is empty
        rawcmd = rawcmd.strip()
        if rawcmd:
            cli.route(rawcmd)
        else:
            continue


if __name__ == "__main__":
    history.load()
    history.save()
    logging.basicConfig(format='DEBUG: %(message)s', level=DEBUG_LEVEL)
    try:
        ttywrapper()
    except (Exception, SystemExit) as e:
        # After ttywrapper() exit, we get SystemExit exception here
        sys.exit(e)
