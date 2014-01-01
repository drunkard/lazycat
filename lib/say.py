# -*- coding: utf-8 -*-
"""This module contains common messages used in this program."""
import sys
try:
    from lib import color
except ImportError as e:
    sys.exit(str(e) + "ERROR: some modules import failed")


def not_implemented():
    print("%sThis is planned, but not implemented yet.%s\n" %
          (color.CYAN_BOLD, color.OFF))


def available_cmds(cmdlist, msg=""):
    if msg == "":
        msg = "All available sub-commands:"
    print(msg)
    if len(cmdlist) > 0:
        for c in sorted(cmdlist):
            print("  " + str(c))
